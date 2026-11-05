"""Bounded authority faults: actual SQL/role/extension/endpoint/race witnesses."""
import concurrent.futures
import time
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from recovery_fencing.broker import Broker, FenceDenied
from recovery_proof.authority_fixture import AuthorityFixture
from recovery_proof.authority_lab import different_cluster_clone
from recovery_proof.sensitivity import catalog


class AuthorityTests(AuthorityFixture):
    def test_actual_different_endpoint_anchor_clone_is_rejected(self):
        self.positive(self.a)
        with different_cluster_clone(self.lab) as connection:
            with psycopg.connect(**connection, user=self.a.cfg['anchor_role'],
                                  password=self.a.cfg['anchor_password']) as clone:
                status = clone.execute('SELECT anchor.status()').fetchone()[0]
                self.assertEqual(status['anchor_sid'], self.lab.cfg['B']['sid'])
                self.assertNotEqual(status['anchor_sid'], self.lab.cfg['C']['sid'])
                self.assertEqual(status['phase'], 'active')
            bad = Broker(cfg=dict(self.a.cfg, anchor_connection=connection))
            with self.assertRaises(FenceDenied):
                bad.status()
            with self.lab.connect('A') as c:
                original = c.execute('SELECT anchor_conn FROM fence_private.config').fetchone()[0]
            params = conninfo_to_dict(original)
            params.update(host='restore', dbname=connection['dbname'])
            try:
                with self.lab.connect('A') as c:
                    c.execute('UPDATE fence_private.config SET anchor_conn=%s', (make_conninfo(**params),))
                self.assertFalse(self.a.ready())
                with self.assertRaises(FenceDenied):
                    self.positive(self.a)
                print('S009D WRONG ENDPOINT WITNESS actual authenticated clone SID mismatch', flush=True)
            finally:
                with self.lab.connect('A') as c:
                    c.execute('UPDATE fence_private.config SET anchor_conn=%s', (original,))
        self.positive(self.a)

    def test_read_only_anchor_actor_session_fails_closed(self):
        role = self.a.cfg['anchor_role']
        with self.lab.connect('C') as c:
            before = c.execute('SELECT rolconfig FROM pg_roles WHERE rolname=%s', (role,)).fetchone()
            c.execute(sql.SQL('ALTER ROLE {} SET default_transaction_read_only=on').format(sql.Identifier(role)))
        try:
            with psycopg.connect(**self.a.cfg['anchor_connection'], user=role,
                                  password=self.a.cfg['anchor_password']) as actor:
                self.assertEqual(actor.execute('SHOW transaction_read_only').fetchone(), ('on',))
            self.assertFalse(self.a.ready())
            with self.assertRaises(FenceDenied):
                self.a.status()
            print('S009D READONLY WITNESS actor transaction_read_only=on denies authority', flush=True)
        finally:
            with self.lab.connect('C') as c:
                c.execute(sql.SQL('ALTER ROLE {} RESET default_transaction_read_only').format(sql.Identifier(role)))
                self.assertEqual(c.execute('SELECT rolconfig FROM pg_roles WHERE rolname=%s', (role,)).fetchone(), before)
        self.positive(self.a)

    def test_malformed_anchor_response_denies_then_recovers(self):
        signature = 'anchor.attest(text,text,text,text,int,text)'
        before = catalog(self.lab, 'C', signature)
        with self.lab.mutate_anchor_return('not-a-signed-response'):
            self.assertFalse(self.a.ready())
            with self.assertRaises(FenceDenied):
                self.positive(self.a)
        self.assertEqual(catalog(self.lab, 'C', signature), before)
        self.positive(self.a)
        print('S009D MALFORMED RESPONSE WITNESS denied; exact function restored', flush=True)

    def test_sql_channel_outage_denies_with_healthy_broker_channel(self):
        with self.lab.connect('A') as c:
            original = c.execute('SELECT anchor_conn FROM fence_private.config').fetchone()[0]
        params = conninfo_to_dict(original)
        params.update(port='1')
        try:
            with self.lab.connect('A') as c:
                c.execute('UPDATE fence_private.config SET anchor_conn=%s', (make_conninfo(**params),))
            self.assertEqual(self.a.status()['phase'], 'active')
            self.assertFalse(self.a.ready())
            with self.assertRaises(FenceDenied):
                self.positive(self.a)
            print('S009D CHANNEL OUTAGE WITNESS SQL link refused; broker status still active', flush=True)
        finally:
            with self.lab.connect('A') as c:
                c.execute('UPDATE fence_private.config SET anchor_conn=%s', (original,))
        self.positive(self.a)

    def test_two_lock_witnessed_contenders_have_exactly_one_cas_winner(self):
        self.restored_b()
        with self.a.anchor() as ca, self.b.anchor() as cb, self.lab.connect('C') as blocker, self.lab.connect('C') as observer:
            observer.autocommit = True
            for actor in [ca, cb]:
                actor.execute("SET LOCAL statement_timeout='5000ms'")
                actor.execute("SET LOCAL lock_timeout='3000ms'")
            blocker.execute('SELECT * FROM anchor.state FOR UPDATE')
            requests = [str(uuid4()), str(uuid4())]
            def reserve(actor, request):
                try:
                    result = actor.execute('SELECT anchor.reserve(1,%s)', (request,)).fetchone()[0]
                    actor.commit()
                    return result
                except psycopg.errors.InsufficientPrivilege:
                    actor.rollback()
                    return None
            with concurrent.futures.ThreadPoolExecutor(2) as workers:
                futures = [workers.submit(reserve, actor, req) for actor, req in zip([ca, cb], requests)]
                try:
                    deadline = time.monotonic() + 2
                    while True:
                        rows = observer.execute(
                            'SELECT pid,pg_blocking_pids(pid) FROM pg_stat_activity '
                            "WHERE pid=ANY(%s) AND wait_event_type='Lock'",
                            ([ca.info.backend_pid, cb.info.backend_pid],)).fetchall()
                        if len(rows) == 2:
                            self.assertTrue(any(blocker.info.backend_pid in ids for _, ids in rows))
                            print('S009D CAS RACE WITNESS two blocked contenders', rows, flush=True)
                            break
                        if time.monotonic() > deadline:
                            self.fail('Missing two-contender lock collision witness')
                        time.sleep(.01)
                finally:
                    blocker.rollback()
                outcomes = [f.result(timeout=4) for f in futures]
        self.assertEqual(sum(x is not None for x in outcomes), 1)
        index = next(i for i, x in enumerate(outcomes) if x is not None)
        receipt = outcomes[index]
        self.assertEqual(receipt['epoch'], 2)
        self.assertFalse(self.a.ready())
        self.assertFalse(self.b.ready())
        winner, loser = (self.a, self.b) if index == 0 else (self.b, self.a)
        winner.activate(1, receipt['request'])
        self.positive(winner)
        with self.assertRaises(FenceDenied):
            self.positive(loser)

    def test_crashed_issuer_orphan_survives_restart_without_timeout_clear(self):
        self.restored_b()
        result = self.lab.crash_worker('A', 'before_issue_commit', operation='issue')
        self.assertEqual(result.returncode, 91)
        self.lab.wait_local_quiet('A')
        self.lab.docker('kill', '--signal', 'KILL', self.lab.cfg['C']['container'])
        self.lab.docker('start', self.lab.cfg['C']['container'])
        self.lab.wait('C')
        fresh = Broker(self.lab, 'A')
        with self.lab.connect('C') as c:
            self.assertGreater(c.execute(
                "SELECT count(*) FROM anchor.operations o WHERE phase='open' AND NOT anchor.live(o)").fetchone()[0], 0)
        self.assertFalse(fresh.ready())
        with self.assertRaises(FenceDenied):
            self.positive(fresh)
        with self.assertRaises(FenceDenied):
            self.b.activate(1, str(uuid4()))
        self.assertEqual(fresh.status()['epoch'], 1)
        print('S009D ORPHAN BLOCKED WITNESS restart preserves unresolved OPEN; no clearing attempted', flush=True)

    def test_discarded_reserve_receipt_disconnect_retry_is_idempotent(self):
        request = str(uuid4())
        with self.a.anchor() as c:
            c.execute('SELECT anchor.reserve(1,%s)', (request,))
            c.commit()
            # Application deliberately discards the receipt and disconnects.
        self.assertFalse(self.a.ready())
        receipt = self.a.activate(1, request)
        self.assertEqual(receipt['epoch'], 2)
        with self.lab.connect('C') as c:
            self.assertEqual(c.execute(
                'SELECT count(*) FROM anchor.activations WHERE request=%s', (request,)).fetchone(), (1,))
        self.positive(self.a)
        print('S009D LOST RECEIPT WITNESS committed reserve + disconnect + same-request retry epoch2', flush=True)

    def test_missing_dblink_extension_denies_then_exact_reapply(self):
        def extension_catalog():
            with self.lab.connect('A') as c:
                return c.execute(
                    "SELECT p.proname,pg_get_function_identity_arguments(p.oid),pg_get_functiondef(p.oid),"
                    "p.proacl::text,p.proowner::regrole::text FROM pg_depend d "
                    "JOIN pg_extension e ON e.oid=d.refobjid AND d.refclassid='pg_extension'::regclass "
                    "JOIN pg_proc p ON p.oid=d.objid AND d.classid='pg_proc'::regclass "
                    "WHERE e.extname='dblink' ORDER BY 1,2").fetchall()
        before = extension_catalog()
        self.assertGreater(len(before), 0)
        try:
            with self.lab.connect('A') as c:
                c.execute('DROP EXTENSION dblink')
            self.assertFalse(self.a.ready())
            with self.assertRaises(FenceDenied):
                self.positive(self.a)
        finally:
            with self.lab.connect('A') as c:
                c.execute('CREATE EXTENSION dblink WITH SCHEMA public')
            self.assertEqual(extension_catalog(), before)
        self.positive(self.a)
        print('S009D EXTENSION WITNESS absent dblink denies; definitions/owners/ACL restored', flush=True)
