"""W_ORACLE_ASSUMED. Actual CI result only; unimplemented feature is a RED build."""
import unittest
from w_oracle.lab import BANNER

if __name__ == '__main__':
    print(BANNER, flush=True)
    tests = unittest.defaultTestLoader.discover('w_oracle/tests', 'test_*.py')
    result = unittest.TextTestRunner(verbosity=2, failfast=True).run(tests)
    if not result.wasSuccessful() or result.skipped:
        raise SystemExit(1)
    print(BANNER, 'ORACLE CONTRACT PASS', tests.countTestCases(), flush=True)
