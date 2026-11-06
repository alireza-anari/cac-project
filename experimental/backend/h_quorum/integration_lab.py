"""Q_SURVIVAL_ONLY. Disposable externally pinned admission, never production DR."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from uuid import uuid4
from psycopg.conninfo import make_conninfo
from recovery_fencing.lab import Lab
from h_quorum.common import BANNER,config,Denied
from h_quorum.cluster import _save
from h_quorum.catalog import MEASURE
from h_quorum.rpc import Client

ROOT=Path(__file__).parent
class IntegrationLab:
    def __init__(self):self.parent=Lab();self.cfg=self.parent.cfg;self.rootcfg=config();self.namespace=None
    def connect(self,node='A',role='postgres'):return self.parent.connect(node,role)
    def quarantine(self,node):
        with self.connect(node) as c:c.execute('ALTER ROLE cac_ctx_runtime NOLOGIN;ALTER ROLE cac_ctx_issuer NOLOGIN')
        with self.connect(node) as c:
            c.autocommit=True;deadline=time.monotonic()+5
            while True:
                rows=c.execute("SELECT pid FROM pg_stat_activity WHERE usename IN ('cac_ctx_runtime','cac_ctx_issuer')").fetchall()
                if not rows:break
                for (pid,) in rows:c.execute('SELECT pg_terminate_backend(%s,1000)',(pid,))
                if time.monotonic()>deadline:raise AssertionError('Quarantine drain incomplete')
        print(BANNER,'QUARANTINE',node,'committed NOLOGIN and zero observed live app sessions',flush=True)
    def down(self,node):
        with self.connect(node) as c:
            if c.execute("SELECT to_regclass('h_guard.config')").fetchone()[0]:c.execute((ROOT/'sql/down.sql').read_text())
    def install(self,node):
        definition=(ROOT/'sql/guard.sql').read_text().replace('-- MEASUREMENT_FUNCTION','CREATE FUNCTION h_guard.measure() RETURNS text LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $measure$ '+MEASURE+' $measure$;')
        with self.connect(node) as c:c.execute(definition)
    def measure(self,node):
        with self.connect(node) as c:return c.execute(MEASURE).fetchone()[0]
    def validate_private_acl(self,node):
        private={'cac_ctx_runtime':['poc_private.challenge_unfenced()','poc_private.verify_unfenced()','h_guard.verify_c()','h_guard.c_is_ready()','fence_private.check_guard_c()','h_guard.rpc(text,jsonb)'],
                 'cac_ctx_issuer':['poc_private.issue_unfenced(text,text,uuid,text,uuid,jsonb)','h_guard.issue_c(text,text,uuid,text,uuid,jsonb)','h_guard.c_is_ready()','fence_private.check_guard_c()','h_guard.rpc(text,jsonb)']}
        with self.connect(node) as c:
            for role,functions in private.items():
                for signature in functions:
                    if c.execute('SELECT has_function_privilege(%s,%s,\'EXECUTE\')',(role,signature)).fetchone()[0]:raise AssertionError('Legacy/private execution privilege; admission denied')
                if c.execute('SELECT rolsuper OR rolbypassrls OR rolcreaterole OR rolcreatedb OR rolreplication FROM pg_roles WHERE rolname=%s',(role,)).fetchone()[0]:raise AssertionError('Privileged application role')
                if c.execute('SELECT has_table_privilege(%s,\'h_guard.config\',\'SELECT\')',(role,)).fetchone()[0]:raise AssertionError('Private checker config exposed')
            if c.execute("SELECT relrowsecurity AND relforcerowsecurity FROM pg_class WHERE oid='poc.records'::regclass").fetchone()!=(True,):raise AssertionError('FORCE RLS absent')
    def bind(self,node):
        actor=self.actors[node];checker=node+'_check'
        conn=make_conninfo(host=self.rootcfg['gateway_ip'],port=self.rootcfg['wire_port'],dbname='rcheck',user=checker,password=self.rootcfg['roles'][checker]['password'],sslmode='verify-full',sslrootcert='/tmp/cac-h-ca.crt',connect_timeout=2)
        with self.connect(node) as c:
            c.execute('DELETE FROM h_guard.config')
            c.execute('INSERT INTO h_guard.config VALUES(true,%s,%s,1,%s,%s,0,%s)',(self.rootcfg['root_id'],self.namespace,node,actor['incarnation'],conn))
    def restart_service(self):
        path=Path(os.environ['RUNNER_TEMP'])/'cac-h-service.pid';pid=int(path.read_text())
        command=Path('/proc',str(pid),'cmdline')
        if b'h_quorum.service' not in command.read_bytes():raise AssertionError('Unowned service process')
        os.kill(pid,signal.SIGTERM);deadline=time.monotonic()+5
        def live():
            try:return bool(command.read_bytes())
            except FileNotFoundError:return False
        while live():
            if time.monotonic()>deadline:raise AssertionError('Old root transport still live')
            time.sleep(.05)
        log=Path(os.environ['GITHUB_WORKSPACE'])/'evidence-s009h/service.log'
        with log.open('ab') as stream:
            process=subprocess.Popen([sys.executable,'-m','h_quorum.service'],stdout=stream,stderr=stream,start_new_session=True)
        path.write_text(str(process.pid));path.chmod(0o600)
        deadline=time.monotonic()+10
        while True:
            try:
                Client(self.rootcfg,'control',self.namespace).call('status');break
            except Denied:
                if process.poll() is not None or time.monotonic()>deadline:raise AssertionError('Current root service failed to start') from None
                time.sleep(.1)
    def reset(self):
        # A fresh independent synthetic dataset/test namespace, never operational
        # recovery or clearing UNKNOWN in an existing namespace. Old R history stays.
        for node in ('A','B'):self.quarantine(node);self.down(node)
        self.parent.reset();self.install('A');measured=self.measure('A')
        self.rootcfg=config()
        expected=self.rootcfg.get('approved_manifest')
        if expected is None:self.rootcfg['approved_manifest']=measured
        elif measured!=expected:raise AssertionError('Pristine external manifest changed; no rebaseline')
        self.namespace=str(uuid4());self.rootcfg['app_namespace']=self.namespace
        self.actors={n:dict(sid=self.cfg[n]['sid'],incarnation=str(uuid4()),manifest=measured,admitted=n=='A',profile_required=True) for n in ('A','B')}
        Client(self.rootcfg,'control',self.namespace).call('genesis',dict(actors=self.actors))
        self.bind('A');self.validate_private_acl('A')
        if self.measure('A')!=self.rootcfg['approved_manifest']:raise AssertionError('Final admission manifest mismatch')
        _save(Path(os.environ['CAC_H_CONFIG']),self.rootcfg);self.restart_service()
        with self.connect() as c:c.execute('ALTER ROLE cac_ctx_runtime LOGIN;ALTER ROLE cac_ctx_issuer LOGIN')
        print(BANNER,'ADMISSION A externally pinned current profile; catalog',measured,'namespace',self.namespace,flush=True)
        return True
    def close(self):self.parent.close()
