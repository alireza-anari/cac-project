"""W_ORACLE_ASSUMED. Real SQL/RLS, independent restore and size-one PgBouncer."""
import concurrent.futures
import time
import unittest
from uuid import uuid4
import psycopg
from psycopg.types.json import Jsonb

from recovery_fencing.lab import S1,P1
from recovery_fencing.broker import FenceDenied
from recovery_proof.pool_lab import Pool
from recovery_proof.authority_lab import dump_anchor,restore_anchor
from w_oracle.lab import BANNER
from w_oracle.integration_lab import IntegrationLab
from w_oracle.broker import Broker


class IntegrationFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lab=IntegrationLab()
    @classmethod
    def tearDownClass(cls):cls.lab.close()
    def setUp(self):
        self.lab.reset();self.a=Broker(self.lab);self.b=Broker(self.lab,'B')
        self.a.activate(0,str(uuid4()))
    def positive(self,broker):
        with broker.runtime() as g:
            token=self.scope(broker,g)
        return token
    def scope(self,broker,g):
        h=g.challenge();token=broker.issue(h);g.install(token)
        self.assertEqual(g.records(),[S1]);return token
    def no_open(self):
        with self.lab.oracle.connect() as w:
            self.assertEqual(w.execute("SELECT count(*) FROM w.ops WHERE phase IN ('open','unknown')").fetchone(),(0,))
    def assert_denied_sql(self,node,role,query,args=()):
        with self.lab.connect(node,role) as c:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute(query,args)
    def takeover(self):
        self.lab.restore();self.assertEqual(self.b.activate(1,str(uuid4()))['epoch'],2)
        self.assertFalse(self.a.ready());self.assertTrue(self.b.ready());self.positive(self.b)
    def after_c_rollback(self):pass # Disposable sensitivity hook; no assertions changed.


