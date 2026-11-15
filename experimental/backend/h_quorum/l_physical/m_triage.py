"""S0-09M: finite observations only; never change Raft or authorize member repair."""
import copy
import json
import os
import re
import signal
import socket
import ssl
import urllib.error
import time
from uuid import uuid4

from h_quorum.authority import Root
from h_quorum.cluster import Cluster
from h_quorum.common import BANNER, Denied
from h_quorum.etcd import b64, unb64, _Expired, _Unavailable
from h_quorum.l_physical.fixture import Physical
from h_quorum.retirement import adopt_policy
from h_quorum.rpc import Client
from recovery_fencing.lab import S1

# Frozen before the first M observation; no outcome-driven case/repetition growth.
CASES = {
    'OFFLINE_OLD_CLEAN': dict(progress=False, kill=False, archive=True),
    'PROGRESSED_OLD_CLEAN': dict(progress=True, kill=False, archive=True),
    'PROGRESSED_OLD_KILL': dict(progress=True, kill=True, archive=True),
    'PROGRESSED_CURRENT_KILL': dict(progress=True, kill=True, archive=False),
}
REPETITIONS = (1, 2)
PROGRESS_PUTS = 16
OBSERVE_SECONDS = 40


def emit(kind, value):
    print(BANNER, 'M '+kind, json.dumps(value, sort_keys=True), flush=True)


def state_summary(state, revision, history):
    return dict(head=state['head'], revision=revision, epoch=state['epoch'], policy=state['policy'],
                seq=state['seq'], complete_journal=len(history),
                open=sum(o['phase']=='OPEN' for o in state['ops'].values()),
                unknown=sum(o['phase']=='UNKNOWN' for o in state['ops'].values()))


class ObservedPhysical(Physical):
    def __init__(self, lab):
        super().__init__(lab)
        self.phase='archive'
        self.frozen=False
        self.stops=[]
        self.highest_index=0

    def status(self, label):
        m=self.q.cfg['members']['r4']
        value=self.q.etcd.call('/v3/maintenance/status',{},endpoint=m['endpoint'])
        if str(value['header']['member_id'])!=str(m['id']):
            raise AssertionError('M TEST_HARNESS_FAILURE wrong observed member ID')
        result={k:value.get(k) for k in ('raftTerm','raftIndex','raftAppliedIndex','leader','version')}
        result.update(member=str(value['header']['member_id']),cluster=str(value['header']['cluster_id']),label=label)
        self.highest_index=max(self.highest_index,int(value['raftIndex']))
        emit('NATIVE_STATUS',result)
        return result

    def stop(self):
        record=copy.deepcopy(self.q.cfg['members']['r4'])
        status=None
        if self.q._owned(record) and not self.frozen:
            status=self.status(self.phase+'-before-stop')
        start=time.monotonic()
        super().stop()
        proof=dict(phase=self.phase,pid=record.get('pid'),member=record['id'],status=status,
                   executable_absent=not self.q._owned(record),frozen=self.frozen,
                   elapsed_seconds=round(time.monotonic()-start,6))
        self.stops.append(proof); emit('STOP_PROOF',proof)



def clean_stop_receipt(test,child,log):
    code=child.wait(timeout=5)
    records=[]
    for line in log.read_text().splitlines():
        try:records.append(json.loads(line))
        except ValueError:pass
    # Upstream osutil resets the default handler and re-raises SIGTERM after
    # e.Close(). Therefore -SIGTERM is a documented clean result, not SIGKILL.
    signal_seen=any(r.get('msg')=='received signal; shutting down' and r.get('signal')=='terminated' for r in records)
    closed=any(r.get('msg')=='closed etcd server' for r in records)
    test.assertIn(code,(0,-signal.SIGTERM),'M native clean stop did not use TERM completion')
    test.assertTrue(signal_seen and closed,'M clean stop lacks native signal and closed-server ACK')
    return dict(exit_code=code,received_sigterm=signal_seen,closed_server=closed)


