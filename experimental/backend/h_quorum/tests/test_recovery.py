"""Q_SURVIVAL_ONLY. Actual W restore/current R and complete replay proofs."""
import unittest
from uuid import uuid4
import psycopg
from recovery_fencing.lab import S1
from h_quorum.common import BANNER,Denied
from h_quorum.integration_lab import IntegrationLab
from h_quorum.broker import Broker

class RecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lab=IntegrationLab()
    @classmethod
    def tearDownClass(cls):cls.lab.close()
    def scope(self,a,action='read',body=None):
        with a.runtime(action=action,body=body or {}) as g:
            token=a.issue(g.challenge(),action=action,body=body or {});g.install(token)
            self.assertEqual(g.records(),[S1])
            pid,tx,sid=g.c.execute('SELECT pg_backend_pid(),txid_current()::text,fence.system_id()').fetchone()
            self.assertEqual((pid,tx,sid),(g.pid,g.tx,g.sid))
            if action=='probe':self.assertEqual(g.c.execute('UPDATE poc.records SET body=%s WHERE store=%s',(body['body'],S1)).rowcount,1)
            proof=a.inspect()
            print(BANNER,'SCOPED SQL',a.node,action,'pid',pid,'fullxid',tx,'PG SID',sid,'R revision',proof['state_revision'],'head',proof['head'],flush=True)
    def start(self):
        self.lab.reset();a=Broker(self.lab);a.activate(0,str(uuid4()));self.scope(a);return a
    def require_recovery(self):
        self.assertTrue(all(hasattr(self.lab,name) for name in ('dump_w','restore_w','restore','replay')),'Actual W projection/restore and B admission fixture is not implemented')
    def test_00_real_old_w_restore_never_revives_old_owner(self):
        a=self.start();self.require_recovery();old=self.lab.dump_w()
        self.lab.restore();b=Broker(self.lab,'B');b.activate(1,str(uuid4()));self.scope(b)
        self.lab.restore_w(old)
        with self.lab.connect('C') as c:self.assertEqual(c.execute('SELECT epoch FROM anchor.state').fetchone(),(1,))
        status=b.command('status',{});self.assertEqual((status['epoch'],status['owner']),(2,'B'))
        with self.lab.connect() as c:self.assertTrue(c.execute('SELECT h_guard.c_is_ready()').fetchone()[0],'Legacy cache precondition must actually allow old A')
        accepted=a.ready()
        if accepted:
            # Narrow current-head sensitivity: stale readiness alone is wrong.
            # Keep current durable ADMIT enforced; do not claim a data bypass.
            with self.assertRaises(Denied):
                with a.runtime():self.fail('Current Root ADMIT also accepted old owner')
            print(BANNER,'STALE HEAD READINESS WITNESS old A ready despite R2/B; independent current Root ADMIT still denied',flush=True)
        self.assertFalse(accepted,'Restored old W revived old-owner readiness under current R')
        for role,query in [('cac_ctx_runtime','SELECT poc.challenge()'),('cac_ctx_runtime','SELECT store FROM poc.records'),('cac_ctx_runtime',"UPDATE poc.records SET body='synthetic-forbidden-old-owner'")]:
            with self.subTest(role=role,query=query):
                with self.lab.connect('A',role) as c:
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute(query)
        with self.assertRaises(Denied):
            with a.runtime():pass
        with self.assertRaises(Denied):a.issue('synthetic-unused-challenge') # supplemental: fresh challenge path above is already denied
        self.assertFalse(b.ready(),'Restored W must replay before successor data readiness')
        self.lab.replay();b.sync_cache();self.assertTrue(b.ready());self.scope(b,'probe',{'body':'synthetic-current-b'})
        print(BANNER,'ACTUAL W pg_dump/pg_restore e2->e1; real R2/B unchanged; oldA challenge/issuer path/RLS read+write denied; complete replay + B positive',flush=True)
    def test_01_missing_w_journal_denies_before_complete_replay(self):
        a=self.start();self.require_recovery()
        with self.lab.connect('C') as c:c.execute('DELETE FROM h_w.journal WHERE namespace=%s AND seq=0',(self.lab.namespace,))
        accepted=a.ready()
        if accepted:self.scope(a) # sensitivity witness must really execute valid scope if the control is disabled
        self.assertFalse(accepted,'Incomplete W journal was accepted for new authorization')
        with self.assertRaises(Denied):
            with a.runtime():pass
        self.lab.replay();self.assertTrue(a.ready());self.scope(a)
    def test_02_old_guard_is_quarantined_and_cannot_self_admit(self):
        a=self.start();self.require_recovery()
        self.assertTrue(hasattr(self.lab,'admit'),'Independent re-admission fixture is not implemented')
        self.lab.quarantine('A');self.lab.down('A')
        with self.assertRaisesRegex(AssertionError,'manifest'):self.lab.admit('A')
        with self.lab.connect() as c:self.assertEqual(c.execute("SELECT rolcanlogin FROM pg_roles WHERE rolname IN ('cac_ctx_runtime','cac_ctx_issuer') ORDER BY rolname").fetchall(),[(False,),(False,)])
        with self.assertRaises(psycopg.OperationalError):self.lab.connect('A','cac_ctx_runtime')
        self.lab.install('A');self.lab.admit('A');a=Broker(self.lab);a.activate(1,str(uuid4()));self.scope(a)
    def test_03_actual_w_restore_and_service_restart_cannot_forget_live_open(self):
        a=self.start();old=self.lab.dump_w();self.lab.restore();b=Broker(self.lab,'B');cuts=[]
        body={'body':'synthetic-open-survives-w-restore'}
        def hook(label):
            if label!='before_local_commit':return
            before=a.inspect();self.assertEqual(before['open'],1);self.assertEqual(before['granted'],1)
            self.lab.restore_w(old);self.lab.restart_service()
            self.assertEqual(a.inspect(),before,'W restore/service restart forgot actual current R OPEN')
            with self.assertRaises(Denied):b.activate(1,str(uuid4()))
            self.assertFalse(b.ready());self.assertEqual(b.command('status',{})['owner'],'A');cuts.append(label)
        with a.runtime(action='probe',body=body) as g:
            g.install(a.issue(g.challenge(),action='probe',body=body));self.assertEqual(g.records(),[S1])
            self.assertEqual(g.c.execute('UPDATE poc.records SET body=%s WHERE store=%s',(body['body'],S1)).rowcount,1)
            a.hook=hook # Runtime-only cut, after independent issuer already closed.
        self.assertEqual(cuts,['before_local_commit']);self.assertEqual(a.inspect()['open'],0)
        self.lab.restore();b=Broker(self.lab,'B');b.activate(1,str(uuid4()));self.scope(b)
        with self.lab.connect('B') as observer:self.assertEqual(observer.execute('SELECT body FROM poc.records WHERE store=%s',(S1,)).fetchone(),(body['body'],))
        print(BANNER,'ACTUAL W restore forgot public OPEN but current-R hold survived restart; successor blocked through old protected COMMIT until known CLOSE',flush=True)
