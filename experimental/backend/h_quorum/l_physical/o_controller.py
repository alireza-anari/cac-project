"""Disposable child controller. Cuts terminate this process, never consensus."""
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

from h_quorum.authority import Root
from h_quorum.cluster import Cluster
from h_quorum.common import BANNER
from h_quorum.l_physical.fixture import Physical
from h_quorum.l_physical.o_transport import OneShotRequests

CASES = ('O_REMOVE_ACK_THEN_STOP_OPEN', 'O_LEARNER_ADDED_THEN_STOP_UNKNOWN',
         'O_PROMOTE_ACK_LOSS_UNKNOWN')
CODES = dict(zip(CASES, (70, 71, 72)))


def emit(kind, **value):
    print(BANNER, 'O_EVENT', json.dumps(dict(kind=kind, **value), sort_keys=True), flush=True)


def root_receipt(value):
    state, revision, journal = value
    return dict(head=state['head'], revision=revision, journal_count=len(journal),
                full_sha256=hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest())


def main():
    case = os.environ['CAC_O_CASE']
    if case not in CASES:
        raise RuntimeError('O frozen case mismatch')
    q = Cluster()
    old = dict(q.cfg['members']['r4'])
    lab = SimpleNamespace(rootcfg=q.cfg, namespace=q.cfg['app_namespace'])
    physical = Physical(lab)
    physical.q = q
    before = Root(q.cfg).read(lab.namespace, True)
    original_call, original_spawn = q.etcd.call, q._spawn
    attempts = []

    def witness(label):
        actual = Root(q.cfg).read(lab.namespace, True)
        if actual != before:
            raise AssertionError('O_SUPPORTED_SECURITY_FAIL Root/journal changed')
        try:
            physical.majority_current(label)
        except AssertionError as error:
            raise AssertionError('O_SUPPORTED_SECURITY_FAIL original majority invariant') from error
        listed = original_call('/v3/cluster/member/list', {'linearizable': True})
        emit('WITNESS', label=label, membership=listed, root=root_receipt(actual),
             original_majority={n: dict(id=m['id'], pid=m['pid'])
                                for n, m in physical.majority.items()})
        return listed

    def cut(label):
        emit('CUT', case=case, label=label, pid=os.getpid(), exit_code=CODES[case],
             attempts=attempts, controller_continuation=False)
        os._exit(CODES[case])

    def traced(path, *args, **kwargs):
        tracked = path.rsplit('/', 1)[-1] if path.startswith('/v3/cluster/member/') else None
        if tracked in ('remove', 'add', 'promote'):
            expected = ('remove', 'add', 'promote')[len(attempts)] if len(attempts) < 3 else None
            if tracked != expected:
                raise RuntimeError('O duplicate/out-of-order membership request forbidden')
            attempts.append(tracked)
            emit('REQUEST', operation=tracked, ordinal=len(attempts))
            if tracked == 'add':
                listed = original_call('/v3/cluster/member/list', {'linearizable': True})
                if any(str(m['ID']) == str(old['id']) for m in listed['members']):
                    raise AssertionError('O_SUPPORTED_SECURITY_FAIL old ID still admitted')
        result = original_call(path, *args, **kwargs)
        if tracked in ('remove', 'add', 'promote'):
            if tracked == 'promote':
                # The transport shim has the real response. q.promote never sees it.
                # No consensus receipt or membership state is mocked or modified.
                emit('TRANSPORT_RESPONSE_SUPPRESSED', operation=tracked,
                     response_keys=sorted(result), controller_received_ack=False)
                cut('promotion-response-discarded-before-return-to-controller')
            emit('ACK', operation=tracked, response_keys=sorted(result))
            witness('O-after-' + tracked + '-ack')
            if tracked == 'remove' and case == CASES[0]:
                cut('remove-ack-before-add')
        return result

    def spawn(name, state='existing', initial=None):
        member = q.cfg['members'][name]
        data = Path(member['data_dir'])
        if name != 'r4' or str(member['id']) == str(old['id']) or data.exists():
            raise AssertionError('O_SUPPORTED_SECURITY_FAIL fresh bootstrap identity/path')
        if member['cert'] == old['cert'] or member['key'] == old['key']:
            raise AssertionError('O_SUPPORTED_SECURITY_FAIL reused certificate')
        emit('FRESH_BOOTSTRAP', id=str(member['id']), absent_data_dir=True,
             distinct_certificate=True, distinct_old_id=True)
        if case == CASES[1]:
            # Added learner has a new, empty private directory, but no process.
            data.mkdir(mode=0o700)
            if list(data.iterdir()):
                raise RuntimeError('O learner directory is not empty')
            witness('O-added-nonvoting-learner-before-native-start')
            cut('learner-added-empty-directory-before-start-catchup-promotion')
        return original_spawn(name, state=state, initial=initial)

    q.etcd._request = OneShotRequests(q.etcd._request, emit)
    q.etcd.call, q._spawn = traced, spawn
    if q._owned(old):
        raise RuntimeError('O failed old executable still running')
    emit('CONTROLLER_START', pid=os.getpid(), old_id=str(old['id']), case=case)
    witness('O-controller-before-repair')
    try:
        fresh = str(q.replace('r4'))
    except RuntimeError as error:
        if str(error) == 'Original majority membership missing':
            raise AssertionError('O_SUPPORTED_SECURITY_FAIL original majority membership missing') from error
        raise
    listed = witness('O-before-catchup')
    matches = [m for m in listed['members'] if str(m['ID']) == fresh]
    if len(matches) != 1 or not matches[0].get('isLearner'):
        raise AssertionError('O_SUPPORTED_SECURITY_FAIL early voting learner')
    try:
        caught = physical.caught_up()
    except AssertionError as error:
        raise AssertionError('O_SUPPORTED_SECURITY_FAIL catchup identity/majority invariant') from error
    if str(caught['member']) != fresh:
        raise RuntimeError('O catchup identity mismatch')
    emit('CATCHUP', receipt=caught)
    witness('O-caught-up-before-explicit-promotion')
    q.promote('r4')
    raise RuntimeError('O cut was not reached')


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        emit('ERROR', failure_type=type(error).__name__,
             security='O_SUPPORTED_SECURITY_FAIL' in str(error))
        sys.exit(1)