def native_receipt(physical, child, log):
    records=[]; functions=set()
    for line in log.read_text().splitlines():
        try: value=json.loads(line)
        except ValueError:
            functions.update(re.findall(r'go\.etcd\.io/raft/v3\.\(\*[^)]+\)\.[A-Za-z_0-9]+',line))
            functions.update(re.findall(r'go\.etcd\.io/raft/v3\.(?:stepFollower|stepCandidate|stepLeader)',line))
            continue
        records.append(value)
    expected=format(int(physical.q.cfg['members']['r4']['id']),'x')
    ids={str(v.get('local-member-id','')).lower().removeprefix('0x').lstrip('0') for v in records}
    code=child.poll()
    result=dict(exit_code=code,member=physical.q.cfg['members']['r4']['id'],
                native_id_confirmed=expected.lstrip('0') in ids,stack_functions=sorted(functions))
    panics=[]
    for value in records:
        match=re.fullmatch(r'tocommit\((\d+)\) is out of range \[lastIndex\((\d+)\)\]\. Was the raft log corrupted, truncated, or lost\?',str(value.get('msg','')))
        if value.get('level')=='panic' and match:
            panics.append(dict(message=value['msg'],tocommit=int(match[1]),last_index=int(match[2])))
    if code==2 and result['native_id_confirmed'] and len(panics)==1 and panics[0]['tocommit']>panics[0]['last_index']:
        result.update(outcome='NATIVE_FAIL_STOP_EXIT2',panic=panics[0])
    elif code==1 and result['native_id_confirmed'] and any('permanently removed' in (str(v.get('msg',''))+' '+str(v.get('error',''))).lower() for v in records):
        result.update(outcome='NATIVE_REFUSAL_EXIT1',reason='native permanently removed identity')
    else:
        result.update(outcome='TEST_HARNESS_FAILURE',reason='unrecognized native process exit')
    return result


def observe(physical, target, revision, history):
    child,log=physical.last_native
    start=time.monotonic(); deadline=start+OBSERVE_SECONDS
    last=None; probe_errors={}
    def probe_range(key,prefix=False,at_revision=None):
        body=dict(key=b64(key),serializable=True)
        if prefix:body['range_end']=b64(key[:-1]+'0') # journal/ -> journal0
        if at_revision is not None:body['revision']=str(at_revision)
        return physical.q.etcd._request(physical.q.cfg['members']['r4']['endpoint'],
                                       '/v3/kv/range',body,physical.q.etcd.token)
    while time.monotonic()<deadline:
        if child.poll() is not None:
            result=native_receipt(physical,child,log)
            result['elapsed_seconds']=round(time.monotonic()-start,6)
            return result
        try:
            # M-only typed probe: inherited call() intentionally collapses errors.
            physical.q.etcd._authenticate(physical.q.cfg['members']['r1']['endpoint'])
            reply=probe_range('/cac-h/'+physical.lab.namespace+'/state')
            rows=reply.get('kvs',[])
            if not rows:
                probe_errors['state_not_yet_applied']=probe_errors.get('state_not_yet_applied',0)+1
                time.sleep(.1); continue
            if len(rows)!=1:raise AssertionError('M invalid local state row count')
            state=json.loads(unb64(rows[0]['value'])); local_revision=int(rows[0]['mod_revision']); header=reply['header']
            last=dict(head=state['head'],revision=local_revision,policy=state['policy'],member=str(header['member_id']))
            if str(header['cluster_id'])!=str(physical.q.cfg['cluster_id']) or str(header['member_id'])!=str(physical.original['id']):
                raise AssertionError('M TEST_HARNESS_FAILURE native identity/cluster mismatch')
            if state==target and local_revision==revision:
                rows=probe_range('/cac-h/'+physical.lab.namespace+'/journal/',prefix=True,at_revision=revision).get('kvs',[])
                wanted=[(r['key'],r['value'],r['mod_revision']) for r in history]
                if [(r['key'],r['value'],r['mod_revision']) for r in rows]==wanted:
                    status=physical.status('after-current-catchup')
                    return dict(outcome='CATCH_UP_SAME_ID',exit_code=child.poll(),member=str(header['member_id']),
                                current=last,status=status,complete_journal=len(rows),
                                elapsed_seconds=round(time.monotonic()-start,6),probe_errors=probe_errors)
        except (_Expired,_Unavailable) as error:
            category=type(error).__name__
            probe_errors[category]=probe_errors.get(category,0)+1
        except (urllib.error.URLError,ConnectionError,TimeoutError) as error:
            reason=getattr(error,'reason',error)
            if isinstance(reason,ssl.SSLError) or not isinstance(reason,(ConnectionError,TimeoutError,socket.timeout)):
                raise AssertionError('M typed probe configuration/transport failure') from error
            category=type(reason).__name__
            probe_errors[category]=probe_errors.get(category,0)+1
        except Denied as error:
            raise AssertionError('M typed probe authentication/permission/protocol failure') from error
        time.sleep(.1)
    # Do not translate a deadline into abort, removal, repair or catch-up.
    if child.poll() is not None:
        result=native_receipt(physical,child,log)
        result['elapsed_seconds']=round(time.monotonic()-start,6)
        return result
    return dict(outcome='TEST_HARNESS_FAILURE' if probe_errors.get('_Expired') else 'TIMEOUT_UNRESOLVED',
                reason='unresolved auth expiry' if probe_errors.get('_Expired') else 'bounded native availability observation',
                probe_errors=probe_errors,exit_code=None,member=physical.original['id'],last_local=last,
                elapsed_seconds=round(time.monotonic()-start,6),deadline_seconds=OBSERVE_SECONDS)