class IntegrationTests(IntegrationFixture):
    def test_direct_issuer_and_rls_use_online_w(self):
        self.assertTrue(self.a.ready());self.positive(self.a);self.no_open()
        with self.lab.oracle.connect() as w:
            self.assertEqual(w.execute("SELECT kind,phase,count(*) FROM w.ops GROUP BY 1,2 ORDER BY 1").fetchall(),
                             [('issuer','closed_commit',1),('runtime','closed_commit',1)])

    def test_missing_ticket_and_private_c_fallback_are_denied(self):
        self.assert_denied_sql('A','cac_ctx_runtime','SELECT poc.challenge()')
        self.assert_denied_sql('A','cac_ctx_runtime','SELECT store FROM poc.records')
        self.assert_denied_sql('A','cac_ctx_issuer','SELECT poc.issue(%s,%s,%s,%s,%s,%s)',
                               ('invalid','invalid',S1,'read',P1,Jsonb({})))
        for role,query in [('cac_ctx_runtime','SELECT w_guard.c_is_ready()'),
                           ('cac_ctx_runtime','SELECT w_guard.verify_c()'),
                           ('cac_ctx_issuer','SELECT w_guard.issue_c(NULL,NULL,NULL,NULL,NULL,NULL)'),
                           ('cac_ctx_runtime','SELECT fence_private.check_guard_c()')]:
            self.assert_denied_sql('A',role,query)

    def test_current_w_blocks_old_owner_after_real_c_rollback(self):
        self.positive(self.a);old=dump_anchor(self.lab.parent)
        self.takeover();latest=dump_anchor(self.lab.parent)
        self.addCleanup(restore_anchor,self.lab.parent,latest)
        restore_anchor(self.lab.parent,old)
        self.after_c_rollback()
        with self.lab.connect('C') as c:self.assertEqual(c.execute('SELECT epoch FROM anchor.state').fetchone(),(1,))
        with self.lab.oracle.connect() as w:self.assertEqual(w.execute('SELECT epoch,owner FROM w.state').fetchone(),(2,'B'))
        revived=self.a.ready()
        if revived:
            # Fault witness only: if mandatory W enforcement has been removed,
            # prove the same direct SQL path can actually issue/use old authority.
            from recovery_fencing.broker import Broker as LegacyBroker
            self.positive(LegacyBroker(self.lab.parent,'A'))
            print(BANNER,'INJECTED UNSAFE W bypass: C1 oldA issued new context and scoped RLS under current W2',flush=True)
        self.assertFalse(revived,'Rolled-back anchor revived previous-owner authority')
        self.assert_denied_sql('A','cac_ctx_runtime','SELECT poc.challenge()')
        self.assert_denied_sql('A','cac_ctx_runtime','SELECT store FROM poc.records')
        self.assert_denied_sql('A','cac_ctx_issuer','SELECT poc.issue(NULL,NULL,NULL,NULL,NULL,NULL)')
        with self.assertRaises(FenceDenied):self.a.issue('old-challenge')
        print(BANNER,'C ROLLBACK actual dump/restore epoch2->1; W2 ownerB unchanged; oldA ready/issuer/SQL/RLS DENIED',flush=True)

    def test_downgraded_verifier_stays_quarantined(self):
        expected=self.lab.oracle.cfg['approved_manifest']
        self.lab.quarantine('A');self.lab.teardown_overlay('A')
        with self.assertRaisesRegex(AssertionError,'manifest mismatch'):self.lab.admit('A',expected)
        with self.lab.connect() as c:
            self.assertEqual(c.execute("SELECT rolcanlogin FROM pg_roles WHERE rolname IN ('cac_ctx_issuer','cac_ctx_runtime') ORDER BY rolname").fetchall(),[(False,),(False,)])
        with self.lab.oracle.connect() as w:
            self.assertEqual(w.execute("SELECT admitted FROM w.actors WHERE node='A'").fetchone(),(False,))
        with self.assertRaises(psycopg.OperationalError):self.lab.connect('A','cac_ctx_runtime')
        print(BANNER,'pre-W verifier downgrade denied by EXTERNAL quarantine/admission; not self-protection of old SQL',flush=True)

    def test_overlay_rollback_reapply_preserves_manifest_acl_rls(self):
        before=self.lab.measure('A');old_inc=self.lab.oracle.cfg['actors']['A']['incarnation']
        self.lab.quarantine('A');self.lab.teardown_overlay('A');self.lab.install('A')
        self.assertEqual(self.lab.measure('A'),before)
        self.lab.admit('A',before)
        self.assertNotEqual(self.lab.oracle.cfg['actors']['A']['incarnation'],old_inc)
        self.assertFalse(self.a.ready())
        self.a.activate(1,str(uuid4()));self.positive(self.a)
        print(BANNER,'OVERLAY ROUNDTRIP definition/owners/ACL/RLS/catalog manifest exact',before,flush=True)

    def test_open_survives_last_guard_until_known_commit_and_close(self):
        self.lab.restore() # Rival must be admitted, otherwise denial is vacuous.
        stages=[]
        def hook(stage):
            if stage in ('after_durable_open','after_final_guard','after_local_commit_before_close'):
                with self.lab.oracle.connect() as w:
                    self.assertEqual(w.execute("SELECT count(*) FROM w.ops WHERE phase='open'").fetchone(),(1,))
                with self.lab.oracle.connect('B') as rival:
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                        rival.execute('SELECT w.reserve(1,%s)',(str(uuid4()),))
                stages.append(stage)
        self.a.hook=hook
        with self.a.runtime():pass
        self.assertEqual(stages,['after_durable_open','after_final_guard','after_local_commit_before_close'])
        self.no_open()
        print(BANNER,'OPEN WITNESS durable before permit, after last guard, after actual local COMMIT ACK, then CLOSE',flush=True)

    def test_known_same_transaction_abort_can_close(self):
        with self.assertRaisesRegex(ValueError,'synthetic known abort'):
            with self.a.runtime():raise ValueError('synthetic known abort')
        with self.lab.oracle.connect() as w:
            self.assertEqual(w.execute('SELECT phase FROM w.ops').fetchall(),[('closed_abort',)])
        self.no_open();self.takeover()

    def test_replaced_transaction_exception_never_closes_original_as_abort(self):
        self.lab.restore()
        with self.assertRaises(FenceDenied):
            with self.a.runtime() as g:
                g.c.commit()
                g.c.execute('SELECT txid_current()')
                raise ValueError('synthetic transaction replacement')
        with self.lab.oracle.connect() as w:
            self.assertEqual(w.execute('SELECT phase FROM w.ops').fetchall(),[('unknown',)])
        with self.lab.oracle.connect('B') as w:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):w.execute('SELECT w.reserve(1,%s)',(str(uuid4()),))


