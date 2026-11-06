"""W_ORACLE_ASSUMED. Real PostgreSQL contract, not real W-root evidence."""
import unittest
import threading
import time
from uuid import uuid4
import psycopg

from w_oracle.lab import OracleLab, BANNER


class OracleContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lab = OracleLab()

    @classmethod
    def tearDownClass(cls):
        cls.lab.close()

    def setUp(self):
        self.lab.reset()
        print(BANNER, 'independent-test namespace', self.lab.namespace, flush=True)

    def test_initial_activation_and_stale_cas_denial(self):
        request = str(uuid4())
        with self.lab.connect('A') as c:
            result = c.execute('SELECT w.reserve(0,%s)', (request,)).fetchone()[0]
        self.assertEqual(result['epoch'], 1)
        with self.lab.connect('B') as c:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                c.execute('SELECT w.reserve(0,%s)', (str(uuid4()),))

    def activate(self, node='A'):
        request = str(uuid4())
        with self.lab.connect(node) as c:
            c.execute('SELECT w.reserve(0,%s)', (request,))
        with self.lab.connect(node) as c:
            c.execute('SELECT w.activate(%s)', (request,))

    def binding(self):
        a = self.lab.cfg['actors']['A']
        return [str(uuid4()),str(uuid4()),'b'*64,self.lab.parent.cfg['A']['sid'],
                123,'456','runtime','cac_ctx_runtime',self.lab.namespace,
                self.lab.cfg['policy'],a['incarnation'],a['manifest']]

    def admit(self, c, args):
        return c.execute('SELECT w.admit('+','.join(['%s']*12)+')',args).fetchone()[0]

    def test_open_is_committed_before_ticket_and_same_key_is_idempotent(self):
        self.activate(); args=self.binding()
        with self.lab.connect('A') as c:
            ticket=self.admit(c,args);c.commit()
            with self.lab.connect() as observer:
                self.assertEqual(observer.execute('SELECT phase,dbpid,dbtx FROM w.ops').fetchone(),('open',123,'456'))
            self.assertTrue(self.admit(c,args)==ticket,'Retry did not return original ticket')
            c.commit()
        with self.lab.connect() as c:
            self.assertEqual(c.execute('SELECT count(*) FROM w.ops').fetchone(),(1,))

    def test_same_key_changed_intent_is_denied(self):
        self.activate();args=self.binding()
        with self.lab.connect('A') as c:
            self.admit(c,args);c.commit();args[2]='c'*64
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):self.admit(c,args)

    def test_same_key_retry_cannot_rebind_original_holder(self):
        self.activate();args=self.binding()
        with self.lab.connect('A') as original:ticket=self.admit(original,args)
        with self.lab.connect('A') as retry:
            self.assertTrue(self.admit(retry,args)==ticket,'Retry changed original idempotent outcome')
            retry.commit()
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):retry.execute('SELECT w.hold(%s)',(ticket,))
        with self.lab.connect('B') as rival:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):rival.execute('SELECT w.reserve(1,%s)',(str(uuid4()),))

    def test_known_local_read_commit_ack_closes_exact_bound_hold(self):
        # Trusted coordinator observes actual PG COMMIT ACK; no guessed outcome.
        with self.lab.parent.connect() as admin:
            installed=admin.execute("SELECT to_regprocedure('fence.system_id()') IS NOT NULL").fetchone()[0]
        if not installed:self.lab.parent.reset()
        self.activate()
        with self.lab.parent.connect('A','cac_ctx_runtime') as local,self.lab.connect('A') as w:
            pid,tx,sid=local.execute('SELECT pg_backend_pid(),txid_current()::text,fence.system_id()').fetchone()
            args=self.binding();args[3:6]=[sid,pid,tx]
            ticket=self.admit(w,args);w.commit()
            w.execute('SELECT w.hold(%s)',(ticket,))
            with self.lab.connect('B') as rival:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    rival.execute('SELECT w.reserve(1,%s)',(str(uuid4()),))
            local.commit()
            self.assertEqual(local.info.transaction_status,psycopg.pq.TransactionStatus.IDLE)
            w.execute('SELECT w.close(%s,%s,%s,%s,%s)',(ticket,'commit',pid,tx,sid));w.commit()
        with self.lab.connect() as observer:
            self.assertEqual(observer.execute('SELECT phase FROM w.ops').fetchone(),('closed_commit',))
        with self.lab.connect('B') as c:
            self.assertEqual(c.execute('SELECT w.reserve(1,%s)',(str(uuid4()),)).fetchone()[0]['epoch'],2)

    def test_checker_cannot_admit_or_close(self):
        self.activate()
        with self.lab.connect('A',check=True) as c:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):self.admit(c,self.binding())
        with self.lab.connect('A',check=True) as c:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                c.execute("SELECT w.close('not-a-ticket','commit',123,'456',%s)",(self.lab.parent.cfg['A']['sid'],))

    def test_orphan_open_blocks_takeover_after_disconnect(self):
        self.activate()
        with self.lab.connect('A') as c:self.admit(c,self.binding())
        with self.lab.connect('B') as c:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                c.execute('SELECT w.reserve(1,%s)',(str(uuid4()),))
        with self.lab.connect() as c:self.assertEqual(c.execute('SELECT phase FROM w.ops').fetchone(),('open',))

    def test_revoke_blocks_new_admission_and_delayed_first_use(self):
        self.activate();args=self.binding()
        with self.lab.connect('A') as holder:
            ticket=self.admit(holder,args);holder.commit()
            with self.lab.connect('B') as revoker:revoker.execute('SELECT w.revoke(1)')
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):holder.execute('SELECT w.hold(%s)',(ticket,))
        with self.lab.connect('A') as c:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):self.admit(c,self.binding())

    def test_copy_actor_with_wrong_incarnation_or_sid_denies(self):
        self.activate()
        for index,value in [(3,self.lab.parent.cfg['B']['sid']),(10,str(uuid4()))]:
            with self.subTest(field=index),self.lab.connect('A') as c:
                args=self.binding();args[index]=value
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):self.admit(c,args)

    def test_declared_continuity_loss_denies_without_reinitialization(self):
        self.activate()
        with self.lab.connect() as c:c.execute('UPDATE w.control SET continuity=false')
        with self.lab.connect('A') as c:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute('SELECT w.status()')
        with self.lab.connect() as c:self.assertEqual(c.execute('SELECT epoch FROM w.state').fetchone(),(1,))

    def test_real_oracle_restart_preserves_durable_open(self):
        self.activate()
        with self.lab.connect('A') as c:self.admit(c,self.binding())
        self.lab.parent.docker('restart','--time','1',self.lab.cfg['container'])
        import time
        end=time.monotonic()+15
        while True:
            try:
                with self.lab.connect() as c:
                    self.assertEqual(c.execute('SELECT count(*) FROM w.ops WHERE phase=\'open\'').fetchone(),(1,))
                break
            except psycopg.Error:
                if time.monotonic()>end:raise
                time.sleep(.1)
        with self.lab.connect('B') as c:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute('SELECT w.reserve(1,%s)',(str(uuid4()),))

    def test_close_never_overwrites_concurrent_unknown(self):
        self.activate(); args=self.binding()
        with self.lab.connect('A') as holder, self.lab.connect('A') as uncertain:
            ticket=self.admit(holder,args); holder.commit()
            holder.execute("SET LOCAL lock_timeout='4000ms'; SET LOCAL statement_timeout='6000ms'")
            pid=holder.execute('SELECT pg_backend_pid()').fetchone()[0]
            holder.execute('SELECT w.hold(%s)',(ticket,))
            uncertain.execute('SELECT w.unknown(%s)',(ticket,))
            result=[]
            def close():
                try:
                    holder.execute('SELECT w.close(%s,%s,%s,%s,%s)',(ticket,'commit',args[4],args[5],args[3]))
                    holder.commit(); result.append('CLOSED')
                except psycopg.errors.InsufficientPrivilege:
                    holder.rollback(); result.append('DENIED')
                except Exception as error:
                    result.append(type(error).__name__)
            worker=threading.Thread(target=close); worker.start()
            blocked=False
            try:
                end=time.monotonic()+2
                with self.lab.connect() as observer:
                    observer.autocommit=True
                    while time.monotonic()<end:
                        if observer.execute('SELECT cardinality(pg_blocking_pids(%s))>0',(pid,)).fetchone()[0]:
                            blocked=True; break
                        time.sleep(.01)
            finally:
                uncertain.commit(); worker.join(7)
            self.assertFalse(worker.is_alive(),'CLOSE thread did not finish')
            self.assertTrue(blocked,'Race barrier did not observe actual PostgreSQL row-lock wait')
            self.assertEqual(result,['DENIED'],'CLOSE overwrote concurrent UNKNOWN')
        with self.lab.connect() as observer:
            self.assertEqual(observer.execute('SELECT phase FROM w.ops').fetchone(),('unknown',))

    def proof_args(self, ticket, args):
        return ['c'*64,'guard',ticket,args[3],args[4],args[5],args[11],args[2],args[7]]

    def test_attestation_requires_live_hold_and_exact_intent(self):
        self.activate(); args=self.binding()
        with self.lab.connect('A') as holder:
            ticket=self.admit(holder,args); holder.commit()
            values=self.proof_args(ticket,args)
            with self.lab.connect('A',check=True) as check:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    check.execute('SELECT w.attest('+','.join(['%s']*9)+')',values)
            holder.execute('SELECT w.hold(%s)',(ticket,))
            for index,value in [(7,''),(7,'d'*64),(4,124),(5,'457'),(6,'e'*64)]:
                with self.subTest(field=index,value=value),self.lab.connect('A',check=True) as check:
                    changed=values.copy(); changed[index]=value
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                        check.execute('SELECT w.attest('+','.join(['%s']*9)+')',changed)
            with self.lab.connect('A',check=True) as check:
                proof=check.execute('SELECT w.attest('+','.join(['%s']*9)+')',values).fetchone()[0]
                self.assertTrue(check.execute('SELECT w.verify('+','.join(['%s']*10)+')',[proof,*values]).fetchone()[0])
                self.assertFalse(check.execute('SELECT w.verify('+','.join(['%s']*10)+')',[proof+'00',*values]).fetchone()[0])
                changed=values.copy(); changed[0]='d'*64
                self.assertFalse(check.execute('SELECT w.verify('+','.join(['%s']*10)+')',[proof,*changed]).fetchone()[0])
            holder.rollback()
            with self.lab.connect('A',check=True) as check:
                self.assertFalse(check.execute('SELECT w.verify('+','.join(['%s']*10)+')',[proof,*values]).fetchone()[0])

    def test_old_hold_cannot_attest_under_changed_namespace_or_policy(self):
        self.activate(); args=self.binding()
        with self.lab.connect('A') as holder:
            ticket=self.admit(holder,args); holder.commit(); holder.execute('SELECT w.hold(%s)',(ticket,))
            with self.lab.connect() as admin:
                admin.execute('UPDATE w.control SET policy=policy+1,namespace=%s',(str(uuid4()),))
            with self.lab.connect('A',check=True) as check:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    check.execute('SELECT w.attest('+','.join(['%s']*9)+')',self.proof_args(ticket,args))

    def test_revocation_invalidates_previous_attestation(self):
        self.activate(); args=self.binding()
        with self.lab.connect('A') as holder:
            ticket=self.admit(holder,args); holder.commit(); holder.execute('SELECT w.hold(%s)',(ticket,))
            values=self.proof_args(ticket,args)
            with self.lab.connect('A',check=True) as check:
                proof=check.execute('SELECT w.attest('+','.join(['%s']*9)+')',values).fetchone()[0]
            with self.lab.connect('B') as revoker:
                revoker.execute('SELECT w.revoke(1)')
            with self.lab.connect('A',check=True) as check:
                self.assertFalse(check.execute('SELECT w.verify('+','.join(['%s']*10)+')',[proof,*values]).fetchone()[0])