def run_sample(test,lab,broker,case,repetition):
    if case not in CASES or repetition not in REPETITIONS:
        raise AssertionError('M TEST_HARNESS_FAILURE case/repetition outside frozen matrix')
    specification=CASES[case]
    row=dict(case=case,repetition=repetition,status='TEST_HARNESS_FAILURE',member_repair='NOT_RUN',
             fixed_progress_puts=PROGRESS_PUTS if specification['progress'] else 0)
    physical=ObservedPhysical(lab)
    test.addCleanup(physical.close)
    emit('FROZEN_SAMPLE',dict(case=case,repetition=repetition,specification=specification))
    body={'body':'synthetic-M-'+case}
    try:
        with broker.runtime(action='probe',body=body) as gate:
            gate.install(broker.issue(gate.challenge(),action='probe',body=body))
            test.assertEqual(gate.records(),[S1])
            test.assertEqual(gate.c.execute('UPDATE poc.records SET body=%s WHERE store=%s',(body['body'],S1)).rowcount,1)
            row['postgres_before']=dict(pid=gate.pid,fullxid=gate.tx,system_id=gate.sid)
            physical.archive_current()
            archive_stop=clean_stop_receipt(test,*physical.last_native)
            archive_exit=archive_stop['exit_code']; row['archive_stop']=archive_stop
            row['archive_root']=physical.old
            row['archive_files']=physical.manifest
            row['archive_stop_status']=physical.stops[-1]['status']
            if specification['progress']:
                physical.phase='resume-progress'; child,_=physical.spawn(); physical.caught_up()
                row['resumed_status']=physical.status('resumed-before-fixed-puts')
                prefix='/cac-m-progress/'+uuid4().hex+'/'
                for n in range(PROGRESS_PUTS):
                    physical.q.etcd.call('/v3/kv/put',dict(key=b64(prefix+str(n)),value=b64(str(n))))
                def applied():
                    value=physical.q.etcd.range(prefix+str(PROGRESS_PUTS-1),serializable=True,
                                               endpoint=physical.q.cfg['members']['r4']['endpoint']).get('kvs',[])
                    return len(value)==1 and unb64(value[0]['value'])==str(PROGRESS_PUTS-1).encode()
                physical.q._wait(applied)
                row['progress_status']=physical.status('fixed-puts-locally-applied')
                test.assertGreaterEqual(int(row['progress_status']['raftAppliedIndex']),int(row['archive_stop_status']['raftAppliedIndex'])+PROGRESS_PUTS)
                physical.phase='final-stop'
                if specification['kill']:
                    record=copy.deepcopy(physical.q.cfg['members']['r4'])
                    os.kill(record['pid'],signal.SIGSTOP); physical.frozen=True
                    physical.q=Cluster(); test.assertFalse(physical.q.children)
                    physical.stop(); physical.frozen=False
                    test.assertFalse(physical.q._owned(record),'M old executable remains before file selection')
                    test.assertEqual(child.wait(timeout=5),-signal.SIGKILL)
                    row['stop_kind']='SIGSTOP_NONCHILD_SIGKILL'; row['stopped_exit']=-signal.SIGKILL
                else:
                    physical.stop(); row['clean_stop']=clean_stop_receipt(test,*physical.last_native)
                    row['stopped_exit']=row['clean_stop']['exit_code']
                    row['stop_kind']='CLEAN_SIGTERM'
            else:
                row['stop_kind']='ALREADY_OFFLINE_CLEAN_SIGTERM'; row['stopped_exit']=archive_exit
            row['stop_proofs']=physical.stops
            data=physical.path(physical.q.cfg['members']['r4']['data_dir'])
            current_files=physical.inventory(data); row['sealed_current_files']=current_files
            if specification['progress']:
                test.assertNotEqual(current_files,physical.manifest,'M progressed files did not change')
            control=Client(lab.rootcfg,'control',lab.namespace)
            cut=control.call('retire_policy',dict(expected=1,new=2,request=str(uuid4())))
            test.assertEqual(cut['policy'],2); lab.replay()
            target,revision,history=Root(lab.rootcfg).read(lab.namespace,True)
            test.assertGreaterEqual(sum(o['phase']=='OPEN' for o in target['ops'].values()),1)
            test.assertEqual(physical.inventory(data),current_files,'M stopped file bytes changed during authority cut')
            row['before_observation']=state_summary(target,revision,history)
            physical.majority_current('M-before-file-selection')
            if specification['archive']:
                data.rename(physical.private/'sealed-pre-replay-current')
                physical.copy_archive(data); expected=physical.manifest
            else:
                expected=current_files
            imported=physical.inventory(data)
            test.assertEqual(imported,expected,'M selected file bytes differ before native start')
            row['started_files']=imported; row['used_old_archive']=specification['archive']
            row['highest_prestart_observed_index']=physical.highest_index
            physical.phase='observation'; physical.spawn()
            try:outcome=observe(physical,target,revision,history)
            except (AssertionError,ValueError,KeyError,OSError) as probe_error:
                outcome=dict(outcome='TEST_HARNESS_FAILURE',reason='typed diagnostic failed',failure_type=type(probe_error).__name__)
            row['native']=outcome
            row['highest_observed_index']=physical.highest_index
            physical.majority_current('M-after-native-observation-before-known-outcome')
            actual=Root(lab.rootcfg).read(lab.namespace,True)
            test.assertEqual(actual,(target,revision,history),'M_SUPPORTED_SECURITY_FAIL Root/OPEN/journal changed across minority replay')
            row['after_observation']=state_summary(*actual)
            test.assertFalse(broker.ready(),'M_SUPPORTED_SECURITY_FAIL old-policy readiness accepted')
            try:
                with broker.runtime():test.fail('M_SUPPORTED_SECURITY_FAIL old policy admitted')
            except Denied:pass
            with lab.connect('A','cac_ctx_issuer') as issuer:
                test.assertEqual(issuer.execute('SELECT fence.is_ready()').fetchone(),(False,),'M_SUPPORTED_SECURITY_FAIL old issuer ready')
            # No data access with a token held past its TTL is required. The
            # write was authorized before archival; Gate proves exact local
            # transaction/COMMIT ACK and only then closes its original grant.
        final=Root(lab.rootcfg).read(lab.namespace)[0]
        test.assertEqual(final['ops'][gate.operation]['phase'],'CLOSED_COMMIT')
        adopt_policy(lab)
        test.assertTrue(broker.ready(),'M current policy2 path unavailable before any repair')
        with broker.runtime() as fresh:
            test.assertEqual(fresh.binding['policy'],2,'M_SUPPORTED_SECURITY_FAIL wrong current admission policy')
            try:
                broker.command('admit',dict(fresh.binding,policy=1,request=str(uuid4()),operation=str(uuid4())))
            except Denied:pass
            else:test.fail('M_SUPPORTED_SECURITY_FAIL explicit policy1 admission accepted')
            fresh.install(broker.issue(fresh.challenge()))
            test.assertEqual(fresh.records(),[S1])
            test.assertEqual(fresh.c.execute('SELECT body FROM poc.records WHERE store=%s',(S1,)).fetchone(),(body['body'],))
            row['healthy_current_postgres_before_repair']=dict(pid=fresh.pid,fullxid=fresh.tx,system_id=fresh.sid,policy=2,scoped_read=True,committed_body=True)
        physical.majority_current('M-after-healthy-current-SQL-no-repair')
        row['majority_ids']={n:m['id'] for n,m in physical.majority.items()}
        test.assertNotEqual(outcome['outcome'],'TEST_HARNESS_FAILURE',json.dumps(outcome))
        row['status']='OBSERVED'; row['p1_closed']=False
        emit('OBSERVATION',row)
        return row
    except BaseException as error:
        row['status']='M_SUPPORTED_SECURITY_FAIL' if 'M_SUPPORTED_SECURITY_FAIL' in str(error) else 'TEST_HARNESS_FAILURE'
        # Exception text could contain private connection diagnostics: keep only type.
        row['failure_type']=type(error).__name__
        emit('OBSERVATION',row)
        raise