class PoolIntegrationTests(IntegrationFixture):
    def setUp(self):
        super().setUp();self.pool=Pool(self.lab);self.addCleanup(self.pool.close)
        self.a=Broker(self.lab,pool=self.pool)
    def witness(self,c,label):
        user,pid,tx=c.execute('SELECT session_user,pg_backend_pid(),txid_current()::text').fetchone()
        self.assertEqual(user,'cac_ctx_runtime')
        print(BANNER,'PGBOUNCER',label,'pid',pid,'fullxid',tx,flush=True)
        return pid,tx
    def stale(self,old,token,ct,wt):
        with self.pool.connect() as c:
            new=self.witness(c,'reuse-denies-old-context')
            self.assertEqual(new[0],old[0]);self.assertNotEqual(new[1],old[1])
            for key,value in [('cac.poc_context',token),('cac.fence_ticket',ct),('cac.w_ticket',wt)]:
                c.execute('SELECT set_config(%s,%s,true)',(key,value))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute('SELECT store FROM poc.records')
            c.rollback()
    def unknown_blocks_takeover(self):
        with self.lab.oracle.connect() as w:
            self.assertEqual(w.execute("SELECT count(*) FROM w.ops WHERE phase='unknown'").fetchone(),(1,))
        self.lab.restore()
        with self.assertRaises(FenceDenied):self.b.activate(1,str(uuid4()))
        self.assertFalse(self.a.ready());self.assertFalse(self.b.ready())
        print(BANNER,'INERROR binding cannot be confirmed: UNKNOWN retained, successor BLOCKED',flush=True)
    def test_pool_commit_and_takeover_reuse(self):
        with self.a.runtime() as g:
            token=self.scope(self.a,g);old=self.witness(g.c,'valid-commit');ct,wt=g.ticket,g.wticket
            g.c.execute("SELECT set_config('cac.w_ticket',%s,false)",(wt,))
        self.no_open();self.stale(old,token,ct,wt);self.takeover();self.stale(old,token,ct,wt)
    def test_pool_rollback_and_takeover_reuse(self):
        with self.assertRaises(psycopg.errors.DivisionByZero):
            with self.a.runtime() as g:
                token=self.scope(self.a,g);old=self.witness(g.c,'before-rollback');ct,wt=g.ticket,g.wticket
                g.c.execute('SELECT 1/0')
        self.stale(old,token,ct,wt);self.unknown_blocks_takeover();self.stale(old,token,ct,wt)
    def test_pool_actual_cancel_and_takeover_reuse(self):
        with self.assertRaises(psycopg.errors.QueryCanceled) as cancelled:
            with self.a.runtime() as g:
                token=self.scope(self.a,g);old=self.witness(g.c,'before-cancel');ct,wt=g.ticket,g.wticket
                with concurrent.futures.ThreadPoolExecutor(1) as workers:
                    pending=workers.submit(g.c.execute,'SELECT pg_sleep(10)')
                    with self.lab.connect() as observer:
                        observer.autocommit=True;end=time.monotonic()+2
                        while observer.execute('SELECT wait_event FROM pg_stat_activity WHERE pid=%s',(old[0],)).fetchone()!=('PgSleep',):
                            if time.monotonic()>end:self.fail('Missing real PgSleep cancellation barrier')
                            time.sleep(.01)
                        self.assertEqual(observer.execute('SELECT pg_cancel_backend(%s)',(old[0],)).fetchone(),(True,))
                    pending.result(timeout=3)
        self.assertEqual(cancelled.exception.diag.message_primary,'canceling statement due to user request')
        print(BANNER,'actual pg_cancel_backend user-request ACK',flush=True)
        self.stale(old,token,ct,wt);self.unknown_blocks_takeover();self.stale(old,token,ct,wt)
