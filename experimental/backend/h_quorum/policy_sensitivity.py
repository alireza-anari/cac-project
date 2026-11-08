"""K authority sensitivity: actual committed mutant; parent-owned byte restoration."""
import hashlib
from pathlib import Path
from h_quorum.authority import Root
from h_quorum.common import BANNER, config
from h_quorum.sensitivity import execute, restart_current

TARGET = 'h_quorum.tests.test_policy_retirement.PolicyRetirementTests.test_02_policy_retirement_requires_control'


def main():
    print(BANNER, 'K AUTHORITY HEALTHY ORIGINAL PROBE', flush=True)
    baseline = execute(['unittest', '-v', TARGET])
    if baseline.returncode or 'Ran 1 test' not in baseline.stderr:
        raise AssertionError('K authority sensitivity baseline is not healthy')
    path = Path(__file__).with_name('retirement.py')
    original = path.read_bytes()
    needle = b"if record['kind'] != 'control':raise Denied('denied')"
    if original.count(needle) != 1:
        raise AssertionError('Ambiguous policy authority mutation')
    retained = None
    try:
        path.write_bytes(original.replace(needle, b"if False:raise Denied('denied') # deliberate test-only authority mutant"))
        mutant = execute(['unittest', '-v', TARGET])
    finally:
        path.write_bytes(original)
        if path.read_bytes() != original:
            raise AssertionError('Policy authority source restoration failed')
        cfg = config(); namespace = cfg['app_namespace']
        retained = Root(cfg).read(namespace)
        restart_current()
        if Root(config()).read(namespace) != retained:
            raise AssertionError('Restoration changed real committed R state')
        print(BANNER, 'K EXACT SOURCE RESTORED sha256', hashlib.sha256(original).hexdigest(),
              'committed mutant namespace retained at policy', retained[0]['policy'],
              'revision', retained[1], 'no R rollback', flush=True)
    combined = mutant.stdout + mutant.stderr
    if (mutant.returncode != 1 or 'FAILED (failures=1)' not in combined
        or 'Policy retirement accepted a non-control role' not in combined
        or 'UNSAFE K POLICY AUTHORITY WITNESS coordinator committed policy2' not in combined
        or 'ERROR:' in combined):
        raise AssertionError('K reason-specific original assertion RED was not demonstrated')
    print(BANNER, 'K EXPECTED_MUTATION_RED actual unprivileged policy2 commit', flush=True)
    green = execute(['unittest', '-v', TARGET])
    if green.returncode or 'Ran 1 test' not in green.stderr:
        raise AssertionError('K identical original probe did not restore GREEN')
    print(BANNER, 'K RESTORED SAME ORIGINAL PROBE GREEN; separate fresh synthetic test namespace, earlier R history retained', flush=True)


if __name__ == '__main__': main()
