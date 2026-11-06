"""Q_SURVIVAL_ONLY. Mandatory application admission preflight, no legacy bypass."""
import unittest
from h_quorum.integration_lab import IntegrationLab

class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lab=IntegrationLab()
    @classmethod
    def tearDownClass(cls):cls.lab.close()
    def test_00_mandatory_guard_before_application_admission(self):
        installed=self.lab.reset()
        self.assertTrue(installed,'Mandatory H guard admission is not implemented')
        with self.lab.connect() as c:
            self.assertIsNotNone(c.execute("SELECT to_regclass('h_guard.config')").fetchone()[0])
            self.assertEqual(c.execute("SELECT rolcanlogin FROM pg_roles WHERE rolname IN ('cac_ctx_runtime','cac_ctx_issuer') ORDER BY rolname").fetchall(),[(True,),(True,)])
