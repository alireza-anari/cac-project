"""Supervisor for one real native precondition and one controller cut; no retries."""
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from h_quorum.authority import Root
from h_quorum.broker import Broker
from h_quorum.cluster import Cluster
from h_quorum.common import BANNER, Denied
from h_quorum.integration_lab import IntegrationLab
from h_quorum.l_physical.m_triage import ObservedPhysical, state_summary
from h_quorum.l_physical.n_triage import (
    progress_and_stop, read_full, replay_old_and_require_panic, retire_policy,
)
from h_quorum.l_physical.o_controller import CASES, CODES, root_receipt
from h_quorum.retirement import adopt_policy
from recovery_fencing.lab import S1


def emit(kind, value):
    print(BANNER, 'O ' + kind, json.dumps(value, sort_keys=True), flush=True)


def secure(condition, message):
    if not condition:
        raise AssertionError('O_SUPPORTED_SECURITY_FAIL ' + message)


class OPhysical(ObservedPhysical):
    def majority_current(self, label):
        try:
            return super().majority_current(label)
        except AssertionError as error:
            raise AssertionError('O_SUPPORTED_SECURITY_FAIL original majority invariant') from error


def guard(lab, broker):
    try:
        lab.validate_private_acl('A')
    except AssertionError as error:
        raise AssertionError('O_SUPPORTED_SECURITY_FAIL trusted ACL/FORCE-RLS invariant') from error
    secure(lab.measure('A') == lab.rootcfg['approved_manifest'], 'trusted guard catalog changed')
    secure(not broker.ready(), 'retired policy became ready')
    with lab.connect('A', 'cac_ctx_issuer') as issuer:
        secure(issuer.execute('SELECT fence.is_ready()').fetchone() == (False,), 'old issuer ready')
    try:
        with broker.runtime():
            secure(False, 'old policy admitted protected SQL')
    except Denied:
        pass


