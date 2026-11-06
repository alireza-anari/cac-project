"""Q_SURVIVAL_ONLY. Actual R signed transcript; no mandatory SQL claim yet."""
import secrets
from uuid import uuid4
from h_quorum.common import Denied,BANNER
from h_quorum.rpc import Client
from h_quorum.tests.test_lifecycle import LifecycleFixture

class GuardTests(LifecycleFixture):
    def granted(self):
        receipt=self.admit();self.a.call('first_use',dict(ticket=receipt['ticket'],**self.binding));return receipt
    def challenge(self,receipt):return dict(self.binding,ticket=receipt['ticket'],root_id=self.cfg['root_id'],epoch=1,nonce=secrets.token_hex(32),mode='guard')
    def proof(self,args):return self.check.call('guard',args)['answer']
    def verify(self,args,answer):return self.check.call('verify',dict(args,answer=answer))['valid']
    def test_00_live_signed_guard_and_online_reverification(self):
        receipt=self.granted();args=self.challenge(receipt)
        try:answer=self.proof(args)
        except Denied:self.fail('Live root signed guard is not implemented')
        self.assertTrue(self.verify(args,answer));print(BANNER,'live signed R transcript and current online revalidation; no SQL enforcement claim',flush=True)
    def test_ungranted_or_missing_open_cannot_attest(self):
        receipt=self.admit();args=self.challenge(receipt)
        with self.assertRaises(Denied):self.proof(args)
        self.a.call('first_use',dict(ticket=receipt['ticket'],**self.binding));self.assertTrue(self.verify(args,self.proof(args)))
        with self.assertRaises(Denied):self.proof(dict(args,ticket='synthetic-unknown-ticket'))
    def test_nonce_and_new_transaction_replay_are_denied(self):
        receipt=self.granted();args=self.challenge(receipt);answer=self.proof(args);self.assertTrue(self.verify(args,answer))
        with self.assertRaises(Denied):self.verify(dict(args,nonce=secrets.token_hex(32)),answer)
        self.c.rollback();pid,tx=self.c.execute('SELECT pg_backend_pid(),txid_current()::text').fetchone();self.assertEqual(pid,self.pid);self.assertNotEqual(tx,self.tx)
        with self.assertRaises(Denied):self.proof(dict(args,tx=tx))
        with self.assertRaises(Denied):self.verify(dict(args,tx=tx),answer)
    def test_authenticated_node_and_root_actor_policy_bindings(self):
        args=self.challenge(self.granted());self.assertTrue(self.verify(args,self.proof(args)))
        with self.assertRaises(Denied):Client(self.cfg,'B_check',self.ns).call('guard',args)
        for field,value in [('sid','synthetic-other-sid'),('root_id',str(uuid4())),('incarnation',str(uuid4())),('policy',0),('policy',True),('manifest','c'*64),('epoch',0),('epoch',True),('login','cac_ctx_issuer')]:
            with self.subTest(field=field,value=value):
                with self.assertRaises(Denied):self.proof(dict(args,**{field:value}))
    def test_closed_operation_invalidates_previously_signed_proof(self):
        receipt=self.granted();args=self.challenge(receipt);answer=self.proof(args);self.assertTrue(self.verify(args,answer));self.c.commit()
        self.a.call('close',dict(self.binding,ticket=receipt['ticket'],outcome='commit'))
        with self.assertRaises(Denied):self.verify(args,answer)
        with self.assertRaises(Denied):self.proof(args)
    def test_grant_before_revoke_stays_bound_and_successor_waits(self):
        args=self.challenge(self.granted());answer=self.proof(args);self.b.call('revoke',dict(expected=1))
        self.assertTrue(self.verify(args,answer));fresh=dict(args,nonce=secrets.token_hex(32));self.assertTrue(self.verify(fresh,self.proof(fresh)))
        with self.assertRaises(Denied):self.b.call('reserve',dict(expected=1,request=str(uuid4())))
    def test_retired_signer_denied_and_current_signer_works(self):
        args=self.challenge(self.granted());answer=self.proof(args);self.assertTrue(self.verify(args,answer))
        self.control.call('retire_signer',dict(expected=1,new=2))
        with self.assertRaises(Denied):self.verify(args,answer)
        fresh=dict(args,nonce=secrets.token_hex(32));self.assertTrue(self.verify(fresh,self.proof(fresh)))
        with self.assertRaises(Denied):self.check.call('retire_signer',dict(expected=2,new=1))
    def test_unknown_invalidates_proof_without_releasing_hold(self):
        receipt=self.granted();args=self.challenge(receipt);answer=self.proof(args);self.a.call('unknown',dict(self.binding,ticket=receipt['ticket']))
        with self.assertRaises(Denied):self.proof(args)
        with self.assertRaises(Denied):self.verify(args,answer)
        self.b.call('revoke',dict(expected=1))
        with self.assertRaises(Denied):self.b.call('reserve',dict(expected=1,request=str(uuid4())))
        self.assertEqual(self.control.call('inspect',{})['unknown'],1)
