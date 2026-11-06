"""Q_SURVIVAL_ONLY. Mandatory application admission preflight, no legacy bypass."""
import unittest
from uuid import uuid4
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
            guard_measure=c.execute('SELECT h_guard.measure()').fetchone()[0]
            self.assertEqual(self.lab.measure('A'),guard_measure,'External controller and live SQL guard catalog measurements differ')
            self.assertEqual(c.execute("SELECT rolcanlogin FROM pg_roles WHERE rolname IN ('cac_ctx_runtime','cac_ctx_issuer') ORDER BY rolname").fetchall(),[(True,),(True,)])

    def broker(self):
        try:from h_quorum.broker import Broker
        except ModuleNotFoundError:self.fail('Trusted H transaction coordinator is not implemented')
        return Broker(self.lab)
    def scope(self,a,g,action='read',body=None):
        from recovery_fencing.lab import S1
        token=a.issue(g.challenge(),action=action,body=body or {})
        g.install(token);self.assertEqual(g.records(),[S1]);return token
    def test_01_actual_guarded_scoped_read_and_body_bound_write(self):
        from recovery_fencing.lab import S1
        self.lab.reset();a=self.broker();a.activate(0,str(uuid4()))
        self.assertTrue(a.ready())
        with a.runtime() as g:self.scope(a,g)
        body={'body':'synthetic-h-updated'}
        with a.runtime(action='probe',body=body) as g:
            self.scope(a,g,'probe',body)
            self.assertEqual(g.c.execute('UPDATE poc.records SET body=%s WHERE store=%s',(body['body'],S1)).rowcount,1)
        with self.lab.connect() as c:
            self.assertEqual(c.execute('SELECT body FROM poc.records WHERE store=%s',(S1,)).fetchone(),(body['body'],))
        self.assertEqual(a.inspect()['open'],0)
    def test_02_direct_sql_and_all_private_legacy_entries_deny(self):
        import psycopg
        self.lab.reset();a=self.broker();a.activate(0,str(uuid4()))
        with a.runtime() as g:self.scope(a,g)
        for role,query in [('cac_ctx_runtime','SELECT poc.challenge()'),('cac_ctx_runtime','SELECT store FROM poc.records'),('cac_ctx_issuer','SELECT poc.issue(NULL,NULL,NULL,NULL,NULL,NULL)'),('cac_ctx_runtime','SELECT h_guard.verify_c()'),('cac_ctx_runtime','SELECT h_guard.c_is_ready()'),('cac_ctx_issuer','SELECT h_guard.issue_c(NULL,NULL,NULL,NULL,NULL,NULL)'),('cac_ctx_runtime','SELECT fence_private.check_guard_c()'),('cac_ctx_runtime','SELECT poc_private.verify_unfenced()')]:
            with self.subTest(role=role,query=query):
                with self.lab.connect('A',role) as c:
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute(query)
    def test_03_read_context_cannot_write_and_probe_cannot_change_body(self):
        import psycopg
        from recovery_fencing.lab import S1
        self.lab.reset();a=self.broker();a.activate(0,str(uuid4()))
        with a.runtime() as g:
            self.scope(a,g)
            self.assertEqual(g.c.execute('UPDATE poc.records SET body=%s WHERE store=%s',('synthetic-forbidden',S1)).rowcount,0)
        body={'body':'synthetic-allowed'}
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with a.runtime(action='probe',body=body) as g:
                self.scope(a,g,'probe',body)
                g.c.execute('UPDATE poc.records SET body=%s WHERE store=%s',('synthetic-forbidden',S1))
        with self.lab.connect() as c:self.assertEqual(c.execute('SELECT body FROM poc.records WHERE store=%s',(S1,)).fetchone(),('synthetic',))
        self.assertEqual(a.inspect()['unknown'],1)
    def test_04_positive_exact_abort_closes_but_replaced_transaction_does_not(self):
        from h_quorum.common import Denied
        self.lab.reset();a=self.broker();a.activate(0,str(uuid4()))
        with self.assertRaisesRegex(ValueError,'synthetic known abort'):
            with a.runtime() as g:
                self.scope(a,g);raise ValueError('synthetic known abort')
        self.assertEqual(a.inspect()['open'],0)
        with self.assertRaises(Denied):
            with a.runtime() as g:
                self.scope(a,g);g.c.commit();g.c.execute('SELECT txid_current()');raise ValueError('synthetic replaced transaction')
        self.assertEqual(a.inspect()['unknown'],1)

    def test_05_external_manifest_covers_nonview_rewrite_rules(self):
        self.lab.reset();a=self.broker();a.activate(0,str(uuid4()))
        with a.runtime() as g:self.scope(a,g)
        expected=self.lab.rootcfg['approved_manifest']
        self.lab.quarantine('A')
        try:
            with self.lab.connect() as c:c.execute('CREATE RULE h_rewrite_probe AS ON UPDATE TO poc.records DO INSTEAD NOTHING')
            self.assertNotEqual(self.lab.measure('A'),expected,'External manifest ignored non-view DML rewrite rule')
            with self.lab.connect() as c:self.assertEqual(c.execute("SELECT rolcanlogin FROM pg_roles WHERE rolname IN ('cac_ctx_runtime','cac_ctx_issuer') ORDER BY rolname").fetchall(),[(False,),(False,)])
        finally:
            with self.lab.connect() as c:c.execute('DROP RULE IF EXISTS h_rewrite_probe ON poc.records')
        self.assertEqual(self.lab.measure('A'),expected,'Rule probe did not restore exact catalog manifest')