def interrupted_repair(test, lab, physical, case, before):
    old = dict(physical.q.cfg['members']['r4'])
    old_id = str(old['id'])
    physical.stop()  # Reap the already failed old native process; this is not a controller cut.
    secure(not physical.q._owned(old), 'old native process survived panic')
    old_files = physical.inventory(Path(old['data_dir']))
    initial = physical.q.etcd.call('/v3/cluster/member/list', {'linearizable': True})
    test.assertEqual(len(initial['members']), 5, 'O initial fixture membership')
    test.assertFalse(any(m.get('isLearner') for m in initial['members']))
    physical.majority_current('O-parent-before-controller')
    child = subprocess.Popen([sys.executable, '-m', 'h_quorum.l_physical.o_controller'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, start_new_session=True)
    try:
        stdout, stderr = child.communicate(timeout=150)
    except subprocess.TimeoutExpired:
        child.kill()
        child.communicate(timeout=10)
        raise RuntimeError('O_INTERRUPTED_REPAIR_INCONCLUSIVE controller timeout; no rerun') from None
    # Only deliberate, allowlisted receipts are forwarded; stderr stays private.
    events = []
    marker = ' O_EVENT '
    for line in stdout.splitlines():
        if marker in line:
            event = json.loads(line.split(marker, 1)[1])
            events.append(event)
            emit('CONTROLLER_RECEIPT', event)
    if any(e.get('kind') == 'ERROR' and e.get('security') for e in events):
        secure(False, 'controller witnessed invariant violation')
    test.assertEqual(child.returncode, CODES[case], 'O faithful cut not observed; no rerun')
    cuts = [e for e in events if e['kind'] == 'CUT']
    test.assertEqual(len(cuts), 1, 'O exactly one deliberate cut')
    test.assertEqual(cuts[0]['pid'], child.pid)
    test.assertFalse(Path('/proc', str(child.pid)).exists(), 'O controller process still exists')
    expected = ['remove'] if case == CASES[0] else ['remove', 'add']
    if case == CASES[2]:
        expected.append('promote')
    requests = [e['operation'] for e in events if e['kind'] == 'REQUEST']
    test.assertEqual(requests, expected, 'O unsafe duplicate or out-of-order membership request')
    test.assertEqual([e['operation'] for e in events if e['kind'] == 'WIRE_REQUEST'], expected,
                     'O wire membership request mismatch')
    test.assertEqual([e['operation'] for e in events if e['kind'] == 'WIRE_RESPONSE'], expected,
                     'O wire membership response mismatch')
    test.assertEqual(cuts[0]['attempts'], expected)
    acknowledgements = [e['operation'] for e in events if e['kind'] == 'ACK']
    test.assertEqual(acknowledgements, [op for op in expected if op != 'promote'])
    witnesses = [e for e in events if e['kind'] == 'WITNESS']
    test.assertGreaterEqual(len(witnesses), 2)
    for witness in witnesses:
        secure(witness['root'] == root_receipt(before), 'Root/revision/ordered journal changed at cut step')

    # A fresh process-owned config and current-quorum membership resolve actual state.
    # No repair continuation, second add/promote, inferred abort, or local flag rewrite.
    physical.q = Cluster()
    q = physical.q
    membership = q.etcd.call('/v3/cluster/member/list', {'linearizable': True})
    members = {str(m['ID']): m for m in membership['members']}
    secure(str(membership['header']['cluster_id']) == str(q.cfg['cluster_id']), 'cluster identity changed')
    secure(old_id not in members, 'removed old ID remains in authoritative membership')
    secure(read_full(lab) == before, 'Root/journal/hold changed across interruption')
    physical.majority_current('O-parent-after-controller-exit-authoritative-reconcile')
    archives = [a for a in q.cfg['members']['r4'].get('archives', []) if str(a['id']) == old_id]
    test.assertEqual(len(archives), 1, 'O old bytes not uniquely quarantined')
    secure(physical.inventory(Path(archives[0]['data_dir'])) == old_files, 'old quarantine hashes changed')
    secure(not Path(old['data_dir']).exists(), 'old data directory reused')
    secure(not q._owned(old), 'old executable restarted')
    learners = [m for m in members.values() if m.get('isLearner')]
    receipt = dict(case=case, controller_pid=child.pid, controller_exit=child.returncode,
                   one_cut=True, controller_process_absent=True, requests=requests,
                   controller_acks=acknowledgements, wire_requests=expected, membership_before=initial,
                   authoritative_membership_after=membership,
                   root_before=root_receipt(before), root_after=root_receipt(read_full(lab)),
                   old_id=old_id, old_bytes_quarantined_hashes=old_files,
                   no_resume_no_retry=True, guard_checks='REQUIRED_SEPARATELY')
    if case == CASES[0]:
        test.assertEqual(len(members), 4)
        secure(not learners, 'unexpected learner after remove-only cut')
        receipt['disposition'] = 'REMOVED_CONTROLLER_STOPPED_BEFORE_ADD_OPEN_HELD'
    else:
        fresh = q.cfg['members']['r4']
        fresh_id = str(fresh['id'])
        test.assertEqual(len(members), 5)
        secure(fresh_id != old_id and fresh_id in members, 'fresh ID missing or reused')
        matches = [m for m in members.values() if old['peer_url'] in m['peerURLs']]
        test.assertEqual(len(matches), 1, 'O ambiguous authoritative replacement')
        secure(str(matches[0]['ID']) == fresh_id, 'authoritative fresh identity mismatch')
        test.assertEqual(len([e for e in events if e['kind'] == 'FRESH_BOOTSTRAP']), 1)
        secure(fresh['cert'] != old['cert'] and fresh['key'] != old['key'], 'fresh certificate reused')
        receipt['fresh_id'] = fresh_id
        if case == CASES[1]:
            secure(members[fresh_id].get('isLearner'), 'learner auto-promoted after interruption')
            test.assertEqual(len(learners), 1)
            test.assertFalse(q._owned(fresh), 'O cut occurred after learner process started')
            test.assertEqual(list(Path(fresh['data_dir']).iterdir()), [], 'O new learner directory not empty')
            test.assertFalse(any(e['kind'] == 'CATCHUP' for e in events))
            receipt['disposition'] = 'EXACT_NONVOTING_UNSTARTED_LEARNER_RECONCILED_UNKNOWN_HELD'
        else:
            test.assertEqual(len([e for e in events if e['kind'] == 'CATCHUP']), 1)
            lost = [e for e in events if e['kind'] == 'TRANSPORT_RESPONSE_SUPPRESSED']
            test.assertEqual(len(lost), 1)
            test.assertFalse(lost[0]['controller_received_ack'])
            secure(not members[fresh_id].get('isLearner', False), 'promotion reconciliation did not show voter')
            secure(not learners, 'learner remains after confirmed promotion')
            # q.promote's local flag update did not execute, proving the caller did not receive ACK.
            test.assertTrue(fresh['isLearner'], 'O controller unexpectedly processed promotion ACK')
            receipt['disposition'] = 'COMMITTED_BUT_REPLY_LOST_AUTHORITATIVE_VOTER_UNKNOWN_HELD'
            receipt['stale_local_learner_flag'] = True
    emit('INTERRUPTION', receipt)
    return receipt


def held_checks(test, lab, broker, successor, before, gate, unknown):
    secure(read_full(lab) == before, 'Root/journal changed before hold checks')
    guard(lab, broker)
    try:
        successor.activate(1, str(uuid4()))
    except Denied:
        pass
    else:
        secure(False, 'successor admitted while operation held')
    if unknown:
        for action in (lambda: adopt_policy(lab), lambda: broker.command(
                'close', dict(gate.binding, ticket=gate.ticket, outcome='abort'))):
            try:
                action()
            except Denied:
                pass
            else:
                secure(False, 'UNKNOWN adoption/inferred abort accepted')
        secure(broker.inspect()['unknown'] == 1, 'genuine UNKNOWN cleared')
    secure(read_full(lab) == before, 'denied action mutated Root/journal/hold')


def run_sample(test, case):
    if case not in CASES:
        raise RuntimeError('O frozen case mismatch')
    lab = IntegrationLab()
    test.addCleanup(lab.close)
    lab.reset()
    broker = Broker(lab)
    broker.activate(0, str(uuid4()))
    physical = OPhysical(lab)
    test.addCleanup(physical.close)
    physical.archive_current()
    successor = Broker(lab, 'B')
    unknown = case != CASES[0]
    body = {'body': 'synthetic-O-' + case}
    gate = broker.runtime(action='probe', body=body)
    row = dict(case=case, verdict='O_INTERRUPTED_REPAIR_INCONCLUSIVE', actual_cut='NOT_RUN')

    def observe_cut():
        row['progress'] = progress_and_stop(test, physical, kill=unknown)
        before = read_full(lab)
        summary = state_summary(*before)
        test.assertEqual(summary['unknown'], 1 if unknown else 0)
        if not unknown:
            test.assertGreaterEqual(summary['open'], 1)
        row['native_replay'] = replay_old_and_require_panic(test, lab, physical, before)
        secure(read_full(lab) == before, 'native panic changed Root/journal')
        held_checks(test, lab, broker, successor, before, gate, unknown)
        row['before'] = summary
        row['repair'] = interrupted_repair(test, lab, physical, case, before)
        row['actual_cut'] = row['repair']['disposition']
        held_checks(test, lab, broker, successor, before, gate, unknown)
        physical.majority_current('O-after-cut-and-guard-denial-checks')
        row['after'] = state_summary(*read_full(lab))
        row['guard_and_successor_denials'] = True
        row['unknown_adoption_abort_denied'] = unknown

    try:
        if unknown:
            def retire_after_open(label):
                if label == 'after_durable_open':
                    retire_policy(lab)
            broker.hook = retire_after_open
            with test.assertRaises(Denied):
                with gate:
                    secure(False, 'ungranted UNKNOWN operation reached SQL')
            broker.hook = lambda _: None
            test.assertIsNotNone(gate.ticket)
            test.assertIsNotNone(gate.binding)
            observe_cut()
            row['policy2_sql'] = 'BLOCKED_BY_DESIGN_WHILE_UNKNOWN'
        else:
            with gate:
                gate.install(broker.issue(gate.challenge(), action='probe', body=body))
                test.assertEqual(gate.records(), [S1])
                test.assertEqual(gate.c.execute('UPDATE poc.records SET body=%s WHERE store=%s',
                                               (body['body'], S1)).rowcount, 1)
                row['pregrant'] = dict(pid=gate.pid, fullxid=gate.tx, system_id=gate.sid,
                                       operation=gate.operation)
                retire_policy(lab)
                observe_cut()
            state = Root(lab.rootcfg).read(lab.namespace)[0]
            secure(state['ops'][gate.operation]['phase'] == 'CLOSED_COMMIT', 'actual COMMIT ACK/CLOSE missing')
            adopt_policy(lab)
            secure(broker.ready(), 'current policy2 not ready after known CLOSE')
            with broker.runtime() as current:
                secure(current.binding['policy'] == 2, 'wrong current policy')
                try:
                    broker.command('admit', dict(current.binding, policy=1,
                                                request=str(uuid4()), operation=str(uuid4())))
                except Denied:
                    pass
                else:
                    secure(False, 'explicit old policy1 admission accepted')
                current.install(broker.issue(current.challenge()))
                secure(current.records() == [S1], 'scoped current SQL failed')
                secure(current.c.execute('SELECT body FROM poc.records WHERE store=%s', (S1,)).fetchone()
                       == (body['body'],), 'committed SQL body mismatch')
            row['policy2_sql'] = 'REAL_COMMIT_ACK_CLOSED_COMMIT_THEN_SCOPED_READ_PASS'
        physical.majority_current('O-final-original-current-majority')
        row['verdict'] = 'O_INTERRUPTED_REPAIR_BOUNDED_PASS'
    except BaseException as error:
        if 'O_SUPPORTED_SECURITY_FAIL' in str(error):
            row['verdict'] = 'O_SUPPORTED_SECURITY_FAIL'
        row['failure_type'] = type(error).__name__
        raise
    finally:
        broker.hook = lambda _: None
        emit('OBSERVATION', row)
