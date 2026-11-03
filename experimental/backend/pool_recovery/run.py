"""CI entrypoint. No test may skip; inherited suites are run by parent workflow."""
import os
import subprocess
import sys
import unittest
from pathlib import Path
from context_poc.harness import CFG, connect

def suite():
    tests=unittest.defaultTestLoader.discover('pool_recovery/tests','test_*.py')
    count=tests.countTestCases()
    assert count==26, ('Unexpected S009B test inventory',count)
    result=unittest.TextTestRunner(verbosity=2).run(tests)
    if not result.wasSuccessful() or result.skipped: raise SystemExit(1)
    print('S009B SUITE PASS',count,'distinct tests; no skip',flush=True)

assert os.geteuid()==0 and os.environ.get('CAC_EXPERIMENTAL_DISPOSABLE')=='1'
assert CFG['connection']['dbname']=='cac_s007_test'
with connect('postgres') as c:
    print(c.execute('SELECT version()').fetchone()[0],flush=True)
    rows=c.execute("SELECT n.nspname,p.proname,p.prosecdef,p.proconfig,pg_get_userbyid(p.proowner),p.proacl::text FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname IN ('poc','poc_private') ORDER BY 1,2").fetchall()
    assert all(r[2] and r[3]==['search_path=pg_catalog, poc_private'] and r[4]=='cac_ctx_guard' for r in rows)
    print('FUNCTION/ROLE INVENTORY',rows,flush=True)
suite()
subprocess.run([sys.executable,'-m','pool_recovery.sensitivity'],check=True)
subprocess.run([sys.executable,'-m','context_poc.roundtrip'],check=True)
suite()
print('S009B COMPLETE; inherited 43+24 floor handled separately by unchanged parent steps',flush=True)
