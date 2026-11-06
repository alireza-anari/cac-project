"""Q_SURVIVAL_ONLY. Real R lifecycle with actual open PG binding; no RLS claim."""
import unittest
from uuid import uuid4
from recovery_fencing.lab import Lab
from h_quorum.common import config,Denied,BANNER
from h_quorum.rpc import Client

class LifecycleFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cfg=config();cls.pg=Lab()
    @classmethod
    def tearDownClass(cls):cls.pg.close()
    def setUp(self):
        self.ns=str(uuid4());self.control=Client(self.cfg,'control',self.ns)
        self.actors={n:dict(sid=self.pg.cfg[n]['sid'],incarnation=str(uuid4()),manifest='a'*64,admitted=True) for n in ('A','B')}
        self.control.call('genesis',dict(actors=self.actors));self.a=Client(self.cfg,'A_coord',self.ns);self.b=Client(self.cfg,'B_coord',self.ns);self.check=Client(self.cfg,'A_check',self.ns)
        self.request=str(uuid4());self.a.call('reserve',dict(expected=0,request=self.request))
        try:active=self.a.call('activate',dict(request=self.request))
        except Denied:self.fail('Actual root ACTIVE transition is missing')
        self.assertEqual(active.get('phase'),'ACTIVE','Actual root ACTIVE transition is missing')
        self.c=self.pg.connect('A','cac_ctx_runtime');self.addCleanup(self.c.close)
        self.pid,self.tx=self.c.execute('SELECT pg_backend_pid(),txid_current()::text').fetchone()
        self.binding=dict(sid=self.actors['A']['sid'],pid=self.pid,tx=self.tx,kind='runtime',login='cac_ctx_runtime',digest='b'*64,incarnation=self.actors['A']['incarnation'],manifest=self.actors['A']['manifest'],policy=1)
    def admit(self,request=None):return self.a.call('admit',dict(self.binding,request=request or str(uuid4()),operation=str(uuid4())))

class LifecycleTests(LifecycleFixture):
    def test_open_ack_is_committed_before_first_use(self):
        receipt=self.admit();self.assertTrue(receipt['ticket']);view=self.control.call('inspect',{})
        self.assertEqual(view['open'],1);self.assertEqual(view['granted'],0);self.assertEqual(receipt['revision'],view['state_revision'])
        self.a.call('first_use',dict(ticket=receipt['ticket'],**self.binding))
        view=self.control.call('inspect',{});self.assertEqual(view['granted'],1);self.assertEqual(view['state_revision'],view['journal_revision'])
        print(BANNER,'OPEN majority ACK then FIRST_USE_GRANTED; actual PG pid/xid',self.pid,self.tx,'root revisions',receipt['revision'],view['state_revision'],flush=True)
    def test_revoke_before_first_use_denies_and_hold_blocks_successor(self):
        receipt=self.admit();self.b.call('revoke',dict(expected=1))
        with self.assertRaises(Denied):self.a.call('first_use',dict(ticket=receipt['ticket'],**self.binding))
        with self.assertRaises(Denied):self.b.call('reserve',dict(expected=1,request=str(uuid4())))
        self.assertEqual(self.control.call('inspect',{})['open'],1)
    def test_grant_before_revoke_can_finish_but_successor_waits_known_close(self):
        receipt=self.admit();self.a.call('first_use',dict(ticket=receipt['ticket'],**self.binding));self.b.call('revoke',dict(expected=1))
        with self.assertRaises(Denied):self.b.call('reserve',dict(expected=1,request=str(uuid4())))
        self.c.execute('SELECT 1');self.c.commit()
        self.a.call('close',dict(ticket=receipt['ticket'],outcome='commit',**self.binding))
        request=str(uuid4());self.assertEqual(self.b.call('reserve',dict(expected=1,request=request))['epoch'],2)
        self.b.call('activate',dict(request=request));self.assertEqual(self.check.call('status')['owner'],'B')
    def test_unknown_never_closes_even_after_actual_local_abort(self):
        receipt=self.admit();self.a.call('first_use',dict(ticket=receipt['ticket'],**self.binding));self.a.call('unknown',dict(ticket=receipt['ticket'],**self.binding));self.c.rollback()
        with self.assertRaises(Denied):self.a.call('close',dict(ticket=receipt['ticket'],outcome='abort',**self.binding))
        self.b.call('revoke',dict(expected=1))
        with self.assertRaises(Denied):self.b.call('reserve',dict(expected=1,request=str(uuid4())))
        self.assertEqual(self.control.call('inspect',{})['unknown'],1)
    def test_idempotency_changed_intent_and_closed_ticket_cannot_revive(self):
        request=str(uuid4());args=dict(self.binding,request=request,operation=str(uuid4()));receipt=self.a.call('admit',args)
        self.assertTrue(self.a.call('admit',args)['ticket']==receipt['ticket'],'Idempotent receipt differs')
        with self.assertRaises(Denied):self.a.call('admit',dict(args,digest='c'*64))
        self.a.call('first_use',dict(ticket=receipt['ticket'],**self.binding));self.c.rollback();self.a.call('close',dict(ticket=receipt['ticket'],outcome='abort',**self.binding))
        with self.assertRaises(Denied):self.a.call('admit',args)
        with self.assertRaises(Denied):self.a.call('first_use',dict(ticket=receipt['ticket'],**self.binding))
    def test_delayed_receipt_cannot_transfer_to_new_pg_transaction(self):
        receipt=self.admit();self.c.rollback();pid,tx=self.c.execute('SELECT pg_backend_pid(),txid_current()::text').fetchone();self.assertEqual(pid,self.pid);self.assertNotEqual(tx,self.tx)
        with self.assertRaises(Denied):self.a.call('first_use',dict(self.binding,ticket=receipt['ticket'],tx=tx))
        self.assertEqual(self.control.call('inspect',{})['granted'],0)
    def test_checker_cannot_create_or_release_operation(self):
        with self.assertRaises(Denied):self.check.call('admit',dict(self.binding,request=str(uuid4()),operation=str(uuid4())))
        receipt=self.admit()
        with self.assertRaises(Denied):self.check.call('close',dict(ticket=receipt['ticket'],outcome='abort',**self.binding))
        self.assertEqual(self.control.call('inspect',{})['open'],1)
