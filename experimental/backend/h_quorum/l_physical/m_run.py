"""One frozen case/repetition per isolated job, four distinct diagnostic methods."""
import os
import unittest
from h_quorum.common import BANNER
from h_quorum.l_physical.m_triage import CASES,REPETITIONS

METHODS=dict(OFFLINE_OLD_CLEAN='test_offline_old_clean',PROGRESSED_OLD_CLEAN='test_progressed_old_clean',
             PROGRESSED_OLD_KILL='test_progressed_old_kill',PROGRESSED_CURRENT_KILL='test_progressed_current_kill')

if __name__=='__main__':
    case=os.environ['CAC_M_CASE']; repetition=int(os.environ['CAC_M_REPEAT'])
    if set(METHODS)!=set(CASES) or case not in CASES or repetition not in REPETITIONS:
        raise AssertionError('M fixed matrix input mismatch')
    target='h_quorum.l_physical.m_tests.MemberTriageTests.'+METHODS[case]
    suite=unittest.defaultTestLoader.loadTestsFromName(target)
    if suite.countTestCases()!=1:raise AssertionError('M one isolated sample required')
    result=unittest.TextTestRunner(verbosity=2,failfast=True).run(suite)
    if not result.wasSuccessful() or result.skipped:raise SystemExit(1)
    print(BANNER,'M OBSERVATIONAL CASE COMPLETE',case,repetition,'no P1 closure or repair claim',flush=True)
