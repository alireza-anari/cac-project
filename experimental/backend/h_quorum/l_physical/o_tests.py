"""Three frozen O observations; no replay or outcome-driven repetitions."""
import importlib.util
import os
import unittest


class InterruptedRepairTests(unittest.TestCase):
    def run_case(self, case):
        self.assertIsNotNone(
            importlib.util.find_spec('h_quorum.l_physical.o_triage'),
            'O interruption controller and observer are not implemented',
        )
        self.assertEqual(os.environ['CAC_O_CASE'], case)
        from h_quorum.l_physical.o_triage import run_sample
        run_sample(self, case)

    def test_remove_ack_then_stop_open(self):
        self.run_case('O_REMOVE_ACK_THEN_STOP_OPEN')

    def test_learner_added_then_stop_unknown(self):
        self.run_case('O_LEARNER_ADDED_THEN_STOP_UNKNOWN')

    def test_promote_ack_loss_unknown(self):
        self.run_case('O_PROMOTE_ACK_LOSS_UNKNOWN')
