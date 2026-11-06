"""Q_SURVIVAL_ONLY. Stop on first real failure, no skips masked as proof."""
import unittest
from h_quorum.common import BANNER
if __name__=='__main__':
    print(BANNER,flush=True)
    suite=unittest.defaultTestLoader.discover('h_quorum/tests','test_*.py')
    count=suite.countTestCases()
    result=unittest.TextTestRunner(verbosity=2,failfast=True).run(suite)
    if not result.wasSuccessful() or result.skipped:raise SystemExit(1)
    print(BANNER,'H SUITE OBSERVED_PASS',count,'distinct; no skips',flush=True)
