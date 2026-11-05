"""Real PostgreSQL regression probes; assertions are shared by GREEN and RED."""
import unittest
from uuid import uuid4

import psycopg

from recovery_fencing.broker import Broker, FenceDenied
from recovery_fencing.lab import Lab
from recovery_proof.sensitivity import weaken


class SecurityTargets(unittest.TestCase):
    mutation = None

    @classmethod
    def setUpClass(cls):
        cls.lab = Lab()
        cls.lab.install_roles()

    @classmethod
    def tearDownClass(cls):
        cls.lab.close()

    def setUp(self):
        self.lab.reset()
        self.a = Broker(self.lab, 'A')
        self.b = Broker(self.lab, 'B')
        if self.mutation:
            self.enterContext(weaken(self.lab, self.mutation))

    def activate(self):
        self.assertEqual(self.a.activate(0, str(uuid4()))['epoch'], 1)

    def test_stale_expected_epoch_cannot_reserve(self):
        # Removing reserve's expected-epoch check must break this assertion.
        self.activate()
        with self.assertRaises(FenceDenied):
            self.b.reserve(0, str(uuid4()))
        self.assertEqual(self.a.status()['epoch'], 1)
        self.assertTrue(self.a.ready())

    def test_sql_online_guard_requires_live_ticket(self):
        # Removing check_guard's online attestation must expose raw challenge.
        self.activate()
        with self.a.runtime() as gate:
            self.assertTrue(gate.challenge())
        with self.lab.connect('A', 'cac_ctx_runtime') as raw:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                raw.execute('SELECT poc.challenge()')

    def test_orphan_open_blocks_reservation(self):
        # Removing reserve's OPEN predicate must permit this forbidden takeover.
        self.activate()
        self.lab.restore()
        self.lab.bind('B')
        crashed = self.lab.crash_worker('A', 'before_issue_commit', operation='issue')
        self.assertEqual(crashed.returncode, 91)
        self.lab.wait_local_quiet('A')
        with self.lab.connect('C') as c:
            count = c.execute(
                "SELECT count(*) FROM anchor.operations o "
                "WHERE phase='open' AND NOT anchor.live(o)").fetchone()[0]
            self.assertGreater(count, 0)
        with self.assertRaises(FenceDenied):
            self.b.reserve(1, str(uuid4()))
        self.assertEqual(self.a.status()['epoch'], 1)
        self.assertFalse(self.a.ready())
        self.assertFalse(self.b.ready())
