"""Prove regressions detect broken controls, ONLY on the disposable CI database.

Temporarily installs broken policies/functions, runs a targeted real DB regression,
then restores the exact catalog definition in finally. Never runs in production.
"""
import os
import subprocess
import sys
import psycopg
from psycopg import sql
from tests.test_security import CFG, connect

if os.environ.get('CAC_EXPERIMENTAL_DISPOSABLE') != '1' or CFG['connection']['dbname'] != 'cac_s007_test':
    raise SystemExit('Refusing regression mutation outside disposable database')

with connect('postgres') as c:
    definition=c.execute("SELECT pg_get_functiondef('foundation.verified_context()'::regprocedure)").fetchone()[0]
    check=c.execute("SELECT with_check FROM pg_policies WHERE schemaname='foundation' AND tablename='scoped_grant' AND policyname='grant_insert'").fetchone()[0]

mutations = [
    ('cross-principal grant', 'test_direct_other_principal_grant_denied_and_not_persisted',
     "ALTER POLICY grant_insert ON foundation.scoped_grant WITH CHECK (true)",
     sql.SQL('ALTER POLICY grant_insert ON foundation.scoped_grant WITH CHECK ({})').format(sql.SQL(check))),
    ('mandatory claim validation', 'test_signed_missing_and_null_mandatory_claims',
     """CREATE OR REPLACE FUNCTION foundation.verified_context() RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,cac_private AS $$ SELECT convert_from(decode(split_part(current_setting('cac.context'),'.',1),'hex'),'UTF8')::jsonb $$""",
     definition),
    ('maximum TTL', 'test_maximum_ttl_and_near_boundary_positive',
     definition.replace('+300', '+900'), definition),
]
assert '+300' in definition, 'TTL mutation did not match actual verifier'
for label, test, broken, restore in mutations:
    try:
        with connect('postgres') as c: c.execute(broken)
        run=subprocess.run([sys.executable,'-m','unittest','tests.test_hardening.HardeningTests.'+test,'-v'],capture_output=True,text=True)
        output=run.stdout+run.stderr
        print(output,flush=True)
        assert run.returncode == 1 and 'FAIL:' in output and 'ERROR:' not in output, (label,run.returncode)
        print('EXPECTED RED PASS:',label,'exit=1; assertion detected weakened control',flush=True)
    finally:
        with connect('postgres') as c: c.execute(restore)
print('All mutated controls restored; full suite must run next.',flush=True)
