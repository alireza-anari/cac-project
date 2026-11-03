"""Root-only disposable CI orchestrator; never part of runtime or issuer."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from context_poc.harness import CFG, connect, seed, P1, P2, S1, S2, S3, U1

ISSUER, RUNTIME, POOL = 62001, 62002, 62003

def drop(uid):
    def apply():
        os.setgroups([]); os.setgid(uid); os.setuid(uid)
    return apply

def safe_env(): return {'PATH': os.environ['PATH'], 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'}

class Worker:
    def __init__(self, lab, many=False):
        cfg = lab.directory / ('runtime-many.json' if many else 'runtime.json')
        self.p = subprocess.Popen([sys.executable, str(lab.directory/'worker.py'), str(cfg),
            str(lab.directory/'issuer.json'), str(lab.issuer.pid), S1, P1],
            user=RUNTIME, group=RUNTIME, extra_groups=[], env=safe_env(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True)
    def reply(self, op, **args):
        self.p.stdin.write(json.dumps({'op':op, 'args':args})+'\n'); self.p.stdin.flush()
        line = self.p.stdout.readline()
        if not line: raise AssertionError('runtime process ended')
        return json.loads(line)
    def call(self, op, **args):
        r = self.reply(op, **args)
        if not r['ok']: raise AssertionError('runtime operation failed: '+str(r.get('state')))
        return r['value']
    def deny(self, op='records', state='42501', **args):
        r = self.reply(op, **args)
        assert r == {'ok':False, 'state':state}, r
    def close(self):
        if self.p.poll() is None:
            self.p.stdin.close()
            try: self.p.wait(timeout=5)
            except subprocess.TimeoutExpired: self.p.kill(); self.p.wait()
        self.p.stdout.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()

class Lab:
    S1, S2, S3, P1, P2, U1 = S1, S2, S3, P1, P2, U1
    def __init__(self):
        assert os.geteuid() == 0 and os.environ.get('CAC_EXPERIMENTAL_DISPOSABLE') == '1'
        assert CFG['connection']['dbname'] == 'cac_s007_test'
        self.directory = Path(tempfile.mkdtemp(prefix='cac-s009b-', dir='/tmp'))
        self.directory.chmod(0o755)
        self.children = []
        self.logs = []
        try:
            seed()
            # Runtime cannot traverse runner's home. Copy only the two credential-free
            # entrypoints to a root-owned read-only execution directory.
            for script in ['issuer.py','worker.py']:
                target=self.directory/script
                target.write_text(Path(__file__).with_name(script).read_text())
                target.chmod(0o644)
            role = 'cac_ctx_issuer'
            self.private('issuer.json', dict(connection=CFG['connection'],role=role,password=CFG['passwords'][role]), ISSUER)
            sock = str(self.directory/'issuer.sock')
            self.issuer = self.start([sys.executable, str(self.directory/'issuer.py'), str(self.directory/'issuer.json'), sock, str(RUNTIME)], ISSUER)
            role = 'cac_ctx_runtime'
            for many, alias in [(False,'one'),(True,'many')]:
                connection = dict(CFG['connection'],port=6543,dbname=alias)
                self.private('runtime-many.json' if many else 'runtime.json', dict(connection=connection,
                    role=role,password=CFG['passwords'][role],proof=CFG['poc_proofs'][0],socket=sock), RUNTIME)
            # Pooler is a third trusted process with runtime password only.
            auth = '"cac_ctx_runtime" "'+CFG['passwords'][role]+'"\n'
            self.private('users.txt', auth, POOL)
            config = f'''[databases]
one = host=127.0.0.1 port={CFG['connection']['port']} dbname=cac_s007_test pool_size=1
many = host=127.0.0.1 port={CFG['connection']['port']} dbname=cac_s007_test pool_size=4
[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6543
unix_socket_dir =
auth_type = scram-sha-256
auth_file = {self.directory}/users.txt
pool_mode = transaction
max_client_conn = 64
default_pool_size = 1
server_reset_query = DISCARD ALL
server_reset_query_always = 0
max_prepared_statements = 0
log_connections = 0
log_disconnections = 0
pidfile = {self.directory}/pool.pid
'''
            # PID file directory must be writable only by pool UID, never by runtime.
            pooldir = self.directory/'pool'; pooldir.mkdir(); pooldir.chmod(0o700); os.chown(pooldir,POOL,POOL)
            config = config.replace(str(self.directory)+'/pool.pid', str(pooldir)+'/pool.pid')
            self.private('pool.ini',config,POOL)
            self.pool = self.start(['/usr/sbin/pgbouncer',str(self.directory/'pool.ini')],POOL)
            deadline=time.monotonic()+10
            while not Path(sock).exists():
                if self.issuer.poll() is not None or time.monotonic()>deadline: raise AssertionError('issuer startup')
                time.sleep(.05)
            while True:
                try:
                    with socket.create_connection(('127.0.0.1',6543),timeout=.2): break
                except OSError:
                    if self.pool.poll() is not None or time.monotonic()>deadline: raise AssertionError('pool startup')
                    time.sleep(.05)
            print('PROCESS WITNESS issuer_uid',ISSUER,'runtime_uid',RUNTIME,'pool_uid',POOL,flush=True)
            print(subprocess.check_output(['/usr/sbin/pgbouncer','--version'],text=True).strip(),flush=True)
        except BaseException:
            for log in self.logs:
                log.seek(0)
                output=log.read().decode(errors='replace')
                for secret in [*CFG['passwords'].values(),*CFG['poc_proofs'],CFG['issuer_key']]:
                    output=output.replace(secret,'[REDACTED]')
                print('SANITIZED CHILD STARTUP DIAGNOSTIC',output[-2000:],flush=True)
            self.close(); raise
    def private(self, name, value, uid):
        p=self.directory/name
        p.write_text(value if isinstance(value,str) else json.dumps(value))
        p.chmod(0o600); os.chown(p,uid,uid)
    def start(self,args,uid):
        # No sensitive environment inherited by either child. Logs are transient,
        # never uploaded: a failed DB request must not expose its proof to artifacts.
        log=tempfile.TemporaryFile(); self.logs.append(log)
        p=subprocess.Popen(args,user=uid, group=uid, extra_groups=[],env=safe_env(),stdout=log,stderr=log)
        self.children.append(p); return p
    def __enter__(self): return self
    def __exit__(self,*a): self.close()
    def worker(self,many=False): return Worker(self,many)
    def close(self):
        for p in self.children:
            if p.poll() is None:
                p.terminate()
                try: p.wait(timeout=5)
                except subprocess.TimeoutExpired: p.kill(); p.wait()
        for f in self.logs: f.close()
        shutil.rmtree(self.directory,ignore_errors=True)
