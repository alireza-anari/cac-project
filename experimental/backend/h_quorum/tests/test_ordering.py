"""Q_SURVIVAL_ONLY. Actual protected SQL at the grant/revoke/commit cuts."""
import concurrent.futures
import unittest
from uuid import uuid4
import psycopg
from recovery_fencing.lab import S1
from h_quorum.common import BANNER,Denied
from h_quorum.integration_lab import IntegrationLab
from h_quorum.broker import Broker

class OrderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lab=IntegrationLab()
    @classmethod
    def tearDownClass(cls):cls.lab.close()
    def setUp(self):
        self.lab.reset();self.a=Broker(self.lab);self.a.activate(0,str(uuid4()))
        with self.a.runtime() as g:self.scope(g)
    def scope(self,g,action='read',body=None):
        g.install(self.a.issue(g.challenge(),action=action,body=body or {}));self.assertEqual(g.records(),[S1])
    def successor(self):
        self.lab.restore();return Broker(self.lab,'B')
    def blocked(self,b,label):
        with self.assertRaises(Denied):
            b.activate(1,str(uuid4()))
            # Only reached on a real unsafe result (or intentional hold mutant).
            with b.runtime() as successor:
                successor.install(b.issue(successor.challenge()));self.assertEqual(successor.records(),[S1])
            if hasattr(self,'held_gate') and label=='before_local_commit':self.held_gate.c.commit()
            print(BANNER,'UNSAFE HOLD WITNESS successor READY and fresh scoped SQL while old protected COMMIT possible; cut',label,flush=True)
        state=b.command('status',{});view=b.inspect()
        self.assertEqual((state['epoch'],state['owner'],state['phase']),(1,'A','REVOKING'))
        self.assertGreater(view['open']+view['unknown'],0)
        print(BANNER,label,'successor denied; actual R revision',view['state_revision'],'OPEN',view['open'],'UNKNOWN',view['unknown'],flush=True)
    def test_00_actual_late_protected_commit_holds_successor_until_root_close(self):
        b=self.successor();cuts=[];body={'body':'synthetic-late-commit'}
        def hook(label):
            if label in ('before_local_commit','after_local_commit_before_close'):
                self.blocked(b,label);cuts.append(label)
                with self.lab.connect() as observer:
                    actual=observer.execute('SELECT body FROM poc.records WHERE store=%s',(S1,)).fetchone()[0]
                    self.assertEqual(actual,body['body'] if label=='after_local_commit_before_close' else 'synthetic')
        with self.a.runtime(action='probe',body=body) as g:
            self.scope(g,'probe',body)
            self.assertEqual(g.c.execute('UPDATE poc.records SET body=%s WHERE store=%s',(body['body'],S1)).rowcount,1)
            self.held_gate=g
            # Issuer's independent COMMIT has already completed. Only the
            # protected runtime transaction below is the intended crash cut.
            self.a.hook=hook
        self.assertEqual(cuts,['before_local_commit','after_local_commit_before_close'])
        self.assertEqual(self.a.inspect()['open'],0)
        # Refresh the independent logical restore after the actual old COMMIT.
        self.lab.restore();b=Broker(self.lab,'B');b.activate(1,str(uuid4()))
        with b.runtime() as g:
            g.install(b.issue(g.challenge()));self.assertEqual(g.records(),[S1])
            self.assertEqual(g.c.execute('SELECT body FROM poc.records WHERE store=%s',(S1,)).fetchone(),(body['body'],))
        self.assertFalse(self.a.ready());self.assertTrue(b.ready())
    def test_01_revoke_after_open_before_first_use_denies_and_retains_unknown(self):
        b=self.successor();cuts=[]
        def hook(label):
            if label=='after_durable_open':
                self.assertEqual(self.a.inspect()['granted'],0)
                b.command('revoke',dict(expected=1));cuts.append(label)
        self.a.hook=hook
        with self.assertRaises(Denied):
            with self.a.runtime() as g:
                self.assertEqual(self.a.inspect()['granted'],1)
                print(BANNER,'UNSAFE FIRST USE WITNESS actual SQL final_check accepted a grant ordered after REVOKE',g.pid,g.tx,flush=True)
                self.fail('Revoked ungranted operation reached application code')
        self.assertEqual(cuts,['after_durable_open']);self.assertEqual(self.a.inspect()['unknown'],1)
        self.blocked(b,'revoked-before-first-use')
    def test_02_actual_delayed_receipt_cannot_enter_replaced_transaction(self):
        cuts=[]
        def hook(label):
            if label=='after_first_use':
                # Actual local transaction replacement, not a changed metadata argument.
                with self.lab.connect() as observer:
                    pid=observer.execute("SELECT pid FROM pg_stat_activity WHERE usename='cac_ctx_runtime' AND xact_start IS NOT NULL").fetchall()
                self.assertEqual(len(pid),1)
                gate.c.commit();new=gate.c.execute('SELECT txid_current()::text').fetchone()[0]
                self.assertNotEqual(new,gate.tx);cuts.append(label)
        self.a.hook=hook;gate=self.a.runtime()
        with self.assertRaises(Denied):
            with gate:self.fail('Old grant entered replacement transaction')
        self.assertEqual(cuts,['after_first_use']);self.assertEqual(self.a.inspect()['unknown'],1)
    def test_03_two_real_concurrent_scoped_transactions_have_distinct_bindings(self):
        one=self.a.runtime();two=self.a.runtime();one.__enter__()
        try:
            self.scope(one);two.__enter__()
            try:
                self.scope(two)
                self.assertNotEqual(one.pid,two.pid);self.assertNotEqual(one.tx,two.tx)
                with concurrent.futures.ThreadPoolExecutor(2) as workers:
                    results=[workers.submit(g.records) for g in (one,two)]
                    self.assertEqual([f.result(timeout=30) for f in results],[[S1],[S1]])
                print(BANNER,'CONCURRENT ACTUAL SQL bindings',one.pid,one.tx,two.pid,two.tx,flush=True)
            except BaseException:
                two._unknown();two._close();raise
            else:two.__exit__(None,None,None)
        except BaseException:
            one._unknown();one._close();raise
        else:one.__exit__(None,None,None)
        self.assertEqual(self.a.inspect()['open'],0)
    def test_04_prepared_transactions_are_actually_disabled(self):
        with self.lab.connect() as observer:
            self.assertEqual(observer.execute('SHOW max_prepared_transactions').fetchone(),('0',))
            self.assertEqual(observer.execute('SHOW fsync').fetchone(),('on',))
            self.assertEqual(observer.execute('SHOW synchronous_commit').fetchone(),('on',))
        with self.assertRaises(Denied):
            with self.a.runtime() as g:
                self.scope(g)
                with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState) as rejected:
                    g.c.execute("PREPARE TRANSACTION 'synthetic-h-denied'")
                self.assertEqual(rejected.exception.sqlstate,'55000')
                print(BANNER,'ACTUAL PREPARE denied SQLSTATE55000; local status',g.c.info.transaction_status.name,'coordinator must deny ambiguous exit',flush=True)
        self.assertEqual(self.a.inspect()['unknown'],1)
    def test_05_actual_admitted_contenders_one_ready_owner_and_scoped_positive(self):
        b=self.successor();b.command('revoke',dict(expected=1))
        def contender(broker):
            try:return broker.node,broker.activate(1,str(uuid4()))['epoch']
            except Denied:return broker.node,'DENIED'
        with concurrent.futures.ThreadPoolExecutor(2) as workers:results=list(workers.map(contender,(self.a,b)))
        self.assertEqual(sum(epoch==2 for _,epoch in results),1)
        self.assertEqual(sum(epoch=='DENIED' for _,epoch in results),1)
        owner=next(node for node,epoch in results if epoch==2);winner=self.a if owner=='A' else b
        self.assertEqual(winner.command('status',{})['owner'],owner)
        self.assertEqual([self.a.ready(),b.ready()],[owner=='A',owner=='B'])
        with winner.runtime() as g:
            g.install(winner.issue(g.challenge()));self.assertEqual(g.records(),[S1])
        print(BANNER,'ACTUAL ADMITTED TAKEOVER CAS',results,'only owner',owner,'READY and fresh scoped SQL positive',flush=True)
