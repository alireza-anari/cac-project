"""S0-09M finite real diagnostic cases; no security-control mutation."""
import importlib.util
import unittest
from uuid import uuid4
from h_quorum.broker import Broker
from h_quorum.integration_lab import IntegrationLab
from recovery_fencing.lab import S1


class MemberTriageTests(unittest.TestCase):
    def run_case(self,case):
        lab=IntegrationLab(); self.addCleanup(lab.close); lab.reset()
        broker=Broker(lab); broker.activate(0,str(uuid4()))
        with broker.runtime() as gate:
            gate.install(broker.issue(gate.challenge()))
            self.assertEqual(gate.records(),[S1])
        self.assertIsNotNone(importlib.util.find_spec('h_quorum.l_physical.m_triage'),
                             'Fixed native member availability diagnostic is not implemented')
        from h_quorum.l_physical.m_triage import run_sample
        import os
        self.assertEqual(os.environ['CAC_M_CASE'],case)
        run_sample(self,lab,broker,case,int(os.environ['CAC_M_REPEAT']))

    def test_offline_old_clean(self):self.run_case('OFFLINE_OLD_CLEAN')
    def test_progressed_old_clean(self):self.run_case('PROGRESSED_OLD_CLEAN')
    def test_progressed_old_kill(self):self.run_case('PROGRESSED_OLD_KILL')
    def test_progressed_current_kill(self):self.run_case('PROGRESSED_CURRENT_KILL')
