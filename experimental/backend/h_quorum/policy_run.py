"""K-specific real tests; inherited H51 remains a separate unchanged suite."""
import unittest
from h_quorum.common import BANNER
from h_quorum.tests.test_policy_retirement import PolicyRetirementTests

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PolicyRetirementTests)
    if suite.countTestCases() != 17: raise AssertionError('K distinct inventory changed')
    result = unittest.TextTestRunner(verbosity=2, failfast=True).run(suite)
    if not result.wasSuccessful() or result.skipped: raise SystemExit(1)
    print(BANNER, 'K POLICY RETIREMENT OBSERVED_PASS 17 distinct; no skips; no majority rollback/orphan recovery claim', flush=True)
