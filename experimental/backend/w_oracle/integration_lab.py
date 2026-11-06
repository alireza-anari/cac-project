"""W_ORACLE_ASSUMED. External disposable admission controller, not production DR."""
import subprocess
import time
from uuid import uuid4
from psycopg.conninfo import make_conninfo
from psycopg import sql

from w_oracle.lab import OracleLab,ROOT,BANNER
from w_oracle.catalog import MEASURE


class IntegrationLab:
    def __init__(self):
        self.oracle=OracleLab();self.parent=self.oracle.parent;self.cfg=self.parent.cfg

    def connect(self,node='A',role='postgres'):
        return self.parent.connect(node,role)

    def quarantine(self,node):
        with self.oracle.connect() as w:
            if w.execute("SELECT to_regclass('w.actors')").fetchone()[0]:
                w.execute('UPDATE w.actors SET admitted=false WHERE node=%s',(node,))
        with self.connect(node) as c:
            c.execute('ALTER ROLE cac_ctx_runtime NOLOGIN; ALTER ROLE cac_ctx_issuer NOLOGIN')
        # Commit NOLOGIN before taking the drain snapshot. Wait for actual
        # termination and a fresh zero-session observation before touching SQL.
        with self.connect(node) as c:
            c.autocommit=True;end=time.monotonic()+5
            while True:
                rows=c.execute("SELECT pid FROM pg_stat_activity WHERE usename IN ('cac_ctx_runtime','cac_ctx_issuer')").fetchall()
                if not rows:break
                for (pid,) in rows:c.execute('SELECT pg_terminate_backend(%s,1000)',(pid,))
                if time.monotonic()>end:raise AssertionError('Quarantine drain incomplete; restore forbidden')
        print(BANNER,'QUARANTINE',node,'NOLOGIN committed + sessions drained; actor unadmitted',flush=True)

    def teardown_overlay(self,node):
        with self.connect(node) as c:
            if c.execute("SELECT to_regclass('w_guard.config')").fetchone()[0]:
                c.execute((ROOT/'sql/guard_down.sql').read_text())

    def install(self,node):
        definition=(ROOT/'sql/guard.sql').read_text()
        definition=definition.replace('-- MEASUREMENT_FUNCTION',
            'CREATE FUNCTION w_guard.measure() RETURNS text LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $measure$ '+MEASURE+' $measure$;')
        with self.connect(node) as c:c.execute(definition)

    def measure(self,node):
        with self.connect(node) as c:return c.execute(MEASURE).fetchone()[0]

    def admit(self,node,expected):
        measured=self.measure(node)
        if measured!=expected:raise AssertionError('External verifier manifest mismatch; quarantine retained')
        actor=self.oracle.cfg['actors'][node]
        actor.update(incarnation=str(uuid4()),manifest=measured)
        # Admission incarnation rotates on every supported app restore/reapply.
        # The controller/configuration live outside the ABC schema dump scope.
        conn=make_conninfo(host='witness',port=5432,dbname='cac_s009f_oracle',
            user=actor['check'],password=actor['check_password'],connect_timeout=2,
            options='-c statement_timeout=1500 -c lock_timeout=700')
        with self.connect(node) as c:
            c.execute('DELETE FROM w_guard.config')
            c.execute('INSERT INTO w_guard.config VALUES(true,%s,%s,%s,%s,%s,0,%s)',
                (self.oracle.cfg['root'],self.oracle.namespace,self.oracle.cfg['policy'],node,actor['incarnation'],conn))
        with self.oracle.connect() as w:
            w.execute('UPDATE w.actors SET incarnation=%s,manifest=%s,admitted=true WHERE node=%s',
                      (actor['incarnation'],measured,node))
        with self.connect(node) as c:c.execute('ALTER ROLE cac_ctx_runtime LOGIN; ALTER ROLE cac_ctx_issuer LOGIN')
        self.oracle.cfg['approved_manifest']=expected;self.oracle.save()
        print(BANNER,'ADMISSION',node,'manifest',measured,'new incarnation',actor['incarnation'],flush=True)

    def reset(self):
        for node in ['A','B']:
            self.quarantine(node);self.teardown_overlay(node)
        self.parent.reset();self.oracle.reset()
        self.install('A')
        approved=self.measure('A')
        self.admit('A',approved)
        with self.oracle.connect() as w:w.execute("UPDATE w.actors SET admitted=false WHERE node='B'")

    def restore(self):
        self.quarantine('B')
        with self.connect('B') as c:
            c.execute('DROP SCHEMA IF EXISTS w_guard CASCADE; DROP SCHEMA IF EXISTS fence CASCADE; DROP SCHEMA IF EXISTS fence_private CASCADE; DROP SCHEMA IF EXISTS poc CASCADE; DROP SCHEMA IF EXISTS poc_private CASCADE')
        a,b=self.cfg['A'],self.cfg['B']
        schemas=['poc','poc_private','fence','fence_private','w_guard']
        command=['docker','exec',a['container'],'pg_dump','-U','postgres','-d','cac_s007_test','-Fc']
        for schema in schemas:command+=['-n',schema]
        dump=subprocess.run(command,capture_output=True,check=True,timeout=20).stdout
        result=subprocess.run(['docker','exec','-i',b['container'],'pg_restore','-U','postgres','-d','cac_s007_test','--exit-on-error'],input=dump,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20)
        if result.returncode:raise AssertionError('Private independent application restore failed')
        self.parent.bind('B');self.admit('B',self.oracle.cfg['approved_manifest'])
        print(BANNER,'ACTUAL RESTORE',a['sid'],'->',b['sid'],'guard remeasured; W untouched',flush=True)

    def close(self):self.oracle.close()
