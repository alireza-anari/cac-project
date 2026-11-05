"""Shared disposable authority test setup, not a runtime recovery API."""
import unittest
from uuid import uuid4

from recovery_fencing.broker import Broker
from recovery_fencing.lab import Lab, S1


class AuthorityFixture(unittest.TestCase):
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
        self.a.activate(0, str(uuid4()))

    def positive(self, broker):
        with broker.runtime() as g:
            h = g.challenge()
            g.install(broker.issue(h))
            self.assertEqual(g.records(), [S1])

    def restored_b(self):
        self.lab.restore()
        self.lab.bind('B')
