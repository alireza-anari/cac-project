"""One frozen S0-09N case/repetition per isolated disposable job."""
import os
import unittest

from h_quorum.common import BANNER

METHODS = {
    "N_PROGRESS_OLD_CLEAN_OPEN": "test_progressed_old_clean_open_survives_fresh_id_repair",
    "N_PROGRESS_OLD_KILL_UNKNOWN": "test_progressed_old_kill_unknown_survives_fresh_id_repair",
}
REPETITIONS = (1, 2)


if __name__ == "__main__":
    case = os.environ["CAC_N_CASE"]
    repetition = int(os.environ["CAC_N_REPEAT"])
    if case not in METHODS or repetition not in REPETITIONS:
        raise AssertionError("N fixed matrix input mismatch")
    target = "h_quorum.l_physical.n_tests.FreshIdentityRepairTests." + METHODS[case]
    suite = unittest.defaultTestLoader.loadTestsFromName(target)
    if suite.countTestCases() != 1:
        raise AssertionError("N requires exactly one isolated sample")
    result = unittest.TextTestRunner(verbosity=2, failfast=True).run(suite)
    if not result.wasSuccessful() or result.skipped:
        raise SystemExit(1)
    print(BANNER, "N FRESH-IDENTITY REPAIR SAMPLE COMPLETE", case, repetition, flush=True)
