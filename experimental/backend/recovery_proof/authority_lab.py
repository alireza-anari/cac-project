"""Private disposable anchor snapshots; dump bytes never enter evidence."""
import contextlib
import subprocess
from uuid import uuid4

import psycopg
from psycopg import sql

from recovery_fencing.lab import require


def dump_anchor(lab):
    require()
    return subprocess.run(
        ['docker', 'exec', lab.cfg['C']['container'], 'pg_dump', '-U', 'postgres',
         '-d', 'cac_s009c_anchor', '-Fc', '-n', 'anchor'],
        capture_output=True, check=True, timeout=20).stdout


def restore_anchor(lab, data):
    require()
    with lab.connect('C') as c:
        c.execute('DROP SCHEMA anchor CASCADE')
    result = subprocess.run(
        ['docker', 'exec', '-i', lab.cfg['C']['container'], 'pg_restore',
         '-U', 'postgres', '-d', 'cac_s009c_anchor', '--exit-on-error'],
        input=data, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    assert result.returncode == 0, 'Private anchor restore failed'


@contextlib.contextmanager
def different_cluster_clone(lab):
    require()
    name = 'cac_s009d_anchor_' + uuid4().hex[:12]
    with lab.connect('B') as c:
        c.execute("CREATE ROLE cac_anchor_guard NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS")
        c.execute('GRANT pg_read_all_stats TO cac_anchor_guard WITH INHERIT TRUE')
        c.execute('GRANT EXECUTE ON FUNCTION pg_control_system() TO cac_anchor_guard')
        for node in ['A', 'B']:
            n = lab.cfg[node]
            c.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS PASSWORD {}').format(
                sql.Identifier(n['anchor_role']), sql.Literal(n['anchor_password'])))
    # The fixture has only one such clone test per runner invocation; cleanup
    # also removes these roles so subsequent invocations remain independent.
    connection = dict(lab.cfg['B']['connection'], dbname=name)
    try:
        with lab.connect('B') as c:
            c.autocommit = True
            c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
            c.execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM PUBLIC').format(sql.Identifier(name)))
            for role in [lab.cfg['A']['anchor_role'], lab.cfg['B']['anchor_role']]:
                c.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}').format(sql.Identifier(name), sql.Identifier(role)))
        with psycopg.connect(**connection, user='postgres',
                              password=lab.cfg['B']['passwords']['postgres']) as c:
            c.execute('CREATE EXTENSION pgcrypto WITH SCHEMA public')
            c.execute('REVOKE ALL ON SCHEMA public FROM PUBLIC')
            c.execute('GRANT USAGE ON SCHEMA public TO cac_anchor_guard')
        result = subprocess.run(
            ['docker', 'exec', '-i', lab.cfg['B']['container'], 'pg_restore',
             '-U', 'postgres', '-d', name, '--exit-on-error'],
            input=dump_anchor(lab), stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=20)
        assert result.returncode == 0, 'Private different-cluster clone failed'
        yield connection
    finally:
        with lab.connect('B') as c:
            c.autocommit = True
            c.execute(sql.SQL('DROP DATABASE IF EXISTS {} WITH (FORCE)').format(sql.Identifier(name)))
        with lab.connect('B') as c:
            c.execute('REVOKE EXECUTE ON FUNCTION pg_control_system() FROM cac_anchor_guard')
            # Remove only the synthetic clone roles created above, never app roles.
            for role in [lab.cfg['A']['anchor_role'], lab.cfg['B']['anchor_role'], 'cac_anchor_guard']:
                c.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))


def authority_snapshot(lab):
    # Private in-memory comparison only; contains MAC material and ticket hashes.
    with lab.connect('C') as c:
        return dict(
            instances=c.execute('SELECT * FROM anchor.instances ORDER BY id').fetchall(),
            state=c.execute('SELECT * FROM anchor.state').fetchall(),
            activations=c.execute('SELECT * FROM anchor.activations ORDER BY request').fetchall(),
            operations=c.execute('SELECT * FROM anchor.operations ORDER BY id').fetchall(),
            sequence=c.execute('SELECT last_value,is_called FROM anchor.operations_id_seq').fetchone(),
            functions=c.execute(
                "SELECT p.proname,pg_get_function_identity_arguments(p.oid),pg_get_functiondef(p.oid),"
                "p.proacl::text,p.proowner::regrole::text,p.prosecdef,p.proconfig "
                "FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                "WHERE n.nspname='anchor' ORDER BY 1,2").fetchall(),
            tables=c.execute(
                "SELECT r.relname,r.relowner::regrole::text,r.relacl::text,r.relrowsecurity,r.relforcerowsecurity "
                "FROM pg_class r JOIN pg_namespace n ON n.oid=r.relnamespace "
                "WHERE n.nspname='anchor' AND r.relkind IN ('r','S') ORDER BY 1").fetchall())
