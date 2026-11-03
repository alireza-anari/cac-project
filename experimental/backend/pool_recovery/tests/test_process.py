import unittest
from pool_recovery.lab import Lab

class ProcessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.lab = Lab()
    @classmethod
    def tearDownClass(cls): cls.lab.close()

    def test_distinct_uid_credentials_and_scoped_read(self):
        with self.lab.worker() as w:
            r = w.call('isolation')
            self.assertTrue(r['different_uid'])
            self.assertTrue(r['issuer_file_denied'])
            self.assertTrue(r['issuer_proc_denied'])
            self.assertEqual(r['keys'], ['connection', 'password', 'proof', 'role', 'socket'])
            self.assertEqual(w.call('scope'), [self.lab.S1])

    def setUp(self):
        from context_poc.harness import seed
        seed()

    def test_runtime_sql_and_role_escalation_denied(self):
        queries = ['SELECT * FROM poc_private.keys', 'SELECT * FROM poc_private.ledger',
                   'SET ROLE cac_ctx_issuer', 'SET ROLE cac_ctx_guard',
                   "SELECT poc_private.pack('{}','context')", 'ALTER TABLE poc.records DISABLE ROW LEVEL SECURITY',
                   "SELECT poc.issue('x','x',NULL,NULL,NULL,NULL)"]
        for q in queries:
            with self.subTest(q=q), self.lab.worker() as w: w.deny('sql', q=q)

    def test_malicious_rpc_and_stolen_proof_wrong_authority(self):
        with self.lab.worker() as w:
            h = w.call('challenge')
            r = w.call('request', h=h)
            mutations = [dict(r, action='sign'), dict(r, sql='SELECT 1'), dict(r, target=self.lab.P2),
                         dict(r, store=self.lab.S3), dict(r, proof='stolen-invalid'), dict(r, body=None),
                         dict(r, store='not-uuid'), dict(r, challenge='x'*16001)]
            from context_poc.harness import CFG
            mutations.append(dict(r, proof=CFG['poc_proofs'][1]))
            for bad in mutations: self.assertEqual(w.call('rpc', request=bad), {'ok':False,'error':'denied'})
            import json
            duplicate = json.dumps(r)[:-1]+',"action":"read"}\n'
            self.assertEqual(w.call('raw', raw=duplicate), {'ok':False,'error':'denied'})
            self.assertEqual(w.call('raw', raw='x'*24001+'\n'), {'ok':False,'error':'denied'})
            self.assertEqual(w.call('scope', h=h), [self.lab.S1])

    def test_kernel_peer_rejects_orchestrator(self):
        import socket, json
        with socket.socket(socket.AF_UNIX) as s:
            s.connect(str(self.lab.directory/'issuer.sock'))
            # Root test orchestrator has NOT the permitted runtime UID.
            self.assertEqual(json.loads(s.recv(1024)), {'ok':False,'error':'denied'})

    def test_deferred_commit_failure_never_returns_token(self):
        from context_poc.harness import connect
        with connect('postgres') as r:
            r.execute("CREATE FUNCTION poc_private.fail_commit_b() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'synthetic deferred failure'; END $$")
            r.execute('CREATE CONSTRAINT TRIGGER fail_commit_b AFTER INSERT ON poc_private.ledger DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION poc_private.fail_commit_b()')
        try:
            with self.lab.worker() as w:
                self.assertEqual(w.call('issue'), {'ok':False,'error':'denied'})
                w.deny()
            with connect('postgres') as r: self.assertEqual(r.execute('SELECT count(*) FROM poc_private.ledger').fetchone(), (0,))
        finally:
            with connect('postgres') as r: r.execute('DROP TRIGGER fail_commit_b ON poc_private.ledger; DROP FUNCTION poc_private.fail_commit_b()')
        with self.lab.worker() as w: self.assertEqual(w.call('scope'), [self.lab.S1])

    def test_issuer_process_unavailable_no_fallback(self):
        # SIGSTOP makes service unavailable without replacing its credentials.
        import os, signal
        os.kill(self.lab.issuer.pid, signal.SIGSTOP)
        try:
            with self.lab.worker() as w:
                self.assertFalse(w.reply('issue')['ok'])
                w.deny()
        finally: os.kill(self.lab.issuer.pid, signal.SIGCONT)
