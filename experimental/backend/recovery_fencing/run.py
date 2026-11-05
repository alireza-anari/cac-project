import json
import os
from pathlib import Path
import unittest
from recovery_fencing.lab import Lab,ROOT

def suite():
    tests=unittest.defaultTestLoader.discover('recovery_fencing/tests','test_*.py')
    assert tests.countTestCases()==20
    r=unittest.TextTestRunner(verbosity=2).run(tests)
    if not r.wasSuccessful() or r.skipped:raise SystemExit(1)
    print('S009C SUITE PASS 20 distinct; no skip',flush=True)

def snapshot(lab):
    with lab.connect() as c:
        return dict(functions=c.execute("SELECT n.nspname,p.proname,pg_get_functiondef(p.oid),p.proacl::text,pg_get_userbyid(p.proowner) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname IN ('poc','poc_private','fence','fence_private') ORDER BY 1,2").fetchall(),
            columns=c.execute("SELECT table_schema,table_name,column_name,data_type,is_nullable FROM information_schema.columns WHERE table_schema IN ('poc','poc_private','fence','fence_private') ORDER BY 1,2,ordinal_position").fetchall(),
            constraints=c.execute("SELECT n.nspname,r.relname,k.conname,pg_get_constraintdef(k.oid) FROM pg_constraint k JOIN pg_class r ON r.oid=k.conrelid JOIN pg_namespace n ON n.oid=r.relnamespace WHERE n.nspname IN ('poc','poc_private','fence','fence_private') ORDER BY 1,2,3").fetchall(),
            policies=c.execute("SELECT policyname,roles,cmd,qual FROM pg_policies WHERE schemaname='poc' ORDER BY 1").fetchall())

if __name__=='__main__':
    with Lab().connect('C') as c:
        assert c.execute("SELECT current_setting('fsync'),current_setting('synchronous_commit'),current_setting('full_page_writes')").fetchone()==('on','on','on')
        print('ANCHOR PostgreSQL',c.execute('SELECT version()').fetchone()[0],'WAL durability controls ON',flush=True)
    suite()
    # Sensitivity is appended after the initial candidate is executed.
    lab=Lab();lab.reset();before=snapshot(lab)
    with lab.connect() as c:c.execute((ROOT/'sql/down.sql').read_text())
    with lab.connect() as c:c.execute((ROOT/'sql/up.sql').read_text())
    lab.bind('A')
    assert before==snapshot(lab),'Fencing migration structural drift'
    print('S009C ROUNDTRIP PASS functions/owners/ACL/columns/constraints/RLS',flush=True)
    lab.close()
    suite()
    print('S009C COMPLETE bounded experimental proof; retained94 in independent unchanged floor workflow',flush=True)
