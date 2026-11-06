"""Q_SURVIVAL_ONLY. Actual transaction-pool reuse with current-R SQL enforcement."""
import concurrent.futures
import time
import unittest
from uuid import uuid4
import psycopg
from recovery_proof.pool_lab import Pool
from recovery_fencing.lab import S1
from h_quorum.common import BANNER,Denied
from h_quorum.integration_lab import IntegrationLab
from h_quorum.broker import Broker

class PoolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lab=IntegrationLab()
    @classmethod
    def tearDownClass(cls):cls.lab.close()
    def setUp(self):
        self.lab.reset();self.pool=Pool(self.lab);self.addCleanup(self.pool.close)
        self.a=Broker(self.lab,pool=self.pool);self.a.activate(0,str(uuid4()))
    def scope(self,g):
        token=self.a.issue(g.challenge());g.install(token);self.assertEqual(g.records(),[S1]);return token
    def witness(self,c,label):
        user,pid,tx=c.execute('SELECT session_user,pg_backend_pid(),txid_current()::text').fetchone()
        self.assertEqual(user,'cac_ctx_runtime')
        print(BANNER,'PgBouncer',label,'backend PID',pid,'fullxid',tx,flush=True);return pid,tx
    def stale(self,old,token,ticket,intent,label):
        with self.pool.connect() as c:
            now=self.witness(c,label);self.assertEqual(now[0],old[0]);self.assertNotEqual(now[1],old[1])
            for key,value in [('cac.poc_context',token),('cac.h_ticket',ticket),('cac.h_intent',intent)]:c.execute('SELECT set_config(%s,%s,true)',(key,value))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute('SELECT store FROM poc.records')
            c.rollback()
    def test_00_commit_persistent_hostile_session_and_takeover_same_backend(self):
        with self.a.runtime() as g:
            token=self.scope(g);old=self.witness(g.c,'before known COMMIT');ticket=g.ticket;intent=g.binding['digest']
            for key,value in [('cac.poc_context',token),('cac.h_ticket',ticket),('cac.h_intent',intent)]:g.c.execute('SELECT set_config(%s,%s,false)',(key,value))
        with self.pool.connect() as c:
            reused=self.witness(c,'persistent hostile session');self.assertEqual(reused[0],old[0]);self.assertNotEqual(reused[1],old[1])
            self.assertTrue(c.execute("SELECT current_setting('cac.poc_context',true)").fetchone()[0]==token,'Expected persistent hostile context')
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute('SELECT store FROM poc.records')
            c.rollback()
        self.lab.restore();b=Broker(self.lab,'B');b.activate(1,str(uuid4()))
        with b.runtime() as g:g.install(b.issue(g.challenge()));self.assertEqual(g.records(),[S1])
        self.stale(old,token,ticket,intent,'after actual B takeover')
        self.assertFalse(self.a.ready());self.assertTrue(b.ready())
    def test_01_known_abort_closes_hold_and_reuses_backend_safely(self):
        with self.assertRaisesRegex(ValueError,'synthetic exact abort'):
            with self.a.runtime() as g:
                token=self.scope(g);old=self.witness(g.c,'before exact ABORT');ticket=g.ticket;intent=g.binding['digest']
                raise ValueError('synthetic exact abort')
        self.assertEqual(self.a.inspect()['open'],0);self.assertEqual(self.a.inspect()['unknown'],0)
        self.stale(old,token,ticket,intent,'after exact ABORT')
        with self.a.runtime() as g:self.scope(g)
    def test_02_actual_cancel_reuses_backend_but_unknown_blocks_successor(self):
        self.lab.restore();b=Broker(self.lab,'B')
        with self.assertRaises(psycopg.errors.QueryCanceled) as cancelled:
            with self.a.runtime() as g:
                token=self.scope(g);old=self.witness(g.c,'before actual cancellation');ticket=g.ticket;intent=g.binding['digest']
                with concurrent.futures.ThreadPoolExecutor(1) as workers:
                    future=workers.submit(g.c.execute,'SELECT pg_sleep(20)')
                    with self.lab.connect() as observer:
                        observer.autocommit=True;deadline=time.monotonic()+3
                        while observer.execute('SELECT wait_event FROM pg_stat_activity WHERE pid=%s',(old[0],)).fetchone()!=('PgSleep',):
                            if time.monotonic()>deadline:self.fail('Missing actual PgSleep cancellation witness')
                            time.sleep(.01)
                        self.assertEqual(observer.execute('SELECT pg_cancel_backend(%s)',(old[0],)).fetchone(),(True,))
                    future.result(timeout=4)
        self.assertEqual(cancelled.exception.diag.message_primary,'canceling statement due to user request')
        self.assertEqual(self.a.inspect()['unknown'],1)
        self.stale(old,token,ticket,intent,'after actual user-request cancellation')
        with self.assertRaises(Denied):b.activate(1,str(uuid4()))
        self.assertFalse(b.ready());self.assertFalse(self.a.ready())
        print(BANNER,'actual PgSleep -> pg_cancel_backend; SQLSTATE57014 user request; persistent UNKNOWN blocks successor without timeout clearing',flush=True)
