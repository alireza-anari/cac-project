"""Disposable CI fixtures. All-role credentials are private, never evidence."""
import contextlib
import tempfile
import time
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from uuid import UUID
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

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
            print('HBA self-link witness',name,c.execute("SELECT type,address,auth_method FROM pg_hba_file_rules WHERE address='127.0.0.1'").fetchall(),flush=True)
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
        require();self.cfg=json.loads(Path(os.environ['CAC_C_CONFIG']).read_text());self.temp=tempfile.TemporaryDirectory(prefix='cac-s009c-private-')
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

    def close(self):self.temp.cleanup()
    def save(self):
        p=Path(os.environ['CAC_C_CONFIG'])
        with p.open('w') as f:json.dump(self.cfg,f)
        p.chmod(0o600)
    def install_roles(self):
        if 'fence_secret' in self.cfg['A']:return
        for name in ['A','B']:
            n=self.cfg[name]
            for role in ['cac_fence_activator','cac_fence_ack']:
                n['passwords'][role]=secrets.token_urlsafe(40)
                with self.connect(name) as c:
                    c.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD {}').format(sql.Identifier(role),sql.Literal(n['passwords'][role])))
                    c.execute(sql.SQL('GRANT CONNECT ON DATABASE cac_s007_test TO {}').format(sql.Identifier(role)))
            with self.connect(name) as c:c.execute('GRANT EXECUTE ON FUNCTION pg_control_system() TO cac_ctx_guard')
            n['instance']=str(UUID(int=2001 if name=='A' else 2002))
            n['anchor_role']='cac_anchor_'+name.lower()
            n['anchor_password']=secrets.token_urlsafe(40)
            n['fence_secret']=secrets.token_hex(32)
        with self.connect('C') as c:
            c.execute('CREATE ROLE cac_anchor_guard NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS')
            c.execute('GRANT pg_read_all_stats TO cac_anchor_guard WITH INHERIT TRUE')
            c.execute('GRANT EXECUTE ON FUNCTION pg_control_system() TO cac_anchor_guard')
            c.execute('REVOKE ALL ON DATABASE cac_s009c_anchor FROM PUBLIC;REVOKE ALL ON SCHEMA public FROM PUBLIC;GRANT USAGE ON SCHEMA public TO cac_anchor_guard')
            for name in ['A','B']:
                n=self.cfg[name]
                c.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS PASSWORD {}').format(sql.Identifier(n['anchor_role']),sql.Literal(n['anchor_password'])))
                c.execute(sql.SQL('GRANT CONNECT ON DATABASE cac_s009c_anchor TO {}').format(sql.Identifier(n['anchor_role'])))
        self.save()
    def reset(self):
        with self.connect('A') as c:
            if c.execute("SELECT 1 FROM pg_namespace WHERE nspname='fence'").fetchone():c.execute((ROOT/'sql/down.sql').read_text())
        self.seed()
        with self.connect('B') as c:c.execute('DROP SCHEMA IF EXISTS fence CASCADE;DROP SCHEMA IF EXISTS fence_private CASCADE;DROP SCHEMA IF EXISTS poc CASCADE;DROP SCHEMA IF EXISTS poc_private CASCADE')
        with self.connect('C') as c:
            c.execute('DROP SCHEMA IF EXISTS anchor CASCADE')
            c.execute((ROOT/'sql/anchor.sql').read_text())
            for name in ['A','B']:
                n=self.cfg[name]
                c.execute('INSERT INTO anchor.instances VALUES(%s,%s,%s,%s)',(n['instance'],n['anchor_role'],n['sid'],bytes.fromhex(n['fence_secret'])))
        with self.connect('A') as c:c.execute((ROOT/'sql/up.sql').read_text())
        self.bind('A')
    def bind(self,name):
        n=self.cfg[name]
        anchor=make_conninfo(host='anchor',port=5432,dbname='cac_s009c_anchor',user=n['anchor_role'],password=n['anchor_password'],connect_timeout=2,options='-c statement_timeout=1500 -c lock_timeout=1000')
        ack=make_conninfo(host='primary' if name=='A' else 'restore',port=5432,dbname='cac_s007_test',user='cac_fence_ack',password=n['passwords']['cac_fence_ack'],connect_timeout=2,options='-c statement_timeout=1500')
        with self.connect(name) as c:
            c.execute('DELETE FROM fence_private.config')
            c.execute('INSERT INTO fence_private.config VALUES(true,%s,%s,%s,%s,%s,%s)',(n['instance'],n['sid'],self.cfg['C']['sid'],anchor,ack,bytes.fromhex(n['fence_secret'])))
            c.execute('UPDATE fence_private.state SET epoch=0,generation=NULL,request=NULL,ready=false')
    def docker(self,*args):
        subprocess.run(['docker',*args],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=25)
    def wait(self,name):
        end=time.monotonic()+15
        while True:
            try:
                with self.connect(name) as c:c.execute('SELECT 1')
                return
            except psycopg.Error:
                if time.monotonic()>end:raise
                time.sleep(.1)
    def wait_local_quiet(self,name):
        end=time.monotonic()+5
        with self.connect(name) as c:
            c.autocommit=True
            while c.execute("SELECT count(*) FROM pg_stat_activity WHERE usename IN ('cac_ctx_runtime','cac_ctx_issuer') AND state='idle in transaction'").fetchone()[0]:
                if time.monotonic()>end:raise AssertionError('Old local transaction still active')
                time.sleep(.05)
    @contextlib.contextmanager
    def mutate_anchor_return(self,proof):
        signature='anchor.attest(text,text,text,text,int,text)'
        with self.connect('C') as c:definition=c.execute('SELECT pg_get_functiondef(%s::regprocedure)',(signature,)).fetchone()[0]
        try:
            with self.connect('C') as c:
                c.execute(sql.SQL("CREATE OR REPLACE FUNCTION anchor.attest(nonce text,mode_arg text,t text,sid text,dbpid int,dbtx text) RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,anchor AS $body$ BEGIN RETURN {};END $body$").format(sql.Literal(proof)))
            yield
        finally:
            with self.connect('C') as c:c.execute(definition)
    def broker_path(self,name):
        from recovery_fencing.broker import Broker
        p=Path(self.temp.name)/(name+'.json')
        if p.exists():p.unlink()
        private(p,Broker(self,name).cfg)
        return p
    def crash_worker(self,name,stage,operation='activate',request=None):
        return subprocess.run([sys.executable,'-m','recovery_fencing.worker',str(self.broker_path(name)),operation,stage,request or str(UUID(int=9900))],capture_output=True,text=True,timeout=15)
    def paused_worker(self,name):
        return subprocess.Popen([sys.executable,'-m','recovery_fencing.worker',str(self.broker_path(name)),'pause','none',str(UUID(int=9901))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)

if __name__=='__main__':bootstrap()
