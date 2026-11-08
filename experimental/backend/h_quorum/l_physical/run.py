"""Real L assertions only; no skip or substitute physical replay claim."""
import unittest
from h_quorum.common import BANNER
from h_quorum.l_physical.tests.test_physical import PhysicalTests

if __name__ == '__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(PhysicalTests)
    if suite.countTestCases()!=7:raise AssertionError('L distinct inventory changed')
    result=unittest.TextTestRunner(verbosity=2,failfast=True).run(suite)
    if not result.wasSuccessful() or result.skipped:raise SystemExit(1)
    print(BANNER,'L PHYSICAL NATIVE OBSERVED_PASS 7 distinct; original majority preserved; no orphan/majority rollback claim',flush=True)
