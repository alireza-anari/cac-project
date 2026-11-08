"""One original assertion after literal native input; parent-owned restoration."""
import hashlib
from pathlib import Path
from h_quorum.authority import Root
from h_quorum.common import BANNER,config
from h_quorum.sensitivity import execute,restart_current

TARGET='h_quorum.l_physical.tests.test_physical.PhysicalTests.test_05_physical_replay_cannot_authorize_retirement_coordinator'

def main():
    original_probe=execute(['unittest','-v',TARGET])
    if original_probe.returncode or 'L LITERAL NATIVE CATCHUP' not in original_probe.stdout:
        raise AssertionError('Healthy original physical probe failed')
    path=Path(__file__).parents[1]/'retirement.py'; original=path.read_bytes()
    needle=b"if record['kind'] != 'control':raise Denied('denied')"
    if original.count(needle)!=1:raise AssertionError('Ambiguous L authority mutation')
    try:
        path.write_bytes(original.replace(needle,b"if False:raise Denied('denied') # intentional L test-only mutant"))
        mutant=execute(['unittest','-v',TARGET])
    finally:
        path.write_bytes(original)
        if path.read_bytes()!=original:raise AssertionError('L source restoration mismatch')
        cfg=config(); retained=Root(cfg).read(cfg['app_namespace'])
        restart_current()
        if Root(config()).read(cfg['app_namespace'])!=retained:raise AssertionError('L source restoration rolled back R')
        print(BANNER,'L EXACT SOURCE RESTORED',hashlib.sha256(original).hexdigest(),
              'R retained policy',retained[0]['policy'],'revision',retained[1],flush=True)
    combined=mutant.stdout+mutant.stderr
    if (mutant.returncode!=1 or 'FAILED (failures=1)' not in combined or 'ERROR:' in combined
        or 'Physical replay accepted non-control policy retirement' not in combined
        or 'UNSAFE L PHYSICAL AUTHORITY WITNESS native import completed then coordinator committed policy2' not in combined
        or 'L EXACT NATIVE BYTES REIMPORTED before spawn' not in combined
        or 'L LITERAL NATIVE CATCHUP' not in combined):
        raise AssertionError('L original reasons-specific physical mutation RED not demonstrated')
    print(BANNER,'L EXPECTED_MUTATION_RED actual native replay then unauthorized policy commit',flush=True)
    green=execute(['unittest','-v',TARGET])
    if green.returncode or 'L LITERAL NATIVE CATCHUP' not in green.stdout:raise AssertionError('L original restored probe not GREEN')
    print(BANNER,'L RESTORED SAME ORIGINAL GREEN; fresh synthetic namespace, original R history retained',flush=True)

if __name__=='__main__':main()
