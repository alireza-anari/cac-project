"""Deliberate weakening in disposable DB only; demand assertion RED, restore exact SQL."""
import os
import subprocess
import sys
from context_poc.harness import CFG,connect
assert os.environ.get('CAC_EXPERIMENTAL_DISPOSABLE')=='1' and CFG['connection']['dbname']=='cac_s007_test'
mutations=[
 ('poc.verify()', "c->>'tx'<>txid_current()::text", 'false', 'test_pool.PoolTests.test_backend_reuse_commit_rollback_and_session_set'),
 ('poc.verify()', "s.mfa<clock_timestamp()-interval '5 minutes'", 'false', 'test_timing.TimingTests.test_exact_mfa_freshness_after_token_issuance'),
 ('poc.issue(text,text,uuid,text,uuid,jsonb)', 'now_s-(h->>\'started\')::numeric NOT BETWEEN 0 AND 5', 'false', 'test_timing.TimingTests.test_exact_challenge_start_plus_five_and_clock_skew'),
]
for name,old,new,test in mutations:
    with connect('postgres') as c: original=c.execute('SELECT pg_get_functiondef(%s::regprocedure)',(name,)).fetchone()[0]
    assert old in original
    try:
        with connect('postgres') as c:c.execute(original.replace(old,new))
        r=subprocess.run([sys.executable,'-m','unittest',test,'-v'],env=dict(os.environ,PYTHONPATH='.:pool_recovery/tests'),capture_output=True,text=True,timeout=30)
        print(r.stdout+r.stderr,flush=True)
        assert r.returncode==1 and 'FAIL:' in r.stderr and 'ERROR:' not in r.stderr, test
        print('S009B EXPECTED RED',test,'exit1 assertion failure',flush=True)
    finally:
        with connect('postgres') as c:c.execute(original)
print('S009B SQL restored exactly; full green required',flush=True)

# A separate observer-control RED: prime an empty pg_stat_activity snapshot,
# then deliberately keep the observer in one transaction. No SQL control changes.
script = r'''
from pathlib import Path
import unittest
source=Path('pool_recovery/tests/test_pool.py').read_text()
old='observer.autocommit=True  # fresh activity snapshot per polling statement'
assert source.count(old)==1
namespace={'__name__':'snapshot_mutation'}
exec(compile(source.replace(old,'observer.autocommit=False'),'<snapshot-mutation>','exec'),namespace)
suite=unittest.TestSuite([namespace['PoolTests']('test_issuance_racing_principal_revoke_has_no_revived_authority')])
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
'''
r=subprocess.run([sys.executable,'-c',script],capture_output=True,text=True,timeout=20)
print(r.stdout+r.stderr,flush=True)
assert r.returncode==1 and 'FAIL:' in r.stderr and 'ERROR:' not in r.stderr and 'missing issuance/revoke race witness' in r.stderr
print('S009B OBSERVER EXPECTED RED: cached activity snapshot is detected; source unchanged',flush=True)
