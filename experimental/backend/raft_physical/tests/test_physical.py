import importlib.util
import unittest
from uuid import uuid4
from h_quorum.broker import Broker
from h_quorum.integration_lab import IntegrationLab
from recovery_fencing.lab import S1


class PhysicalTests(unittest.TestCase):
    def test_00_literal_native_archive_restart(self):
        lab = IntegrationLab()
        self.addCleanup(lab.close)
        lab.reset()
        broker = Broker(lab); broker.activate(0, str(uuid4()))
        with broker.runtime() as gate:
            gate.install(broker.issue(gate.challenge()))
            self.assertEqual(gate.records(), [S1])
        self.assertIsNotNone(importlib.util.find_spec('raft_physical.fixture'),
                             'Literal native Raft archive/reimport fixture is not implemented')
