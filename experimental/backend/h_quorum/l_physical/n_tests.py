"""S0-09N: qualify fresh-ID learner repair after the exact native M fail-stop."""
import importlib.util
import os
import unittest
from uuid import uuid4

from h_quorum.broker import Broker
from h_quorum.integration_lab import IntegrationLab
from recovery_fencing.lab import S1


class FreshIdentityRepairTests(unittest.TestCase):
    def run_case(self, case):
        lab = IntegrationLab()
        self.addCleanup(lab.close)
        lab.reset()
        broker = Broker(lab)
        broker.activate(0, str(uuid4()))
        self.assertIsNotNone(
            importlib.util.find_spec("h_quorum.l_physical.n_triage"),
            "S0-09N fresh-identity repair qualification is not implemented",
        )
        self.assertEqual(os.environ["CAC_N_CASE"], case)
        from h_quorum.l_physical.n_triage import run_sample
        run_sample(self, lab, broker, case, int(os.environ["CAC_N_REPEAT"]))

    def test_progressed_old_clean_open_survives_fresh_id_repair(self):
        self.run_case("N_PROGRESS_OLD_CLEAN_OPEN")

    def test_progressed_old_kill_unknown_survives_fresh_id_repair(self):
        self.run_case("N_PROGRESS_OLD_KILL_UNKNOWN")
