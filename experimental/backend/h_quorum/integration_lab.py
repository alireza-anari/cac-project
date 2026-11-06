"""Q_SURVIVAL_ONLY. Disposable externally pinned admission, never production DR."""
import os
import json
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
        with self.connect(node) as c:
            c.execute('SET LOCAL search_path=pg_catalog')
            return c.execute(MEASURE).fetchone()[0]
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
    def bind(self,node,epoch=0):
        actor=self.actors[node];checker=node+'_check'
        conn=make_conninfo(host=self.rootcfg['gateway_ip'],port=self.rootcfg['wire_port'],dbname='rcheck',user=checker,password=self.rootcfg['roles'][checker]['password'],sslmode='verify-full',sslrootcert='/tmp/cac-h-ca.crt',connect_timeout=2)
        with self.connect(node) as c:
            c.execute('DELETE FROM h_guard.config')
            c.execute('INSERT INTO h_guard.config VALUES(true,%s,%s,1,%s,%s,%s,%s)',(self.rootcfg['root_id'],self.namespace,node,actor['incarnation'],epoch,conn))
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
        with self.connect() as c:live_measure=c.execute('SELECT h_guard.measure()').fetchone()[0]
        if live_measure!=measured:raise AssertionError('External and live guard catalog measurement differ; LOGIN remains closed')
        self.rootcfg=config()
        expected=self.rootcfg.get('approved_manifest')
        if expected is None:self.rootcfg['approved_manifest']=measured
        elif measured!=expected:raise AssertionError('Pristine external manifest changed; no rebaseline')
        self.namespace=str(uuid4());self.rootcfg['app_namespace']=self.namespace;self.rootcfg['w_sid']=self.cfg['C']['sid']
        with self.connect('C') as c:
            c.execute('DROP SCHEMA IF EXISTS h_w CASCADE');c.execute((ROOT/'sql/w.sql').read_text())
        self.actors={n:dict(sid=self.cfg[n]['sid'],incarnation=str(uuid4()),manifest=measured,admitted=n=='A',profile_required=True,w_required=True) for n in ('A','B')}
        Client(self.rootcfg,'control',self.namespace).call('genesis',dict(actors=self.actors))
        self.bind('A');self.validate_private_acl('A')
        if self.measure('A')!=self.rootcfg['approved_manifest']:raise AssertionError('Final admission manifest mismatch')
        _save(Path(os.environ['CAC_H_CONFIG']),self.rootcfg);self.restart_service();self.replay()
        with self.connect() as c:c.execute('ALTER ROLE cac_ctx_runtime LOGIN;ALTER ROLE cac_ctx_issuer LOGIN')
        print(BANNER,'ADMISSION A externally pinned current profile; catalog',measured,'namespace',self.namespace,flush=True)
        return True
    def replay(self):
        from h_quorum.projection import publish
        return publish(self)
    def admit(self,node):
        if self.measure(node)!=self.rootcfg['approved_manifest']:raise AssertionError('External verifier manifest mismatch; quarantine retained')
        self.validate_private_acl(node)
        with self.connect(node) as c:
            if c.execute('SELECT h_guard.measure()').fetchone()[0]!=self.rootcfg['approved_manifest']:raise AssertionError('Live manifest mismatch')
        actor=dict(self.actors[node],incarnation=str(uuid4()),admitted=True,profile_required=True,w_required=True)
        control=Client(self.rootcfg,'control',self.namespace)
        control.call('admit_actor',dict(node=node,actor=actor));self.actors[node]=actor
        status=control.call('status')
        self.bind(node,status['epoch'] if status['owner']==node and status['phase']=='ACTIVE' else 0)
        self.replay()
        with self.connect(node) as c:c.execute('ALTER ROLE cac_ctx_runtime LOGIN;ALTER ROLE cac_ctx_issuer LOGIN')
        print(BANNER,'ADMISSION',node,'actual SID',actor['sid'],'pinned manifest',actor['manifest'],'new incarnation',actor['incarnation'],flush=True)
    def restore(self):
        self.r_evidence('before-app-restore');self.quarantine('B')
        with self.connect('B') as c:c.execute('DROP SCHEMA IF EXISTS h_guard CASCADE;DROP SCHEMA IF EXISTS fence CASCADE;DROP SCHEMA IF EXISTS fence_private CASCADE;DROP SCHEMA IF EXISTS poc CASCADE;DROP SCHEMA IF EXISTS poc_private CASCADE')
        a,b=self.cfg['A'],self.cfg['B']
        command=['docker','exec',a['container'],'pg_dump','-U','postgres','-d','cac_s007_test','-Fc']
        for schema in ('poc','poc_private','fence','fence_private','h_guard'):command+=['-n',schema]
        dump=subprocess.run(command,capture_output=True,check=True,timeout=30).stdout
        result=subprocess.run(['docker','exec','-i',b['container'],'pg_restore','-U','postgres','-d','cac_s007_test','--exit-on-error'],input=dump,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
        if result.returncode:raise AssertionError('Independent B restore failed (private dump not logged)')
        self.parent.bind('B');self.admit('B');self.r_evidence('after-app-restore-admission')
        print(BANNER,'ACTUAL APP RESTORE',a['sid'],'->',b['sid'],'NOLOGIN drain + new admitted B incarnation',flush=True)
    def r_evidence(self,label):
        from h_quorum.cluster import Cluster
        control=Client(self.rootcfg,'control',self.namespace)
        witness=dict(topology=Cluster(self.rootcfg).snapshot(label),state=control.call('status'),operations=control.call('inspect'))
        print(BANNER,'CURRENT R WITNESS',json.dumps(witness,sort_keys=True),flush=True)
        return witness
    def dump_w(self):
        self.r_evidence('before-w-snapshot')
        result=subprocess.run(['docker','exec',self.cfg['C']['container'],'pg_dump','-U','postgres','-d','cac_s009c_anchor','-Fc','-n','anchor','-n','h_w'],capture_output=True,timeout=30)
        if result.returncode:raise AssertionError('Private W dump failed')
        return result.stdout
    def restore_w(self,dump):
        before=self.r_evidence('before-w-restore')
        with self.connect('C') as c:c.execute('DROP SCHEMA anchor CASCADE;DROP SCHEMA h_w CASCADE')
        result=subprocess.run(['docker','exec','-i',self.cfg['C']['container'],'pg_restore','-U','postgres','-d','cac_s009c_anchor','--exit-on-error'],input=dump,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
        if result.returncode:raise AssertionError('Private W restore failed')
        after=self.r_evidence('after-w-restore')
        if before['state']!=after['state'] or before['operations']!=after['operations']:raise AssertionError('W restore changed authoritative R state')
        print(BANNER,'ACTUAL W RESTORE legacy anchor + public projection; current R and external profile untouched',flush=True)
    def close(self):self.parent.close()
