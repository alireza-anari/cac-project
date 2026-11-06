"""W_ORACLE_ASSUMED. Private fixture controller, outside ABC restore scope."""
import json
import os
from pathlib import Path
import secrets
from uuid import uuid4

import psycopg
from psycopg import sql

from recovery_fencing.lab import Lab as ParentLab, private, require

ROOT = Path(__file__).parent
BANNER = 'W_ORACLE_ASSUMED / LANE1_ONLY / ROOT_AND_ORPHAN_RECOVERY_UNPROVED'


def bootstrap():
    require()
    parent = ParentLab()
    parent.install_roles()
    cfg = dict(connection=dict(host='127.0.0.1', port=5435, dbname='cac_s009f_oracle'),
               password=secrets.token_urlsafe(48), container=os.environ['CAC_F_W_CONTAINER'],
               root=str(uuid4()), policy=1, actors={})
    with psycopg.connect(**cfg['connection'], user='postgres',
                          password='synthetic-s009f-disposable-only') as c:
        c.execute(sql.SQL('ALTER ROLE postgres PASSWORD {}').format(sql.Literal(cfg['password'])))
        c.execute('CREATE EXTENSION pgcrypto')
        c.execute('CREATE ROLE cac_w_guard NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS')
        c.execute('GRANT pg_read_all_stats TO cac_w_guard WITH INHERIT TRUE')
        c.execute('GRANT EXECUTE ON FUNCTION pg_control_system() TO cac_w_guard')
        c.execute('REVOKE ALL ON DATABASE cac_s009f_oracle FROM PUBLIC; REVOKE ALL ON SCHEMA public FROM PUBLIC')
        c.execute('GRANT USAGE ON SCHEMA public TO cac_w_guard')
        cfg['sid'] = c.execute('SELECT system_identifier::text FROM pg_control_system()').fetchone()[0]
        assert c.execute("SELECT current_setting('fsync'),current_setting('synchronous_commit'),current_setting('full_page_writes'),current_setting('max_prepared_transactions')").fetchone()==('on','on','on','0')
        for node in ['A', 'B']:
            actor = dict(incarnation=str(uuid4()), manifest='a'*64)
            for kind in ['coord', 'check']:
                role = 'cac_w_' + node.lower() + '_' + kind
                password = secrets.token_urlsafe(40)
                actor[kind] = role
                actor[kind+'_password'] = password
                c.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD {}').format(sql.Identifier(role),sql.Literal(password)))
                c.execute(sql.SQL('GRANT CONNECT ON DATABASE cac_s009f_oracle TO {}').format(sql.Identifier(role)))
            cfg['actors'][node] = actor
    private(Path(os.environ['CAC_F_CONFIG']), cfg)
    print(BANNER, 'oracle SID', cfg['sid'], 'durability controls ON; prepared disabled; same-host model; authenticated channel ASSUMED', flush=True)
    parent.close()


class OracleLab:
    def __init__(self):
        require()
        self.parent = ParentLab()
        self.cfg = json.loads(Path(os.environ['CAC_F_CONFIG']).read_text())

    def connect(self, node=None, check=False):
        if node is None:
            role, password = 'postgres', self.cfg['password']
        else:
            a = self.cfg['actors'][node]
            kind = 'check' if check else 'coord'
            role, password = a[kind], a[kind+'_password']
        return psycopg.connect(**self.cfg['connection'], user=role, password=password,
                               connect_timeout=2, prepare_threshold=None,
                               options='-c statement_timeout=3000 -c lock_timeout=800')

    def reset(self):
        # Independent-test genesis only, NEVER operational recovery or OPEN clearing.
        self.namespace = str(uuid4())
        with self.connect() as c:
            c.execute('DROP SCHEMA IF EXISTS w CASCADE')
            c.execute((ROOT/'sql/oracle.sql').read_text())
            c.execute('INSERT INTO w.control VALUES(true,%s,%s,%s,true,public.gen_random_bytes(32))',
                      (self.cfg['root'], self.namespace, self.cfg['policy']))
            for node, actor in self.cfg['actors'].items():
                c.execute('INSERT INTO w.actors VALUES(%s,%s,%s,%s,%s,%s,true)',
                          (node, actor['coord'], actor['check'], self.parent.cfg[node]['sid'],
                           actor['incarnation'], actor['manifest']))

    def close(self):
        self.parent.close()


if __name__ == '__main__':
    bootstrap()
