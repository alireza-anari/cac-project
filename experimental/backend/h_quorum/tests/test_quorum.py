"""Q_SURVIVAL_ONLY. Real root concurrency/outage/learner current-history probes."""
from concurrent.futures import ThreadPoolExecutor
import json
import time
import unittest
from uuid import uuid4
from h_quorum.common import config,Denied,BANNER
from h_quorum.cluster import Cluster
from h_quorum.etcd import Etcd,unb64
from h_quorum.rpc import Client

class QuorumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cfg=config();cls.q=Cluster()
    def setUp(self):
        self.ns=str(uuid4());self.control=Client(self.cfg,'control',self.ns)
        self.control.call('genesis',dict(actors={n:dict(sid='synthetic-'+n,incarnation=str(uuid4()),manifest='a'*64,admitted=True) for n in ('A','B')}))
    def reserve(self,node,expected=0):return Client(self.cfg,node+'_coord',self.ns).call('reserve',dict(expected=expected,request=str(uuid4())))
    def test_two_contenders_cas_one_committed_epoch(self):
        def attempt(node):
            try:return self.reserve(node)['epoch']
            except Denied:return 'DENIED'
        with ThreadPoolExecutor(2) as executor:result=list(executor.map(attempt,['A','B']))
        self.assertCountEqual(result,[1,'DENIED'])
        state=self.control.call('inspect',{})
        self.assertEqual(state['seq'],1);self.assertEqual(state['state_revision'],state['journal_revision'])
        print(BANNER,'CAS contenders one epoch committed; revision',state['state_revision'],flush=True)
    def test_minority_loss_retains_current_majority_progress(self):
        before=self.q.snapshot('before-minority-stop');self.q.stop(['r4','r5'])
        try:
            self.assertEqual(self.reserve('A')['epoch'],1)
            self.assertEqual(Client(self.cfg,'A_check',self.ns).call('status')['epoch'],1)
            print(BANNER,'three original current survivors committed epoch; IDs',{n:before['members'][n]['id'] for n in ('r1','r2','r3')},flush=True)
        finally:
            for name in ('r4','r5'):self.q.start(name)
    def test_quorum_loss_denies_reads_and_commands_then_current_recovery(self):
        self.assertEqual(self.reserve('A')['epoch'],1)
        self.q.stop(['r3','r4','r5'])
        try:
            with self.assertRaises(Denied):Client(self.cfg,'A_check',self.ns).call('status')
            with self.assertRaises(Denied):self.reserve('B',1)
        finally:
            for name in ('r3','r4','r5'):self.q.start(name)
        recovered=Client(self.cfg,'A_check',self.ns).call('status')
        self.assertEqual(recovered['phase'],'RESERVED')
        self.assertIn(recovered['epoch'],(1,2)) # A timed-out mutation may have committed: never infer ABORT.
        print(BANNER,'actual quorum outage denied current read + command; current data restart preserved epoch',flush=True)
    def test_replacement_is_fresh_learner_then_verified_catchup_then_explicit_vote(self):
        before=self.q.snapshot('before-replacement');self.assertEqual(self.reserve('A')['epoch'],1)
        inspector=self.control.call('inspect',{})
        for name in ('r4','r5'):
            fresh=self.q.replace(name);phase=self.q.snapshot('learner-'+name)
            self.assertNotEqual(fresh,before['members'][name]['id']);self.assertTrue(phase['members'][name]['isLearner'])
            self.assertEqual(sum(not m['isLearner'] for m in phase['members'].values() if m['admitted']),4)
            for survivor in ('r1','r2','r3'):self.assertEqual(phase['members'][survivor]['id'],before['members'][survivor]['id'])
            endpoint=self.q.cfg['members'][name]['endpoint'];client=Etcd(self.q.cfg)
            # Authenticate is a Raft proposal and forbidden on learners. Mint a
            # fresh token at a surviving voter AFTER learner start, then observe
            # its actual replicated auth entry and serializable local data.
            client._authenticate(self.q.cfg['members']['r1']['endpoint'])
            with self.assertRaises(Denied):client.range('/cac-h/'+self.ns+'/state',endpoint=endpoint)
            deadline=time.monotonic()+15
            while True:
                local=client.range('/cac-h/'+self.ns+'/state',serializable=True,endpoint=endpoint)
                if local.get('kvs') and json.loads(unb64(local['kvs'][0]['value']))['head']==inspector['head']:break
                if time.monotonic()>deadline:self.fail('Learner did not catch up current root state')
                time.sleep(.1)
            revision=int(local['kvs'][0]['mod_revision'])
            history=client.range('/cac-h/'+self.ns+'/journal/',prefix=True,revision=revision,serializable=True,endpoint=endpoint)
            self.assertEqual(len(history.get('kvs',[])),2)
            self.assertEqual(int(history['kvs'][-1]['mod_revision']),revision)
            self.q.promote(name);after=self.q.snapshot('promoted-'+name)
            self.assertTrue(all(not m['isLearner'] for m in after['members'].values()))
            self.assertEqual(len(after['members']),5)
            print(BANNER,'REAL recovery',json.dumps(dict(learner=phase,promoted=after,state_revision=revision,journal_head=inspector['head'])),flush=True)
        self.assertEqual(self.control.call('inspect',{})['head'],inspector['head'])
