"""Finite P route audit. Existing SQL, coordinator, issuer and pool stay unchanged."""
import copy
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from uuid import UUID, uuid4

import psycopg
from psycopg.types.json import Jsonb
from h_quorum.authority import Root
from h_quorum.broker import Broker, Gate
from h_quorum.cluster import Cluster
from h_quorum.common import BANNER, Denied
from h_quorum.etcd import unb64
from h_quorum.integration_lab import IntegrationLab
from h_quorum.retirement import adopt_policy
from h_quorum.p_evidence import snapshot
from h_quorum.rpc import Client
from recovery_fencing.lab import P1, S1, S2
from recovery_proof.pool_lab import Pool

P2, S3 = (str(UUID(int=n)) for n in (1002, 1005))
CASES = ('P_STALE_ISSUER_POLICY_AFTER_RETIREMENT', 'P_DIRECT_SQL_OLD_PRINCIPAL',
         'P_POOL_REUSED_BACKEND_OLD_CONTEXT')
GUC = ('cac.poc_context', 'cac.h_ticket', 'cac.h_intent')


def emit(kind, value):
    print(BANNER, 'P ' + kind, json.dumps(value, sort_keys=True), flush=True)


def secure(condition, message):
    if not condition:
        raise AssertionError('P_SUPPORTED_SECURITY_FAIL ' + message)


def full_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def sql_identity(c):
    user, role, pid, tx, sid = c.execute(
        'SELECT session_user,current_user,pg_backend_pid(),txid_current()::text,fence.system_id()'
    ).fetchone()
    return dict(session_user=user, role=role, pid=pid, fullxid=tx, system_id=sid)


def sql_denial(c, statement, parameters=()):
    try:
        c.execute(statement, parameters).fetchall()
    except psycopg.errors.InsufficientPrivilege as error:
        context = error.diag.context or ''
        functions = [s for s in ('h_guard.require', 'poc.verify', 'poc.issue', 'h_guard.scope') if s in context]
        c.rollback()
        return dict(sqlstate='42501', guard_functions=functions)
    secure(False, 'stale/private SQL route accepted instead of denying')


