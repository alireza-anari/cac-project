"""One fixed real-route observation in a disposable current-majority fixture."""
import os
import unittest
from h_quorum.common import BANNER

METHODS = {
    'P_STALE_ISSUER_POLICY_AFTER_RETIREMENT': 'test_stale_issuer_policy_after_retirement',
    'P_DIRECT_SQL_OLD_PRINCIPAL': 'test_direct_sql_old_principal',
    'P_POOL_REUSED_BACKEND_OLD_CONTEXT': 'test_pool_reused_backend_old_context',
}

if __name__ == '__main__':
    case = os.environ['CAC_P_CASE']
    if case not in METHODS:
        raise RuntimeError('P fixed route matrix mismatch')
    suite = unittest.defaultTestLoader.loadTestsFromName(
        'h_quorum.p_tests.LegacyRouteAuditTests.' + METHODS[case])
    if suite.countTestCases() != 1:
        raise RuntimeError('P exactly one original observation required')
    result = unittest.TextTestRunner(verbosity=2, failfast=True).run(suite)
    if not result.wasSuccessful() or result.skipped:
        raise SystemExit(1)
    print(BANNER, 'P ONE ORIGINAL ROUTE OBSERVATION COMPLETE', case, flush=True)
