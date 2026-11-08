"""S0-09K: actual policy retirement; current non-restored quorum required."""
import unittest
import concurrent.futures
import hashlib
import hmac
import json
import secrets
import time
from uuid import uuid4
import psycopg
from h_quorum.authority import Root
from h_quorum.broker import Broker
from h_quorum.common import BANNER, Denied
from h_quorum.integration_lab import IntegrationLab
from h_quorum.rpc import Client
from recovery_fencing.lab import S1
from h_quorum.common import unb64


class PolicyRetirementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.lab = IntegrationLab()
    @classmethod
    def tearDownClass(cls): cls.lab.close()

    def setUp(self):
        self.lab.reset()
        self.a = Broker(self.lab)
        self.a.activate(0, str(uuid4()))
        self.control = Client(self.lab.rootcfg, 'control', self.lab.namespace)

    def state(self):
        return Root(self.lab.rootcfg).read(self.lab.namespace, True)

    def scope(self, gate, broker=None, action='read', body=None):
        broker = broker or self.a
        gate.install(broker.issue(gate.challenge(), action=action, body=body or {}))
        self.assertEqual(gate.records(), [S1])

    def retire(self, request=None):
        args = dict(expected=1, new=2, request=request or str(uuid4()))
        try:
            result = self.control.call('retire_policy', args)
        except Denied:
            self.fail('Actual Root policy retirement transaction is not implemented')
        self.lab.replay()
        return result, args

    def adopt(self, node='A'):
        from h_quorum.retirement import adopt_policy
        return adopt_policy(self.lab, node)

    def positive2(self):
        self.assertEqual(self.control.call('status')['policy'], 2)
        self.assertTrue(self.a.ready())
        with self.a.runtime() as gate:
            self.assertEqual(gate.binding['policy'], 2)
            self.scope(gate)

    def active_args(self, connection, version):
        pid, tx, sid = connection.execute('SELECT pg_backend_pid(),txid_current()::text,fence.system_id()').fetchone()
        actor = self.lab.actors['A']
        with self.lab.connect() as observer:
            projection = observer.execute('SELECT h_guard.w_status()').fetchone()[0]
        return dict(sid=sid, pid=pid, tx=tx, kind='runtime', login='cac_ctx_runtime', digest='',
                    incarnation=actor['incarnation'], manifest=actor['manifest'], policy=version,
                    ticket='', root_id=self.lab.rootcfg['root_id'], epoch=1,
                    nonce=secrets.token_hex(32), mode='active', projection=projection)

    def test_00_real_policy_transition_is_atomic_not_signer_rotation(self):
        self.lab.r_evidence('K healthy current policy1')
        with self.a.runtime() as gate:
            self.scope(gate)
        before, _, _ = self.state()
        self.assertEqual((before['policy'], before['signer_epoch']), (1, 1))
        receipt, args = self.retire()
        after, revision, rows = self.state()
        self.assertEqual((after['policy'], after['signer_epoch']), (2, 1))
        self.assertEqual(after['ops'], before['ops'])
        self.assertEqual(after['seq'], before['seq'] + 1)
        self.assertEqual(receipt['revision'], revision)
        self.assertEqual(int(rows[-1]['mod_revision']), revision)
        from h_quorum.common import unb64
        import json
        entry = json.loads(unb64(rows[-1]['value']))
        self.assertEqual(entry['command']['action'], 'retire_policy')
        self.assertEqual(entry['command']['request'], args['request'])
        self.lab.r_evidence('K policy2 majority-committed with unchanged signer')
        print(BANNER, 'K REAL POLICY RETIREMENT', receipt,
              'same signer; full operation state preserved; one journal/state MVCC', flush=True)

    def test_01_policy2_positive_and_stale_sql_and_new_admit_denied(self):
        with self.a.runtime() as gate:
            self.scope(gate)
        self.retire()
        self.assertFalse(self.a.ready(), 'Old SQL policy config remained ready after retirement')
        with self.assertRaises(Denied):
            with self.a.runtime(): self.fail('Stale policy runtime entered')
        with self.lab.connect('A', 'cac_ctx_runtime') as connection:
            self.assertEqual(connection.execute('SELECT fence.is_ready()').fetchone(), (False,))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute('SELECT store FROM poc.records')
            connection.rollback()
        self.adopt()
        with self.a.runtime() as gate:
            self.scope(gate)
            old = dict(gate.binding, policy=1, request=str(uuid4()), operation=str(uuid4()))
            with self.assertRaises(Denied): self.a.command('admit', old)
        self.positive2()
        print(BANNER, 'K stale current-guard SQL readiness and ADMIT denied; paired policy2 RLS positive', flush=True)

    def test_02_policy_retirement_requires_control(self):
        before = self.control.call('status')
        with self.assertRaises(Denied, msg='Policy retirement accepted a non-control role'):
            Client(self.lab.rootcfg, 'A_coord', self.lab.namespace).call(
                'retire_policy', dict(expected=1, new=2, request=str(uuid4())))
            self.assertEqual(self.control.call('status')['policy'], 2)
            print(BANNER, 'UNSAFE K POLICY AUTHORITY WITNESS coordinator committed policy2', flush=True)
        self.assertEqual(self.control.call('status'), before)
        self.retire(); self.adopt(); self.positive2()

    def test_03_invalid_backwards_future_and_duplicate_mutations(self):
        before = self.control.call('status')
        request = str(uuid4())
        for role, args in [
            ('A_check', dict(expected=1, new=2, request=request)),
            ('control', dict(expected=True, new=2, request=request)),
            ('control', dict(expected=1, new=True, request=request)),
            ('control', dict(expected=1, new=1, request=request)),
            ('control', dict(expected=1, new=0, request=request)),
            ('control', dict(expected=0, new=2, request=request)),
            ('control', dict(expected=1, new=3, request=request)),
        ]:
            with self.subTest(role=role, args=args):
                with self.assertRaises(Denied): Client(self.lab.rootcfg, role, self.lab.namespace).call('retire_policy', args)
                self.assertEqual(self.control.call('status'), before)
        receipt, args = self.retire(request)
        committed = self.control.call('status')
        self.assertEqual(self.control.call('retire_policy', args), receipt)
        self.assertEqual(self.control.call('status'), committed, 'Exact retry added another journal entry')
        for invalid in (dict(args, request=str(uuid4())), dict(args, expected=2, new=1), dict(args, expected=2, new=3)):
            with self.assertRaises(Denied): self.control.call('retire_policy', invalid)
        self.adopt(); self.positive2()

    def test_04_two_control_cas_contenders_one_committed_cut(self):
        before = self.control.call('status')
        def attempt(_):
            try:
                return self.control.call('retire_policy', dict(expected=1, new=2, request=str(uuid4())))
            except Denied: return None
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            results = list(pool.map(attempt, range(2)))
        self.assertEqual(sum(r is not None for r in results), 1)
        state, revision, rows = self.state()
        self.assertEqual(state['seq'], before['seq']+1)
        self.assertEqual((state['policy'], int(rows[-1]['mod_revision'])), (2, revision))
        self.assertEqual(len(state['retired_policies']), 1)
        self.lab.replay(); self.adopt(); self.positive2()
        print(BANNER, 'K actual concurrent control CAS exactly one policy cut revision', revision, flush=True)

    def test_05_cryptographically_valid_old_transcript_and_delayed_reply_denied(self):
        checker = Client(self.lab.rootcfg, 'A_check', self.lab.namespace)
        with self.lab.connect('A', 'cac_ctx_runtime') as connection:
            args = self.active_args(connection, 1)
            answer = checker.call('guard', args)['answer']
            self.assertTrue(checker.call('verify', dict(args, answer=answer))['valid'])
            encoded, signature = answer.split('.')
            key = bytes.fromhex(self.lab.rootcfg['signing_keys']['1'])
            self.assertTrue(hmac.compare_digest(signature, hmac.new(key, bytes.fromhex(encoded), hashlib.sha256).hexdigest()))
            self.retire()
            self.assertEqual(self.control.call('status')['signer_epoch'], 1)
            with self.assertRaises(Denied): checker.call('verify', dict(args, answer=answer))
            with self.assertRaises(Denied): checker.call('guard', args)
            fresh = self.active_args(connection, 2)
            with self.assertRaises(Denied): checker.call('verify', dict(fresh, answer=answer))
            self.assertTrue(checker.call('verify', dict(fresh, answer=checker.call('guard', fresh)['answer']))['valid'])
        self.adopt(); self.positive2()
        print(BANNER, 'K old active transcript valid HMAC under still-current signer1; current policy2 denies replay/issuance', flush=True)

    def test_06_pregrant_actual_commit_blocks_successor_until_known_close(self):
        self.lab.restore(); successor = Broker(self.lab, 'B')
        body = {'body': 'synthetic-k-late-commit'}
        with self.a.runtime(action='probe', body=body) as gate:
            self.scope(gate, action='probe', body=body)
            gate.c.execute('UPDATE poc.records SET body=%s WHERE store=%s', (body['body'], S1))
            before = self.state()[0]['ops']
            self.retire()
            self.assertEqual(self.state()[0]['ops'], before)
            with self.assertRaises(Denied): self.adopt()
            with self.assertRaises(Denied):
                self.a.command('admit', dict(gate.binding, policy=2, request=str(uuid4()), operation=str(uuid4())))
            with self.assertRaises(Denied): successor.activate(1, str(uuid4()))
            self.assertFalse(successor.ready())
            self.assertEqual(gate.records(), [S1], 'Pre-retirement grant lost guarded continuation')
            def hook(label):
                if label == 'after_local_commit_before_close':
                    with self.assertRaises(Denied): successor.activate(1, str(uuid4()))
                    self.assertEqual(self.a.inspect()['open'], 1)
            self.a.hook = hook
        self.a.hook = lambda label: None
        self.assertEqual(self.state()[0]['ops'][gate.operation]['phase'], 'CLOSED_COMMIT')
        self.lab.restore(); successor = Broker(self.lab, 'B'); successor.activate(1, str(uuid4()))
        with successor.runtime() as new:
            self.assertEqual(new.binding['policy'], 2)
            self.scope(new, broker=successor)
            self.assertEqual(new.c.execute('SELECT body FROM poc.records WHERE store=%s', (S1,)).fetchone(), (body['body'],))
        print(BANNER, 'K real old protected COMMIT after retirement; successor blocked before/after COMMIT until authoritative CLOSE; policy2 B positive', flush=True)

    def test_07_known_abort_can_close_old_policy_without_unknown_clearing(self):
        with self.assertRaisesRegex(ValueError, 'synthetic known K abort'):
            with self.a.runtime() as gate:
                self.scope(gate); self.retire()
                raise ValueError('synthetic known K abort')
        self.assertEqual(self.state()[0]['ops'][gate.operation]['phase'], 'CLOSED_ABORT')
        self.assertEqual(self.a.inspect()['unknown'], 0)
        self.adopt(); self.positive2()

    def test_08_ungranted_old_first_use_denied_unknown_never_adopted(self):
        self.lab.restore(); successor = Broker(self.lab, 'B')
        def hook(label):
            if label == 'after_durable_open': self.retire()
        self.a.hook = hook
        gate = self.a.runtime()
        with self.assertRaises(Denied):
            with gate: self.fail('Retired ungranted operation reached protected SQL')
        self.a.hook = lambda label: None
        self.assertEqual(self.a.inspect()['unknown'], 1)
        self.assertFalse(self.state()[0]['ops'][gate.operation]['granted'])
        with self.assertRaises(Denied): self.a.command('close', dict(gate.binding, ticket=gate.ticket, outcome='abort'))
        with self.assertRaises(Denied): self.adopt()
        with self.assertRaises(Denied): successor.activate(1, str(uuid4()))
        self.assertEqual(self.a.inspect()['unknown'], 1)

    def test_09_lost_actual_policy_commit_ack_exact_retry_resolves_once(self):
        from h_quorum.reply_loss import ReplyLoss
        proxy = ReplyLoss(self.lab.rootcfg, 'retire_policy'); self.addCleanup(proxy.close)
        args = dict(expected=1, new=2, request=str(uuid4()))
        before = self.control.call('status')
        with self.assertRaises(Denied): Client(proxy.cfg, 'control', self.lab.namespace).call('retire_policy', args)
        self.assertEqual(proxy.seen, [dict(action='retire_policy', namespace=self.lab.namespace, upstream_ack=True)])
        committed = self.control.call('status')
        self.assertEqual((committed['policy'], committed['seq']), (2, before['seq']+1))
        recovered = self.control.call('retire_policy', args)
        self.assertEqual(self.control.call('retire_policy', args), recovered)
        self.assertEqual(self.control.call('status'), committed)
        self.assertFalse(self.a.ready())
        self.lab.replay(); self.adopt(); self.positive2()
        print(BANNER, 'K actual committed policy2 TLS reply dropped; current exact request recovery no second transition', recovered, flush=True)

    def test_10_stale_read_before_admit_is_denied_without_new_open(self):
        calls = []
        def hook(label):
            if label == 'before_open_commit':
                calls.append(label); self.retire()
        self.a.hook = hook
        with self.assertRaises(Denied):
            with self.a.runtime(): self.fail('Stale policy snapshot obtained new OPEN')
        self.a.hook = lambda label: None
        self.assertEqual(calls, ['before_open_commit'])
        self.assertEqual((self.a.inspect()['open'], self.a.inspect()['unknown']), (0, 0))
        self.adopt(); self.positive2()

    def test_11_reused_pgbouncer_backend_old_context_denied_policy2_positive(self):
        from recovery_proof.pool_lab import Pool
        pool = Pool(self.lab); self.addCleanup(pool.close)
        self.a.pool = pool
        with self.a.runtime() as gate:
            token = self.a.issue(gate.challenge()); gate.install(token)
            self.assertEqual(gate.records(), [S1])
            pid, tx = gate.pid, gate.tx
            for name, value in [('cac.poc_context', token), ('cac.h_ticket', gate.ticket), ('cac.h_intent', gate.binding['digest'])]:
                gate.c.execute('SELECT set_config(%s,%s,false)', (name, value))
        self.retire(); self.adopt()
        with pool.connect() as connection:
            new_pid, new_tx = connection.execute('SELECT pg_backend_pid(),txid_current()::text').fetchone()
            self.assertEqual(new_pid, pid); self.assertNotEqual(new_tx, tx)
            self.assertEqual(connection.execute("SELECT current_setting('cac.poc_context',true)").fetchone()[0], token)
            with self.assertRaises(psycopg.errors.InsufficientPrivilege): connection.execute('SELECT store FROM poc.records')
            connection.rollback()
        with self.a.runtime() as current:
            self.assertEqual(current.pid, pid); self.assertNotEqual(current.tx, tx)
            self.assertEqual(current.binding['policy'], 2); self.scope(current)
            print(BANNER, 'K PgBouncer same backend PID', pid, 'old xid', tx, 'new xid', current.tx,
                  'old context denied; policy2 scoped SQL positive', flush=True)

    def test_12_old_verifier_catalog_remains_quarantined_under_policy2(self):
        with self.a.runtime() as gate: self.scope(gate)
        self.retire(); self.adopt(); self.positive2()
        self.lab.quarantine('A'); self.lab.down('A')
        with self.assertRaisesRegex(AssertionError, 'External verifier manifest mismatch'):
            self.lab.admit('A')
        with self.lab.connect() as observer:
            self.assertEqual(observer.execute("SELECT rolcanlogin FROM pg_roles WHERE rolname IN ('cac_ctx_runtime','cac_ctx_issuer') ORDER BY rolname").fetchall(), [(False,), (False,)])
        self.assertEqual(self.control.call('status')['policy'], 2)
        print(BANNER, 'K actual old SQL overlay rejected by independently pinned catalog; NOLOGIN retained', flush=True)

    def test_13_actual_cancel_after_retirement_retains_unknown_on_reused_backend(self):
        from recovery_proof.pool_lab import Pool
        pool = Pool(self.lab); self.addCleanup(pool.close); self.a.pool = pool
        gate = self.a.runtime()
        with self.assertRaises(psycopg.errors.QueryCanceled):
            with gate:
                self.scope(gate)
                with concurrent.futures.ThreadPoolExecutor(1) as workers:
                    future = workers.submit(gate.c.execute, 'SELECT pg_sleep(20)')
                    with self.lab.connect() as observer:
                        observer.autocommit = True; deadline = time.monotonic()+3
                        while observer.execute('SELECT wait_event FROM pg_stat_activity WHERE pid=%s', (gate.pid,)).fetchone() != ('PgSleep',):
                            if time.monotonic() > deadline: self.fail('Missing actual PG sleep witness')
                            time.sleep(.01)
                        self.retire()
                        self.assertEqual(observer.execute('SELECT pg_cancel_backend(%s)', (gate.pid,)).fetchone(), (True,))
                    future.result(timeout=4)
        self.assertEqual(self.a.inspect()['unknown'], 1)
        with pool.connect() as connection:
            pid, tx = connection.execute('SELECT pg_backend_pid(),txid_current()::text').fetchone()
            self.assertEqual(pid, gate.pid); self.assertNotEqual(tx, gate.tx)
            with self.assertRaises(psycopg.errors.InsufficientPrivilege): connection.execute('SELECT store FROM poc.records')
            connection.rollback()
        with self.assertRaises(Denied): self.adopt()
        self.assertEqual(self.a.inspect()['unknown'], 1)
        print(BANNER, 'K actual cancel after policy2 cut; same pooled backend reused; UNKNOWN retained, adoption blocked', flush=True)

    def test_14_policy_transition_with_three_original_current_survivors(self):
        from h_quorum.cluster import Cluster
        quorum = Cluster(); before = quorum.snapshot('K before minority stop')
        quorum.stop(['r4', 'r5'])
        try:
            self.retire(); self.adopt(); self.positive2()
            print(BANNER, 'K policy2 committed with original current survivors',
                  {name: before['members'][name]['id'] for name in ('r1','r2','r3')}, flush=True)
        finally:
            for name in ('r4', 'r5'): quorum.start(name)

    def test_15_old_policy_issuer_admission_and_actual_readiness_denied(self):
        from recovery_fencing.lab import P1
        from psycopg.types.json import Jsonb
        with self.a.runtime() as gate: self.scope(gate)
        with self.lab.connect('A', 'cac_ctx_issuer') as old_issuer:
            self.assertEqual(old_issuer.execute('SELECT fence.is_ready()').fetchone(), (True,))
            self.retire()
            self.assertEqual(old_issuer.execute('SELECT fence.is_ready()').fetchone(), (False,))
        self.adopt()
        with self.a.runtime() as gate:
            challenge = gate.challenge()
            args = [challenge, self.a.cfg['proof'], S1, 'read', P1, Jsonb({})]
            with self.lab.connect('A', 'cac_ctx_issuer') as issuer:
                pid, tx, sid = issuer.execute('SELECT pg_backend_pid(),txid_current()::text,fence.system_id()').fetchone()
                intent = issuer.execute('SELECT h_guard.issuer_digest(%s,%s,%s,%s,%s,%s)', args).fetchone()[0]
                actor = self.lab.actors['A']
                old = dict(sid=sid, pid=pid, tx=tx, kind='issuer', login='cac_ctx_issuer', digest=intent,
                           incarnation=actor['incarnation'], manifest=actor['manifest'], policy=1,
                           request=str(uuid4()), operation=str(uuid4()))
                before = self.a.inspect()['open']
                with self.assertRaises(Denied): self.a.command('admit', old)
                self.assertEqual(self.a.inspect()['open'], before)
                issuer.rollback()
            gate.install(self.a.issue(challenge)); self.assertEqual(gate.records(), [S1])
        print(BANNER, 'K same issuer SQL readiness true before cut / false after cut; policy1 ADMIT denied; policy2 actual issuance + RLS healthy', flush=True)

    def test_16_runtime_and_issuer_cannot_downgrade_private_sql_policy(self):
        self.retire(); self.adopt(); self.positive2()
        for role in ('cac_ctx_runtime','cac_ctx_issuer'):
            with self.lab.connect('A', role) as connection:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege): connection.execute('UPDATE h_guard.config SET policy=1')
                connection.rollback()
        with self.lab.connect() as observer:
            self.assertEqual(observer.execute('SELECT policy FROM h_guard.config').fetchall(), [(2,)])
        self.positive2()
