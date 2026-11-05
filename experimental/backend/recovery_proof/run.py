"""Phase 1: unchanged security assertions under independent real SQL mutations."""
import unittest

from recovery_fencing.lab import require
from recovery_fencing.run import suite as retained_c_suite
from recovery_proof.tests.test_sensitivity_targets import SecurityTargets

CONTROLS = [
    ('cas', 'test_stale_expected_epoch_cannot_reserve', 'FenceDenied not raised'),
    ('sql_fence', 'test_sql_online_guard_requires_live_ticket', 'InsufficientPrivilege not raised'),
    ('open', 'test_orphan_open_blocks_reservation', 'FenceDenied not raised'),
]


def run_tests(method=None, mutation=None):
    if method:
        case = SecurityTargets(method)
        case.mutation = mutation
        tests = unittest.TestSuite([case])
    else:
        tests = unittest.defaultTestLoader.loadTestsFromTestCase(SecurityTargets)
        assert tests.countTestCases() == 3
    return unittest.TextTestRunner(verbosity=2).run(tests)


def green(result):
    assert result.wasSuccessful() and not result.skipped, 'GREEN gate failed'


if __name__ == '__main__':
    require()
    green(run_tests())
    print('S009D BASELINE GREEN 3 distinct probes; no skips', flush=True)
    for kind, method, expected in CONTROLS:
        result = run_tests(method, kind)
        assert result.testsRun == 1 and len(result.failures) == 1
        assert not result.errors and not result.skipped and not result.unexpectedSuccesses
        assert expected in result.failures[0][1], 'RED was not the intended missing denial'
        print('S009D EXPECTED RED', kind, method, 'one assertion failure; zero errors/skips', flush=True)
        green(run_tests(method))
        print('S009D RESTORED GREEN', kind, flush=True)
    green(run_tests())
    retained_c_suite()
    print('S009D PHASE1 COMPLETE 3 independent SQL mutation receipts; restored probes + retained C20 GREEN', flush=True)
