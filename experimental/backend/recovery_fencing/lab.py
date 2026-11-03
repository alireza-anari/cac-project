"""Disposable CI fixtures. All-role credentials are private, never evidence."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from uuid import UUID
import psycopg
from psycopg import sql

ROOT=Path(__file__).parent
P1,S1,S2=[str(UUID(int=i)) for i in (1001,1003,1004)]

def require():
    if os.environ.get('CAC_EXPERIMENTAL_DISPOSABLE')!='1':raise RuntimeError('Disposable only')

def private(path,value):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:json.dump(value,f)

def bootstrap():
    require()
    base=Path(os.environ['CAC_C_CONFIG'])
    bundle={}
    for name,port in [('A',5432),('B',5433)]:
        path=base.with_name(base.name+'.'+name)
        env=dict(os.environ,CAC_TEST_CONFIG=str(path),PGHOST='127.0.0.1',PGPORT=str(port),PGDATABASE='cac_s007_test',PGPASSWORD='synthetic-s009c-disposable-only')
        for command in [['scripts/bootstrap.py'],['-m','context_poc.migrate','bootstrap'],['-m','pool_recovery.rotate_admin']]:
            subprocess.run([sys.executable,*command],env=env,check=True,stdout=subprocess.DEVNULL)
        node=json.loads(path.read_text())
        node['container']=os.environ['CAC_C_'+name+'_CONTAINER']
        bundle[name]=node
        if name=='A':
            subprocess.run([sys.executable,'-m','context_poc.migrate','up'],env=env,check=True,stdout=subprocess.DEVNULL)
        with psycopg.connect(**node['connection'],user='postgres',password=node['passwords']['postgres']) as c:
            c.execute('GRANT USAGE ON SCHEMA public TO cac_ctx_guard')
            c.execute('CREATE EXTENSION dblink WITH SCHEMA public')
            node['sid']=c.execute('SELECT system_identifier::text FROM pg_control_system()').fetchone()[0]
        path.unlink()
    anchor={'connection':dict(host='127.0.0.1',port=5434,dbname='cac_s009c_anchor'),'password':secrets.token_urlsafe(48),'container':os.environ['CAC_C_C_CONTAINER']}
    with psycopg.connect(**anchor['connection'],user='postgres',password='synthetic-s009c-disposable-only') as c:
        c.execute(sql.SQL('ALTER ROLE postgres PASSWORD {}').format(sql.Literal(anchor['password'])))
        c.execute('CREATE EXTENSION pgcrypto')
        anchor['sid']=c.execute('SELECT system_identifier::text FROM pg_control_system()').fetchone()[0]
    bundle['C']=anchor
    assert len({n['sid'] for n in bundle.values()})==3,'Not independent clusters'
    private(base,bundle)
    print('TOPOLOGY independent PG cluster system identifiers',{k:v['sid'] for k,v in bundle.items()},flush=True)

class Lab:
    def __init__(self):
        require();self.cfg=json.loads(Path(os.environ['CAC_C_CONFIG']).read_text())
    def connect(self,node='A',role='postgres'):
        n=self.cfg[node]
        return psycopg.connect(**n['connection'],user=role,password=n['password'] if node=='C' else n['passwords'][role],prepare_threshold=None,connect_timeout=2)
    def seed(self):
        # Reuse the exact parent fixture generator with a private temporary config.
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.json';private(p,self.cfg['A'])
            subprocess.run([sys.executable,'-c','from context_poc.harness import seed;seed()'],env=dict(os.environ,CAC_TEST_CONFIG=str(p)),stdout=subprocess.DEVNULL,check=True)
    def restore(self):
        a,b=self.cfg['A'],self.cfg['B']
        with self.connect('B') as c:
            c.execute('DROP SCHEMA IF EXISTS fence CASCADE;DROP SCHEMA IF EXISTS fence_private CASCADE;DROP SCHEMA IF EXISTS poc CASCADE;DROP SCHEMA IF EXISTS poc_private CASCADE')
        schemas=['poc','poc_private']
        with self.connect() as c:
            if c.execute("SELECT 1 FROM pg_namespace WHERE nspname='fence'").fetchone():schemas+=['fence','fence_private']
        command=['docker','exec',a['container'],'pg_dump','-U','postgres','-d','cac_s007_test','-Fc']
        for name in schemas:command+=['-n',name]
        dump=subprocess.run(command,capture_output=True,check=True,timeout=20).stdout
        r=subprocess.run(['docker','exec','-i',b['container'],'pg_restore','-U','postgres','-d','cac_s007_test','--exit-on-error'],input=dump,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20)
        if r.returncode:raise AssertionError('Independent restore failed (private dump/log not emitted)')
        print('RESTORE WITNESS independent clusters',a['sid'],b['sid'],'schemas',schemas,flush=True)

if __name__=='__main__':bootstrap()
