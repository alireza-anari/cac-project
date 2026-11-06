"""W_ORACLE_ASSUMED. Real PostgreSQL contract, not real W-root evidence."""
import unittest
from uuid import uuid4

from w_oracle.lab import OracleLab, BANNER


class OracleContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lab = OracleLab()

    @classmethod
    def tearDownClass(cls):
        cls.lab.close()

    def setUp(self):
        self.lab.reset()
        print(BANNER, 'independent-test namespace', self.lab.namespace, flush=True)

    def test_initial_activation_and_stale_cas_denial(self):
        import psycopg
        request = str(uuid4())
        with self.lab.connect('A') as c:
            result = c.execute('SELECT w.reserve(0,%s)', (request,)).fetchone()[0]
        self.assertEqual(result['epoch'], 1)
        with self.lab.connect('B') as c:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                c.execute('SELECT w.reserve(0,%s)', (str(uuid4()),))
