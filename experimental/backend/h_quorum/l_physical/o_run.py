"""Exactly one frozen O observation in this disposable CI job."""
import os
import unittest
from h_quorum.common import BANNER

METHODS = {
    'O_REMOVE_ACK_THEN_STOP_OPEN': 'test_remove_ack_then_stop_open',
    'O_LEARNER_ADDED_THEN_STOP_UNKNOWN': 'test_learner_added_then_stop_unknown',
    'O_PROMOTE_ACK_LOSS_UNKNOWN': 'test_promote_ack_loss_unknown',
}

if __name__ == '__main__':
    case = os.environ['CAC_O_CASE']
    if case not in METHODS:
        raise RuntimeError('O frozen case mismatch')
    target = 'h_quorum.l_physical.o_tests.InterruptedRepairTests.' + METHODS[case]
    suite = unittest.defaultTestLoader.loadTestsFromName(target)
    if suite.countTestCases() != 1:
        raise RuntimeError('O exactly one observation required')
    result = unittest.TextTestRunner(verbosity=2, failfast=True).run(suite)
    if not result.wasSuccessful() or result.skipped:
        raise SystemExit(1)
    print(BANNER, 'O_INTERRUPTED_REPAIR_BOUNDED_PASS', case, flush=True)
