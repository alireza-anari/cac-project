"""S0-09K: actual policy retirement; current non-restored quorum required."""
import unittest
from uuid import uuid4
from h_quorum.authority import Root
from h_quorum.broker import Broker
from h_quorum.common import BANNER, Denied
from h_quorum.integration_lab import IntegrationLab
from h_quorum.rpc import Client
from recovery_fencing.lab import S1


class PolicyRetirementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.lab = IntegrationLab()
    @classmethod
    def tearDownClass(cls): cls.lab.close()

    def setUp(self):
        self.lab.reset()
        self.a = Broker(self.lab)
        self.a.activate(0, str(uuid4()))
        self.control = Client(self.lab.rootcfg, 'control', self.lab.namespace)

    def state(self):
        return Root(self.lab.rootcfg).read(self.lab.namespace, True)

    def scope(self, gate, broker=None, action='read', body=None):
        broker = broker or self.a
        gate.install(broker.issue(gate.challenge(), action=action, body=body or {}))
        self.assertEqual(gate.records(), [S1])

    def retire(self, request=None):
        args = dict(expected=1, new=2, request=request or str(uuid4()))
        try:
            result = self.control.call('retire_policy', args)
        except Denied:
            self.fail('Actual Root policy retirement transaction is not implemented')
        self.lab.replay()
        return result, args

    def test_00_real_policy_transition_is_atomic_not_signer_rotation(self):
        self.lab.r_evidence('K healthy current policy1')
        with self.a.runtime() as gate:
            self.scope(gate)
        before, _, _ = self.state()
        self.assertEqual((before['policy'], before['signer_epoch']), (1, 1))
        receipt, args = self.retire()
        after, revision, rows = self.state()
        self.assertEqual((after['policy'], after['signer_epoch']), (2, 1))
        self.assertEqual(after['ops'], before['ops'])
        self.assertEqual(after['seq'], before['seq'] + 1)
        self.assertEqual(receipt['revision'], revision)
        self.assertEqual(int(rows[-1]['mod_revision']), revision)
        from h_quorum.common import unb64
        import json
        entry = json.loads(unb64(rows[-1]['value']))
        self.assertEqual(entry['command']['action'], 'retire_policy')
        self.assertEqual(entry['command']['request'], args['request'])
        self.lab.r_evidence('K policy2 majority-committed with unchanged signer')
        print(BANNER, 'K REAL POLICY RETIREMENT', receipt,
              'same signer; full operation state preserved; one journal/state MVCC', flush=True)
