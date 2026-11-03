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
