"""Q_SURVIVAL_ONLY. Stop on first real failure, no skips masked as proof."""
import unittest
from h_quorum.common import BANNER
if __name__=='__main__':
    print(BANNER,flush=True)
    # Transport preflight must precede intentional topology faults.
    from h_quorum.tests.test_root import RootTests
    from h_quorum.tests.test_quorum import QuorumTests
    from h_quorum.tests.test_transport import TransportTests
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case) for case in (RootTests,QuorumTests,TransportTests))
    count=suite.countTestCases()
    result=unittest.TextTestRunner(verbosity=2,failfast=True).run(suite)
    if not result.wasSuccessful() or result.skipped:raise SystemExit(1)
    print(BANNER,'H ROOT PREFLIGHT OBSERVED_PASS',count,'distinct; no skips; remaining H scope NOT_RUN',flush=True)
