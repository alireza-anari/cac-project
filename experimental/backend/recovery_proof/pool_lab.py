"""Test-only transaction-pool transport; original SQL and Gate are unchanged."""
import os
from pathlib import Path
import subprocess
import tempfile
import time

import psycopg

from recovery_fencing.broker import Broker
from recovery_fencing.lab import require


class Pool:
    def __init__(self, lab):
        require()
        self.lab = lab
        self.directory = tempfile.TemporaryDirectory(prefix='cac-s009d-pool-')
        self.process = None
        self.log = tempfile.TemporaryFile()
        directory = Path(self.directory.name)
        runtime = 'cac_ctx_runtime'
        password = lab.cfg['A']['passwords'][runtime]
        users = directory / 'users.txt'
        users.write_text('"' + runtime + '" "' + password + '"\n')
        users.chmod(0o600)
        config = directory / 'pool.ini'
        config.write_text(f'''[databases]
one = host=127.0.0.1 port=5432 dbname=cac_s007_test pool_size=1
[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6544
unix_socket_dir =
auth_type = scram-sha-256
auth_file = {users}
pool_mode = transaction
default_pool_size = 1
max_client_conn = 32
max_prepared_statements = 0
server_reset_query = DISCARD ALL
server_reset_query_always = 0
log_connections = 0
log_disconnections = 0
pidfile = {directory}/pool.pid
''')
        config.chmod(0o600)
        try:
            self.process = subprocess.Popen(
                ['/usr/sbin/pgbouncer', str(config)],
                env={'PATH': os.environ['PATH'], 'LANG': 'C.UTF-8'},
                stdout=self.log, stderr=self.log)
            deadline = time.monotonic() + 8
            while True:
                try:
                    with self.connect() as c:
                        assert c.execute('SELECT 1').fetchone() == (1,)
                    break
                except psycopg.Error:
                    if self.process.poll() is not None or time.monotonic() > deadline:
                        raise AssertionError('Disposable pool startup failed') from None
                    time.sleep(.05)
        except BaseException:
            self.close()
            raise

    def connect(self):
        c = psycopg.connect(host='127.0.0.1', port=6544, dbname='one',
                            user='cac_ctx_runtime',
                            password=self.lab.cfg['A']['passwords']['cac_ctx_runtime'],
                            connect_timeout=2, prepare_threshold=None)
        try:
            c.execute("SET LOCAL statement_timeout='2500ms'")
            c.execute("SET LOCAL lock_timeout='700ms'")
            return c
        except BaseException:
            c.close()
            raise

    def close(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.log.close()
        self.directory.cleanup()


class PoolBroker(Broker):
    def __init__(self, lab, pool):
        super().__init__(lab, 'A')
        self.pool = pool
        self.direct = Broker(lab, 'A')

    def local(self, role):
        return self.pool.connect() if role == 'cac_ctx_runtime' else self.direct.local(role)

    def ready(self):
        # Readiness uses the same original online SQL via a direct connection:
        # an issuer precheck cannot queue behind a held size-one runtime pool.
        # All runtime authorization/RLS still runs through the real pool.
        return self.direct.ready()