class Audit:
    def __init__(self, test):
        self.test = test
        self.lab = IntegrationLab()
        test.addCleanup(self.lab.close)
        self.lab.reset()
        self.a = Broker(self.lab)
        self.a.activate(0, str(uuid4()))
        self.q = Cluster()
        self.original = {n: copy.deepcopy(m) for n, m in self.q.cfg['members'].items()}
        self.q.stop(['r4', 'r5'])
        self.control = Client(self.lab.rootcfg, 'control', self.lab.namespace)
        self.receipts = []
        self.witness('P-original-current-three-survivors')
        self.inventory()

    def state(self):
        return Root(self.lab.rootcfg).read(self.lab.namespace, True)

    def witness(self, label):
        state, revision, history = self.state()
        membership = self.q.etcd.call('/v3/cluster/member/list', {'linearizable': True})
        by_id = {str(m['ID']): m for m in membership['members']}
        secure(str(membership['header']['cluster_id']) == str(self.q.cfg['cluster_id']), 'R cluster changed')
        secure(len(by_id) == 5 and not any(m.get('isLearner') for m in by_id.values()), 'R membership changed')
        statuses = {}
        for name, original in self.original.items():
            current = self.q.cfg['members'][name]
            secure(str(current['id']) == str(original['id']) and str(current['id']) in by_id,
                   'original R identity changed')
            if name in ('r4', 'r5'):
                secure(not self.q._owned(original), 'fixture is not three surviving original voters')
                continue
            secure(current['pid'] == original['pid'] and current['data_dir'] == original['data_dir']
                   and self.q._owned(current), 'original current R process/data changed')
            status = self.q.etcd.call('/v3/maintenance/status', {}, endpoint=current['endpoint'])
            secure(str(status['header']['member_id']) == str(original['id']), 'wrong live R endpoint')
            def local():
                rows = self.q.etcd.range('/cac-h/' + self.lab.namespace + '/state', serializable=True,
                                          endpoint=current['endpoint']).get('kvs', [])
                journal = self.q.etcd.range('/cac-h/' + self.lab.namespace + '/journal/', prefix=True,
                                            revision=revision, serializable=True,
                                            endpoint=current['endpoint']).get('kvs', [])
                return (len(rows) == 1 and int(rows[0]['mod_revision']) == revision
                        and json.loads(unb64(rows[0]['value'])) == state
                        and [(r['key'], r['value'], r['mod_revision']) for r in journal]
                        == [(r['key'], r['value'], r['mod_revision']) for r in history])
            self.q._wait(local)
            statuses[name] = dict(id=str(current['id']), pid=current['pid'],
                                  raft_index=status['raftIndex'], applied=status['raftAppliedIndex'])
        try:
            self.lab.validate_private_acl('A')
        except AssertionError as error:
            raise AssertionError('P_SUPPORTED_SECURITY_FAIL ACL/FORCE-RLS invariant') from error
        secure(self.lab.measure('A') == self.lab.rootcfg['approved_manifest'], 'trusted guard catalog changed')
        receipt = dict(label=label, cluster_id=str(self.q.cfg['cluster_id']), current_majority=statuses,
                       stopped_original_ids={n: str(self.original[n]['id']) for n in ('r4', 'r5')},
                       head=state['head'], revision=revision, policy=state['policy'], seq=state['seq'],
                       journal_count=len(history), full_root_journal_sha256=full_hash((state, revision, history)),
                       open=sum(o['phase'] == 'OPEN' for o in state['ops'].values()),
                       unknown=sum(o['phase'] == 'UNKNOWN' for o in state['ops'].values()),
                       mandatory_guard_catalog=True)
        self.receipts.append(receipt)
        emit('CURRENT_R_WITNESS', receipt)
        self.emit_snapshot(label, (state, revision, history))
        return receipt

    def emit_snapshot(self, label, value):
        safe = snapshot(*value)
        secure(safe['original_tuple_sha256'] == full_hash(value), 'snapshot digest mismatch')
        emit('ROOT_STATE_SNAPSHOT', dict(label=label, state=safe['state'], revision=safe['revision'],
                                       original_tuple_sha256=safe['original_tuple_sha256']))
        for number, entry in enumerate(safe['journal']):
            emit('ORDERED_JOURNAL_SNAPSHOT', dict(label=label, index=number, row=entry))
        emit('SNAPSHOT_REDACTION_MANIFEST', dict(label=label, fields=safe['redacted_fields'],
                                                journal_count=len(safe['journal'])))

    def inventory(self):
        with self.lab.connect() as c:
            roles = c.execute("SELECT rolname,rolsuper,rolbypassrls,rolcanlogin,rolinherit,rolcreaterole,rolcreatedb,rolreplication "
                              "FROM pg_roles WHERE rolname LIKE 'cac_%' OR rolname='postgres' ORDER BY rolname").fetchall()
            memberships = c.execute("SELECT a.rolname,b.rolname,m.admin_option FROM pg_auth_members m "
                                   "JOIN pg_roles a ON a.oid=m.member JOIN pg_roles b ON b.oid=m.roleid "
                                   "WHERE a.rolname LIKE 'cac_%' ORDER BY 1,2").fetchall()
            rel = c.execute("SELECT pg_get_userbyid(relowner),relrowsecurity,relforcerowsecurity "
                            "FROM pg_class WHERE oid='poc.records'::regclass").fetchone()
            policies = c.execute("SELECT policyname,cmd,roles::text,qual,with_check FROM pg_policies "
                                 "WHERE schemaname='poc' AND tablename='records' ORDER BY policyname").fetchall()
            funcs = c.execute("SELECT p.oid::regprocedure::text,pg_get_userbyid(p.proowner),p.prosecdef,p.proconfig "
                              "FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                              "WHERE n.nspname IN ('poc','poc_private','h_guard','fence','fence_private') ORDER BY 1").fetchall()
            acls = []
            private = ('poc_private.issue_unfenced(text,text,uuid,text,uuid,jsonb)',
                       'poc_private.verify_unfenced()', 'h_guard.issue_c(text,text,uuid,text,uuid,jsonb)',
                       'h_guard.verify_c()', 'h_guard.rpc(text,jsonb)', 'fence_private.check_guard_c()')
            for role in ('cac_ctx_runtime', 'cac_ctx_issuer', 'cac_ctx_identity', 'cac_fence_activator'):
                role_row = next(r for r in roles if r[0] == role)
                secure(not any((role_row[1], role_row[2], role_row[5], role_row[6], role_row[7])), 'privileged application login')
                for owner in ('cac_ctx_owner', 'cac_ctx_guard', 'postgres'):
                    allowed = c.execute('SELECT pg_has_role(%s,%s,\'SET\')', (role, owner)).fetchone()[0]
                    secure(not allowed, 'application login can SET ROLE to privileged owner')
                for signature in private:
                    allowed = c.execute('SELECT has_function_privilege(%s,%s,\'EXECUTE\')', (role, signature)).fetchone()[0]
                    acls.append(dict(role=role, function=signature, execute=allowed))
                    secure(not allowed, 'application role has private legacy function execution')
            secure(rel == ('cac_ctx_owner', True, True), 'protected relation owner/FORCE-RLS changed')
        emit('LIVE_ROUTE_INVENTORY', dict(roles=roles, memberships=memberships, relation=rel,
             policies=policies, function_owners_definers_search_paths=funcs, private_execute_acls=acls,
             direct_listener=self.lab.cfg['A']['connection']['port'],
             privileged_routes='postgres/NOLOGIN owners: OUT_OF_SCOPE; no role grants added'))

    def retire(self):
        before = self.state()
        receipt = self.control.call('retire_policy', dict(expected=1, new=2, request=str(uuid4())))
        self.lab.replay()
        after = self.state()
        secure(after[0]['policy'] == 2 and after[0]['signer_epoch'] == before[0]['signer_epoch'], 'not a real policy cut')
        secure(after[0]['ops'] == before[0]['ops'], 'retirement prematurely changed OPEN/UNKNOWN')
        secure(after[0]['seq'] == before[0]['seq'] + 1 and len(after[2]) == len(before[2]) + 1,
               'retirement journal transition mismatch')
        secure(receipt['revision'] == after[1] == int(after[2][-1]['mod_revision']), 'retirement lacks MVCC receipt')
        emit('POLICY_CUT', dict(receipt=receipt, before=full_hash(before), after=full_hash(after),
                               signer_unchanged=True, operations_unchanged=True))
        self.emit_snapshot('P-immediately-before-policy-cut', before)
        self.emit_snapshot('P-immediately-after-policy-cut', after)
        return receipt

    def root_denied(self, action, args, reason):
        before = self.state()
        try:
            self.a.command(action, args)
        except Denied:
            pass
        else:
            secure(False, reason)
        secure(self.state() == before, 'denied operation mutated full Root/journal')

    def new_old_admit(self, gate):
        self.root_denied('admit', dict(gate.binding, policy=1, request=str(uuid4()), operation=str(uuid4())),
                         'new policy1 ADMIT accepted after retirement')

    def grant(self, gate, broker=None, store=S1, principal=P1, proof=None, action='read', body=None,
              challenge=None):
        broker = broker or self.a
        h = challenge if challenge is not None else gate.challenge()
        args = [h, proof or broker.cfg['proof'], store, action, principal, Jsonb(body or {})]
        with Gate(broker, 'cac_ctx_issuer', args=args) as issuer_gate:
            token = issuer_gate.c.execute('SELECT poc.issue(%s,%s,%s,%s,%s,%s)', args).fetchone()[0]
            issuer = dict(pid=issuer_gate.pid, fullxid=issuer_gate.tx, role='cac_ctx_issuer')
        gate.install(token)
        secure(gate.records() == [store], 'healthy signed scope failed')
        return token, h, issuer

    def positive(self, broker=None, store=S1, principal=P1, proof=None):
        broker = broker or self.a
        with broker.runtime(store=store, target=principal) as gate:
            secure(gate.binding['policy'] == 2, 'current positive admitted wrong policy')
            token, _, issuer = self.grant(gate, broker, store, principal, proof)
            self.new_old_admit(gate)
            secure(gate.c.execute('SELECT store FROM poc.records WHERE store<>%s', (store,)).fetchall() == [],
                   'cross-store/cross-tenant SELECT leaked rows')
            other = S3 if store == S1 else S1
            secure(gate.c.execute('UPDATE poc.records SET body=%s WHERE store=%s',
                                  ('synthetic-no-cross-write', other)).rowcount == 0, 'cross-tenant write leaked')
            return dict(runtime=sql_identity(gate.c), issuer=issuer, principal=principal, own_store=store,
                        visible=[store], cross_store_select=[], cross_tenant_update=0)


class LegacyIssuer:
    def __init__(self, audit):
        self.audit = audit
        self.temp = tempfile.TemporaryDirectory(prefix='cac-p-issuer-', dir=os.environ['RUNNER_TEMP'])
        self.base = Path(self.temp.name)
        self.base.chmod(0o700)
        cfg = self.base / 'issuer.json'
        cfg.write_text(json.dumps(dict(connection=audit.lab.cfg['A']['connection'], role='cac_ctx_issuer',
                                       password=audit.lab.cfg['A']['passwords']['cac_ctx_issuer'])))
        cfg.chmod(0o600)
        self.socket = self.base / 'original.sock'
        self.log_path = self.base / 'safe-trace.log'
        self.output = self.log_path.open('w+')
        self.log_path.chmod(0o600)
        self.stderr = tempfile.TemporaryFile()
        with socket.socket(socket.AF_UNIX) as listener:
            listener.bind(str(self.socket)); listener.listen(4)
            self.child = subprocess.Popen([sys.executable, '-m', 'h_quorum.p_issuer_worker', str(cfg),
                                           str(os.getuid()), str(listener.fileno())], pass_fds=(listener.fileno(),),
                stdout=self.output, stderr=self.stderr, env=dict(PATH=os.environ['PATH'], LANG='C.UTF-8',
                PYTHONPATH='.', PYTHONDONTWRITEBYTECODE='1'))
        audit.test.addCleanup(self.close)
        deadline = time.monotonic() + 10
        while True:
            if '"kind": "READY"' in self.log_path.read_text():
                break
            if self.child.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError('P_ENV_OR_ROUTE_BLOCKED_NOT_RUN original issuer startup')
            time.sleep(.03)

    def request(self, h):
        req = dict(challenge=h, proof=self.audit.a.cfg['proof'], store=S1, action='probe', target=P1,
                   body={'body': 'synthetic-P-inflight'})
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(5)
            client.connect(str(self.socket))
            client.sendall(json.dumps(req).encode() + b'\n')
            response = b''
            while not response.endswith(b'\n'):
                chunk = client.recv(4096)
                if not chunk or len(response) > 24000:
                    raise RuntimeError('P legacy original response unresolved')
                response += chunk
        events = [json.loads(line.split('P_LEGACY_EVENT ', 1)[1]) for line in self.log_path.read_text().splitlines()
                  if 'P_LEGACY_EVENT ' in line]
        for e in events:
            emit('ORIGINAL_ISSUER_TRACE', e)
        secure(json.loads(response) == {'ok': False, 'error': 'denied'}, 'old socket issuer issued after cut')
        calls = [e for e in events if e['kind'] == 'ORIGINAL_SQL_CALL']
        errors = [e for e in events if e['kind'] == 'ORIGINAL_SQL_EXCEPTION']
        self.audit.test.assertEqual(len(calls), 1, 'Actual original issuer SQL route not witnessed')
        self.audit.test.assertEqual(len(errors), 1, 'Original SQL denial not uniquely witnessed')
        secure(calls[0]['role'] == calls[0]['session_user'] == 'cac_ctx_issuer', 'wrong original issuer SQL role')
        secure(calls[0]['pid'] == calls[0]['driver_backend_pid'], 'issuer backend mismatch')
        self.audit.test.assertTrue(0 <= calls[0]['challenge_age_seconds'] < 5,
                                   'P original issuer observation inconclusive: challenge expired')
        self.audit.test.assertTrue('h_guard.require' in errors[0]['functions'], 'Denied route did not prove mandatory guard')
        secure(errors[0]['sqlstate'] == '42501', 'wrong original issuer denial')
        return dict(events=events, response='denied', original_serve=True,
                    os_custody='SAME_RUNNER_UID_ONLY_NOT_INDEPENDENT_CUSTODY')

    def close(self):
        if hasattr(self, 'child') and self.child.poll() is None:
            self.child.terminate()
            self.child.wait(timeout=5)
        if not self.output.closed:
            self.output.close(); self.stderr.close(); self.temp.cleanup()


def stale_tuple(c, token, ticket, intent):
    for key, value in zip(GUC, (token, ticket, intent)):
        c.execute('SELECT set_config(%s,%s,true)', (key, value))


def unexpired_context(test, c, token):
    claims = json.loads(bytes.fromhex(token.split('.')[0]))
    now = c.execute('SELECT extract(epoch FROM clock_timestamp())').fetchone()[0]
    remaining = float(claims['exp']) - float(now)
    test.assertGreater(remaining, 0, 'P stale-context cut inconclusive: token expired before replay')
    return dict(unexpired=True, remaining_seconds=remaining,
                signed_original_pid=claims['pid'], signed_original_tx=claims['tx'])


def issuer_case(a):
    old = LegacyIssuer(a)  # Start before generating the inherited five-second challenge.
    body = {'body': 'synthetic-P-inflight'}
    with a.a.runtime(action='probe', body=body) as gate:
        a.grant(gate, action='probe', body=body)
        gate.c.execute('UPDATE poc.records SET body=%s WHERE store=%s', (body['body'], S1))
        a.retire()
        secure(gate.records() == [S1], 'valid historical pregrant incorrectly lost scope')
        secure(a.state()[0]['ops'][gate.operation]['phase'] == 'OPEN', 'historical OPEN prematurely released')
        a.witness('P-historical-pregrant-still-OPEN-after-retirement')
    secure(a.state()[0]['ops'][gate.operation]['phase'] == 'CLOSED_COMMIT', 'historical real COMMIT ACK/CLOSE missing')
    adopt_policy(a.lab)
    with a.a.runtime(action='probe', body=body) as current:
        secure(current.binding['policy'] == 2, 'fresh issuer control is not current policy2')
        a.new_old_admit(current)
        challenge = current.challenge()
        def ledger_count():
            with a.lab.connect() as c:
                return c.execute('SELECT count(*) FROM poc_private.ledger WHERE tx=%s AND pid=%s',
                                 (current.tx, current.pid)).fetchone()[0]
        a.test.assertEqual(ledger_count(), 0, 'P legacy request is not a fresh issuance attempt')
        before = a.state()
        result = old.request(challenge)
        call = next(e for e in result['events'] if e['kind'] == 'ORIGINAL_SQL_CALL')
        a.test.assertEqual((call['challenge_pid'], call['challenge_tx']), (current.pid, current.tx),
                           'P original issuer used a different runtime challenge')
        secure(a.state() == before, 'legacy issuer changed full Root/journal')
        secure(ledger_count() == 0, 'legacy issuer inserted an unauthorized signed context')
        _, _, issuer = a.grant(current, action='probe', body=body, challenge=challenge)
        secure(ledger_count() == 1, 'same-challenge healthy current issuance missing')
        result['current_positive'] = dict(runtime=sql_identity(current.c), issuer=issuer,
            policy=2, same_fresh_challenge=True, ledger_before=0, ledger_after_old=0,
            ledger_after_current=1, visible=current.records())
    result['historical'] = 'PREGRANTED_OPEN_RETAINED_REAL_COMMIT_ACK_THEN_CLOSED_COMMIT'
    result['generation_limit'] = 'OLD_PROTOCOL_HAS_NO_POLICY_OR_R_TICKET; EXPLICIT_POLICY1_ADMIT_NEGATIVE_SEPARATE'
    return result


def direct_case(a):
    with a.a.runtime() as gate:
        token, challenge, _ = a.grant(gate)
        ticket, intent = gate.ticket, gate.binding['digest']
    secure(a.state()[0]['ops'][gate.operation]['phase'] == 'CLOSED_COMMIT', 'pre-cut direct operation not closed')
    a.retire()
    before = a.state()
    with a.lab.connect('A', 'cac_ctx_runtime') as c:
        identity = sql_identity(c)
        stale_tuple(c, token, ticket, intent)
        live = unexpired_context(a.test, c, token)
        stale = sql_denial(c, 'SELECT store FROM poc.records')
        a.test.assertIn('h_guard.require', stale['guard_functions'], 'P direct guard path not witnessed')
        legacy_helpers = []
        for statement, parameters in (
                ('SELECT poc.verify()', ()), ('SELECT poc.read_scope()', ()),
                ('SELECT poc.authorize(%s,%s,%s)', ('read', P1, Jsonb({})))):
            stale_tuple(c, token, ticket, intent)
            legacy_helpers.append(dict(statement=statement, outcome=sql_denial(c, statement, parameters)))
    with a.lab.connect('A', 'cac_ctx_issuer') as c:
        issuer_identity = sql_identity(c)
        private = sql_denial(c, 'SELECT h_guard.issue_c(%s,%s,%s,%s,%s,%s)',
                             (challenge, a.a.cfg['proof'], S1, 'read', P1, Jsonb({})))
    secure(a.state() == before, 'direct denied SQL mutated Root/journal')
    a.witness('P-real-direct-listener-stale-role-denied')
    adopt_policy(a.lab)
    return dict(direct_runtime=identity, stale_runtime_sql=stale, stale_signed_context=live, issuer=issuer_identity,
                executable_legacy_helpers=legacy_helpers,
                private_legacy_function_acl=private, principal1_positive=a.positive(),
                principal2_positive=a.positive(store=S3, principal=P2, proof=a.lab.cfg['A']['poc_proofs'][1]),
                privileged='DBA/owner/guard rewrite OUT_OF_SCOPE; no grants or role changes')


def pool_case(a):
    pool = Pool(a.lab)
    a.test.addCleanup(pool.close)
    broker = Broker(a.lab, pool=pool)
    body = {'body': 'synthetic-P-pool'}
    # The same original authenticated pool connection spans a valid old grant.
    with broker.runtime(action='probe', body=body) as gate:
        token, _, _ = a.grant(gate, broker, action='probe', body=body)
        first = sql_identity(gate.c)
        values = (token, gate.ticket, gate.binding['digest'])
        for key, value in zip(GUC, values):
            gate.c.execute('SELECT set_config(%s,%s,false)', (key, value))
        a.retire()
        secure(gate.records() == [S1], 'historical pooled pregrant incorrectly denied')
        gate.c.execute('UPDATE poc.records SET body=%s WHERE store=%s', (body['body'], S1))
        a.a.command('revoke', dict(expected=1))
        a.root_denied('reserve', dict(expected=1, request=str(uuid4())), 'successor reserved while historical OPEN')
        def hook(label):
            if label == 'after_local_commit_before_close':
                secure(a.state()[0]['ops'][gate.operation]['phase'] == 'OPEN', 'OPEN cleared before R CLOSE')
                a.root_denied('reserve', dict(expected=1, request=str(uuid4())), 'successor reserved before acknowledged CLOSE')
        broker.hook = hook
    broker.hook = lambda _: None
    secure(a.state()[0]['ops'][gate.operation]['phase'] == 'CLOSED_COMMIT', 'pooled actual COMMIT/CLOSE missing')
    before = a.state()
    with pool.connect() as c:
        second = sql_identity(c)
        a.test.assertEqual(first['pid'], second['pid'], 'P pool route NOT_RUN: backend was not reused')
        a.test.assertNotEqual(first['fullxid'], second['fullxid'], 'P pool new transaction not witnessed')
        retained = [c.execute('SELECT current_setting(%s,true)', (key,)).fetchone()[0] for key in GUC]
        a.test.assertTrue(retained == list(values), 'P persistent old session state not reproduced')
        live_raw = unexpired_context(a.test, c, token)
        raw = sql_denial(c, 'SELECT store FROM poc.records')
        a.test.assertIn('h_guard.require', raw['guard_functions'], 'P raw pooled guard not witnessed')
    with pool.connect() as c:
        third = sql_identity(c)
        a.test.assertEqual(first['pid'], third['pid'], 'P pool explicit replay not same backend')
        stale_tuple(c, *values)
        live_replay = unexpired_context(a.test, c, token)
        replay = sql_denial(c, 'SELECT store FROM poc.records')
        a.test.assertIn('h_guard.require', replay['guard_functions'], 'P replay pooled guard not witnessed')
    secure(a.state() == before, 'pooled stale denial changed Root/journal')
    a.witness('P-same-pooled-backend-old-context-denied')
    adopt_policy(a.lab)
    a.a.activate(1, str(uuid4()))
    positive = a.positive(broker)
    a.test.assertEqual(positive['runtime']['pid'], first['pid'], 'P current positive not on reused backend')
    a.test.assertNotEqual(positive['runtime']['fullxid'], third['fullxid'])
    positive_p2 = a.positive(broker, store=S3, principal=P2, proof=a.lab.cfg['A']['poc_proofs'][1])
    a.test.assertEqual(positive_p2['runtime']['pid'], first['pid'], 'P principal switch not on reused backend')
    # A real PostgreSQL error leaves the inherited Gate's genuine UNKNOWN hold.
    unknown = broker.runtime()
    with a.test.assertRaises(psycopg.errors.DivisionByZero):
        with unknown:
            a.grant(unknown, broker)
            unknown.c.execute('SELECT 1/0')
    secure(a.state()[0]['ops'][unknown.operation]['phase'] == 'UNKNOWN', 'real SQL failure did not retain UNKNOWN')
    a.root_denied('close', dict(unknown.binding, ticket=unknown.ticket, outcome='abort'), 'inferred abort cleared UNKNOWN')
    a.a.command('revoke', dict(expected=2))
    a.root_denied('reserve', dict(expected=2, request=str(uuid4())), 'successor accepted while UNKNOWN')
    secure(a.a.inspect()['unknown'] == 1, 'UNKNOWN prematurely released')
    return dict(first=first, reused=second, explicit_replay=third, retained_context_ticket_intent=True,
                raw_sql_denial=raw, explicit_SET_LOCAL_denial=replay, current_positive=positive,
                current_principal2_positive=positive_p2, live_old_context_raw=live_raw,
                live_old_context_replay=live_replay,
                historical='REAL_COMMIT_ACK_THEN_CLOSE; SUCCESSOR_DENIED_UNTIL_CLOSE',
                unknown='REAL_SQL_ERROR_UNKNOWN_RETAINED; INFERRED_ABORT_AND_SUCCESSOR_DENIED',
                cleanup='SESSION_VALUES_INTENTIONALLY_PERSIST; NEW_SET_LOCAL_AUTH_REQUIRED',
                cross_login_pool='NOT_APPLICABLE single runtime-login pool; no cross-login switching claim')


def run_case(test, case):
    if case not in CASES:
        raise RuntimeError('P fixed route case mismatch')
    row = dict(case=case, verdict='P_LEGACY_ROUTE_COVERAGE_INCONCLUSIVE', actual_path='NOT_RUN')
    try:
        a = Audit(test)
        row['before'] = a.witness('P-case-before')
        row['result'] = {CASES[0]: issuer_case, CASES[1]: direct_case, CASES[2]: pool_case}[case](a)
        row['after'] = a.witness('P-case-after')
        row['actual_path'] = 'EXECUTED_ORIGINAL_ROUTE'
        row['verdict'] = 'P_LEGACY_ROUTE_BOUNDED_PASS'
    except BaseException as error:
        if 'P_SUPPORTED_SECURITY_FAIL' in str(error):
            row['verdict'] = 'P_SUPPORTED_SECURITY_FAIL'
        elif 'P_ENV_OR_ROUTE_BLOCKED_NOT_RUN' in str(error):
            row['verdict'] = 'P_ENV_OR_ROUTE_BLOCKED_NOT_RUN'
        row['failure_type'] = type(error).__name__
        if isinstance(error, AssertionError):
            row['preserved_assertion'] = str(error)
        raise RuntimeError(row['verdict'] + ': preserved original failure; no rerun') from None
    finally:
        emit('OBSERVATION', row)
