"""Three original route observations; no skipped or invented route coverage."""
import importlib.util
import os
import unittest


class LegacyRouteAuditTests(unittest.TestCase):
    def observe(self, case):
        self.assertIsNotNone(importlib.util.find_spec('h_quorum.p_audit'),
                             'P executable real-route diagnostic is missing')
        self.assertEqual(os.environ['CAC_P_CASE'], case)
        from h_quorum.p_audit import run_case
        run_case(self, case)

    def test_stale_issuer_policy_after_retirement(self):
        self.observe('P_STALE_ISSUER_POLICY_AFTER_RETIREMENT')

    def test_direct_sql_old_principal(self):
        self.observe('P_DIRECT_SQL_OLD_PRINCIPAL')

    def test_pool_reused_backend_old_context(self):
        self.observe('P_POOL_REUSED_BACKEND_OLD_CONTEXT')
