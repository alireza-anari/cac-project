import json
import os
import subprocess
import sys
from pathlib import Path
from context_poc.harness import connect

def snapshot():
    with connect('postgres') as c:
        return {
            'columns':c.execute("SELECT table_schema,table_name,column_name,data_type,is_nullable FROM information_schema.columns WHERE table_schema IN ('poc','poc_private') ORDER BY 1,2,3").fetchall(),
            'constraints':c.execute("SELECT n.nspname,r.relname,c.conname,pg_get_constraintdef(c.oid) FROM pg_constraint c JOIN pg_class r ON r.oid=c.conrelid JOIN pg_namespace n ON n.oid=r.relnamespace WHERE n.nspname IN ('poc','poc_private') ORDER BY 1,2,3").fetchall(),
            'functions':c.execute("SELECT n.nspname,p.proname,pg_get_functiondef(p.oid),p.proacl::text,pg_get_userbyid(p.proowner) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname IN ('poc','poc_private') ORDER BY 1,2").fetchall(),
            'rls':c.execute("SELECT relname,relrowsecurity,relforcerowsecurity,relacl::text,pg_get_userbyid(relowner) FROM pg_class WHERE relnamespace IN ('poc'::regnamespace,'poc_private'::regnamespace) AND relkind='r' ORDER BY relname").fetchall(),
            'policies':c.execute("SELECT tablename,policyname,roles,cmd,qual,with_check FROM pg_policies WHERE schemaname='poc' ORDER BY 1,2").fetchall()}
before=snapshot()
subprocess.run([sys.executable,'-m','context_poc.migrate','down'],check=True)
with connect('postgres') as c:assert c.execute("SELECT count(*) FROM pg_namespace WHERE nspname IN ('poc','poc_private')").fetchone()==(0,)
subprocess.run([sys.executable,'-m','context_poc.migrate','up'],check=True)
assert before==snapshot(),'POC schema/function/ACL/RLS drift'
Path(os.environ['CAC_EVIDENCE_DIR'],'poc-schema.json').write_text(json.dumps(before,default=str,indent=2))
print('POC ROUNDTRIP PASS: schema/constraints/function owners/ACL/RLS match; fixture data intentionally discarded')
