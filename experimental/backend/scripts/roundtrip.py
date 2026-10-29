"""Destructive rollback proof, ONLY on bootstrap's explicitly disposable DB."""
import json
import os
from pathlib import Path
import subprocess
import sys
import psycopg
cfg=json.loads(Path(os.environ['CAC_TEST_CONFIG']).read_text())
if os.environ.get('CAC_EXPERIMENTAL_DISPOSABLE')!='1' or cfg['connection']['dbname']!='cac_s007_test':
    raise SystemExit('Refusing non-disposable migration rollback')
def snapshot():
    with psycopg.connect(**cfg['connection'],user='postgres',password=cfg['passwords']['postgres']) as c:
        queries={
          'columns':"SELECT table_name,column_name,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='foundation' AND table_name<>'django_migrations' ORDER BY 1,2",
          'constraints':"SELECT r.relname,c.conname,pg_get_constraintdef(c.oid) FROM pg_constraint c JOIN pg_class r ON r.oid=c.conrelid WHERE r.relnamespace='foundation'::regnamespace AND r.relname<>'django_migrations' ORDER BY 1,2",
          'policies':"SELECT tablename,policyname,roles,cmd,qual,with_check FROM pg_policies WHERE schemaname='foundation' ORDER BY 1,2",
          'rls_acl':"SELECT relname,relrowsecurity,relforcerowsecurity,relacl::text,pg_get_userbyid(relowner) FROM pg_class WHERE relnamespace='foundation'::regnamespace AND relkind='r' AND relname<>'django_migrations' ORDER BY 1",
          'functions':"SELECT proname,pg_get_functiondef(oid),proacl::text FROM pg_proc WHERE pronamespace='foundation'::regnamespace ORDER BY 1",
        }
        return {k:c.execute(v).fetchall() for k,v in queries.items()}
before=snapshot()
subprocess.run([sys.executable,'manage.py','migrate','foundation','zero','--noinput'],check=True)
with psycopg.connect(**cfg['connection'],user='postgres',password=cfg['passwords']['postgres']) as c:
    assert c.execute("SELECT count(*) FROM pg_tables WHERE schemaname='foundation' AND tablename<>'django_migrations'").fetchone()==(0,)
    assert c.execute("SELECT count(*) FROM pg_proc WHERE pronamespace='foundation'::regnamespace").fetchone()==(0,)
subprocess.run([sys.executable,'manage.py','migrate','--noinput'],check=True)
after=snapshot()
assert before==after,'Schema/RLS/ACL differs after rollback and reapply'
print('ROUNDTRIP PASS: tables, columns, constraints, policies, owner, ACL and functions match; rollback removed experimental tables/functions.')
Path(os.environ['CAC_EVIDENCE_DIR'],'schema-snapshot.json').write_text(json.dumps(after,indent=2,default=str)+'\n')
