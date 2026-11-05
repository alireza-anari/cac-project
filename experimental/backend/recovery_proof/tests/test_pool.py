"""C-fenced SQL through an actual size-one transaction pool, no SQL mocks."""
import concurrent.futures
import time
import unittest
from uuid import uuid4

import psycopg

from recovery_fencing.broker import Broker, FenceDenied
from recovery_fencing.lab import Lab, S1
from recovery_proof.pool_lab import Pool, PoolBroker


class PoolFencingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lab = Lab()
        cls.lab.install_roles()

    @classmethod
    def tearDownClass(cls):
        cls.lab.close()

    def setUp(self):
        self.lab.reset()
        self.pool = Pool(self.lab)
        self.addCleanup(self.pool.close)
        self.a = PoolBroker(self.lab, self.pool)
        self.b = Broker(self.lab, 'B')
        self.a.activate(0, str(uuid4()))

    def witness(self, c, label):
        user, role, pid, tx = c.execute(
            'SELECT session_user,current_user,pg_backend_pid(),txid_current()::text').fetchone()
        self.assertEqual((user, role), ('cac_ctx_runtime', 'cac_ctx_runtime'))
        print('S009D POOL WITNESS', label, 'pid', pid, 'fullxid', tx, flush=True)
        return pid, tx

    def scope(self, gate):
        h = gate.challenge()
        token = self.a.issue(h)
        gate.install(token)
        self.assertEqual(gate.records(), [S1])
        return token

    def no_open(self):
        with self.lab.connect('C') as c:
            self.assertEqual(c.execute(
                "SELECT count(*) FROM anchor.operations WHERE phase='open'").fetchone(), (0,))

    def takeover(self):
        self.lab.restore()
        self.lab.bind('B')
        self.assertEqual(self.b.activate(1, str(uuid4()))['epoch'], 2)
        self.assertFalse(self.a.ready())
        with self.b.runtime() as g:
            h = g.challenge()
            g.install(self.b.issue(h))
            self.assertEqual(g.records(), [S1])

    def stale_on_same_backend(self, old, token, ticket, label):
        with self.pool.connect() as raw:
            current = self.witness(raw, label)
            self.assertEqual(current[0], old[0])
            self.assertNotEqual(current[1], old[1])
            raw.execute("SELECT set_config('cac.poc_context',%s,true)", (token,))
            raw.execute("SELECT set_config('cac.fence_ticket',%s,true)", (ticket,))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                raw.execute('SELECT store FROM poc.records')
            raw.rollback()
        return current

    def test_commit_hostile_session_state_and_takeover_reuse(self):
        with self.a.runtime() as g:
            token = self.scope(g)
            old = self.witness(g.c, 'committed-valid-context')
            ticket = g.ticket
            g.c.execute("SELECT set_config('cac.poc_context',%s,false)", (token,))
            g.c.execute("SELECT set_config('cac.fence_ticket',%s,false)", (ticket,))
        with self.pool.connect() as raw:
            reused = self.witness(raw, 'hostile-session-reuse')
            self.assertEqual(reused[0], old[0])
            self.assertNotEqual(reused[1], old[1])
            self.assertTrue(raw.execute(
                "SELECT current_setting('cac.poc_context',true)").fetchone()[0] == token,
                'Expected deliberately persistent hostile session context')
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                raw.execute('SELECT store FROM poc.records')
            raw.rollback()
        self.no_open()
        self.takeover()
        self.stale_on_same_backend(old, token, ticket, 'post-takeover-session-reuse')

    def test_rollback_closes_open_then_same_backend_denies_old_context(self):
        with self.assertRaises(psycopg.errors.DivisionByZero):
            with self.a.runtime() as g:
                token = self.scope(g)
                old = self.witness(g.c, 'before-rollback')
                ticket = g.ticket
                g.c.execute('SELECT 1/0')
        self.no_open()
        self.stale_on_same_backend(old, token, ticket, 'after-rollback')
        self.takeover()
        self.stale_on_same_backend(old, token, ticket, 'rollback-after-takeover')

    def test_real_query_cancel_rolls_back_gate_and_reuses_backend(self):
        with self.assertRaises(psycopg.errors.QueryCanceled) as cancelled:
            with self.a.runtime() as g:
                token = self.scope(g)
                old = self.witness(g.c, 'before-cancel')
                ticket = g.ticket
                with concurrent.futures.ThreadPoolExecutor(1) as workers:
                    future = workers.submit(g.c.execute, 'SELECT pg_sleep(10)')
                    with self.lab.connect('A') as observer:
                        observer.autocommit = True
                        deadline = time.monotonic() + 2
                        while True:
                            row = observer.execute(
                                'SELECT wait_event FROM pg_stat_activity WHERE pid=%s',
                                (old[0],)).fetchone()
                            if row == ('PgSleep',):
                                break
                            if time.monotonic() > deadline:
                                self.fail('Missing actual cancellation wait witness')
                            time.sleep(.01)
                        self.assertEqual(observer.execute(
                            'SELECT pg_cancel_backend(%s)', (old[0],)).fetchone(), (True,))
                        print('S009D CANCEL WITNESS PgSleep -> pg_cancel_backend', old[0], flush=True)
                    future.result(timeout=3)
        self.assertEqual(cancelled.exception.diag.message_primary,
                         'canceling statement due to user request')
        print('S009D CANCEL DIAGNOSTIC user request (not statement timeout)', flush=True)
        self.no_open()
        self.stale_on_same_backend(old, token, ticket, 'after-cancel')
        self.takeover()
        self.stale_on_same_backend(old, token, ticket, 'cancel-after-takeover')

    def test_blocked_takeover_then_reused_backend_fails_closed(self):
        self.lab.restore()
        self.lab.bind('B')
        with self.a.runtime() as g:
            token = self.scope(g)
            old = self.witness(g.c, 'held-during-takeover')
            ticket = g.ticket
            with self.lab.connect('C') as observer:
                observer.autocommit = True
                # Force a fresh observer snapshot before launching the contender.
                self.assertEqual(observer.execute(
                    "SELECT pid FROM pg_stat_activity WHERE usename='cac_anchor_b' "
                    "AND wait_event_type='Lock'").fetchall(), [])
                with concurrent.futures.ThreadPoolExecutor(1) as workers:
                    future = workers.submit(self.b.reserve, 1, str(uuid4()))
                    deadline = time.monotonic() + 2
                    while True:
                        rows = observer.execute(
                            "SELECT pid,pg_blocking_pids(pid) FROM pg_stat_activity "
                            "WHERE usename='cac_anchor_b' AND wait_event_type='Lock'").fetchall()
                        if any(g.a.info.backend_pid in blockers for _, blockers in rows):
                            print('S009D TAKEOVER LOCK WITNESS', rows, flush=True)
                            break
                        if time.monotonic() > deadline:
                            self.fail('Missing takeover lock witness')
                        time.sleep(.01)
                    with self.assertRaises(FenceDenied):
                        future.result(timeout=3)
        self.no_open()
        self.assertEqual(self.b.activate(1, str(uuid4()))['epoch'], 2)
        self.stale_on_same_backend(old, token, ticket, 'held-transaction-after-takeover')
        self.assertFalse(self.a.ready())
        self.assertTrue(self.b.ready())
