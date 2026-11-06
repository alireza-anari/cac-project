"""Q_SURVIVAL_ONLY. Actual upstream ACK, actual lost TLS downstream reply."""
import unittest
from uuid import uuid4
from recovery_fencing.lab import S1
from h_quorum.common import BANNER,Denied
from h_quorum.integration_lab import IntegrationLab
from h_quorum.broker import Broker
from h_quorum.reply_loss import ReplyLoss
from h_quorum.rpc import Client
from h_quorum.authority import Root

class ReplyLossTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lab=IntegrationLab()
    @classmethod
    def tearDownClass(cls):cls.lab.close()
    def setUp(self):
        self.lab.reset();self.a=Broker(self.lab);self.a.activate(0,str(uuid4()))
        with self.a.runtime() as g:self.scope(g)
        self.lab.restore();self.b=Broker(self.lab,'B')
    def scope(self,g,action='read',body=None):g.install(self.a.issue(g.challenge(),action=action,body=body or {}));self.assertEqual(g.records(),[S1])
    def proxy(self,action,broker):
        proxy=ReplyLoss(self.lab.rootcfg,action);self.addCleanup(proxy.close)
        broker.root=Client(proxy.cfg,broker.node+'_coord',self.lab.namespace);return proxy
    def state(self):return Root(self.lab.rootcfg).read(self.lab.namespace)[0]
    def test_00_lost_durable_open_reply_retains_ungranted_hold(self):
        proxy=self.proxy('admit',self.a);gate=self.a.runtime()
        with self.assertRaises(Denied):
            with gate:self.fail('Missing OPEN reply reached application code')
        self.assertEqual(proxy.seen,[dict(action='admit',namespace=self.lab.namespace,upstream_ack=True)])
        view=self.a.inspect();self.assertEqual((view['open'],view['unknown'],view['granted']),(1,0,0))
        op=self.state()['ops'][gate.operation];self.assertTrue(op['binding']==gate.binding);self.assertEqual(op['phase'],'OPEN')
        self.lab.replay()
        with self.assertRaises(Denied):self.b.activate(1,str(uuid4()))
        self.assertFalse(self.b.ready());self.assertEqual(self.a.inspect()['open'],1)
        print(BANNER,'ACTUAL TLS OPEN ACK LOST after upstream majority ACK; no first use; durable ungranted hold retained',flush=True)
    def test_01_lost_root_close_reply_after_actual_protected_commit_does_not_undo_outcome(self):
        body={'body':'synthetic-actual-commit-lost-root-close'}
        with self.assertRaises(Denied):
            with self.a.runtime(action='probe',body=body) as gate:
                self.scope(gate,'probe',body)
                self.assertEqual(gate.c.execute('UPDATE poc.records SET body=%s WHERE store=%s',(body['body'],S1)).rowcount,1)
                proxy=self.proxy('close',self.a)
        self.assertEqual(len(proxy.seen),1)
        self.assertEqual(self.state()['ops'][gate.operation]['phase'],'CLOSED_COMMIT')
        self.assertEqual((self.a.inspect()['open'],self.a.inspect()['unknown']),(0,0))
        with self.lab.connect() as c:self.assertEqual(c.execute('SELECT body FROM poc.records WHERE store=%s',(S1,)).fetchone(),(body['body'],))
        self.lab.replay();self.lab.restore();self.b=Broker(self.lab,'B');self.b.activate(1,str(uuid4()))
        with self.b.runtime() as g:g.install(self.b.issue(g.challenge()));self.assertEqual(g.records(),[S1])
        print(BANNER,'ACTUAL TLS CLOSE ACK LOST after exact PG COMMIT ACK + Root CLOSE; caller denied, durable outcome preserved, successor positive after known close',flush=True)
    def test_02_issuer_never_returns_token_after_actual_lost_root_close_reply(self):
        issuer=Broker(self.lab);proxy=self.proxy('close',issuer);returned=[]
        with self.a.runtime() as g:
            with self.assertRaises(Denied):returned.append(issuer.issue(g.challenge()))
        self.assertEqual(returned,[]);self.assertEqual(len(proxy.seen),1)
        self.assertEqual((self.a.inspect()['open'],self.a.inspect()['unknown']),(0,0))
        self.assertTrue(any(op['binding']['kind']=='issuer' and op['phase']=='CLOSED_COMMIT' for op in self.state()['ops'].values()))
        print(BANNER,'ACTUAL issuer CLOSE reply dropped over TLS; no token returned despite positive durable Root outcome',flush=True)
    def pg_lost_reply(self,action):
        from h_quorum.pg_reply_loss import PgReplyLoss
        proxy=PgReplyLoss(self.lab);self.addCleanup(proxy.close);self.a.pool=proxy
        body={'body':'synthetic-pg-terminal-ack-lost'}
        with self.assertRaises(Denied):
            with self.a.runtime(action='probe',body=body) as gate:
                self.scope(gate,'probe',body)
                self.assertEqual(gate.c.execute('UPDATE poc.records SET body=%s WHERE store=%s',(body['body'],S1)).rowcount,1)
                proxy.armed=action
                if action=='ROLLBACK':raise ValueError('synthetic exact abort but wire ACK will be lost')
        self.assertEqual(proxy.seen,[dict(action=action,command_complete=action,ready='IDLE',reply_dropped=True)])
        with self.lab.connect() as observer:
            self.assertEqual(observer.execute('SELECT body FROM poc.records WHERE store=%s',(S1,)).fetchone(),(body['body'] if action=='COMMIT' else 'synthetic',))
        self.assertEqual(self.state()['ops'][gate.operation]['phase'],'UNKNOWN')
        self.assertEqual(self.a.inspect()['unknown'],1)
        with self.assertRaises(Denied):self.b.activate(1,str(uuid4()))
        self.assertFalse(self.b.ready());self.assertEqual(self.b.command('status',{})['owner'],'A')
        print(BANNER,'ACTUAL PG WIRE TERMINAL ACK LOST',action,'server CommandComplete+ReadyForQuery IDLE withheld; exact persisted data observed; UNKNOWN keeps successor blocked',flush=True)
    def test_03_actual_lost_pg_commit_reply_keeps_unknown(self):self.pg_lost_reply('COMMIT')
    def test_04_actual_lost_pg_abort_reply_keeps_unknown(self):self.pg_lost_reply('ROLLBACK')
