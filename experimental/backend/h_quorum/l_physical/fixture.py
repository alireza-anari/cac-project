"""Disposable native minority byte replay; NEVER a majority/production restore API."""
import copy
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from uuid import uuid4

from h_quorum.authority import Root
from h_quorum.cluster import Cluster
from h_quorum.common import BANNER, Denied
from h_quorum.etcd import b64, unb64


class Physical:
    def __init__(self, lab):
        self.lab = lab
        self.q = Cluster()
        self.majority = {n: copy.deepcopy(self.q.cfg['members'][n]) for n in ('r1','r2','r3')}
        self.original = copy.deepcopy(self.q.cfg['members']['r4'])
        self.base = Path(self.q.cfg['private_dir']).resolve()
        self.private = Path(tempfile.mkdtemp(prefix='l-native-', dir=self.base))
        self.private.chmod(0o700)
        self.archive = self.private / 'stopped-original-data'
        self.manifest = None
        self.old = None
        self.command_receipts = []
        self.stopped_records = []
        self.last_native = None
        self.last_local = None

    def stop(self):
        # Cluster.stop may clear a bootstrap-owned PID immediately after SIGKILL.
        # Retain its original identity and prove that executable is gone before
        # any copy/rename/restart, including the non-child forced-stop branch.
        record=copy.deepcopy(self.q.cfg['members']['r4'])
        self.q.stop('r4')
        deadline=time.monotonic()+5
        while self.q._owned(record):
            if time.monotonic()>deadline:raise AssertionError('Minority process not terminated; native import forbidden')
            time.sleep(.02)
        self.stopped_records.append(record)
        print(BANNER,'L STOP PROVEN original minority executable absent',record.get('pid'),record['id'],flush=True)

    def path(self, value):
        p = Path(value)
        if p.is_symlink() or not p.resolve().is_relative_to(self.base) or p.resolve() == self.base:
            raise AssertionError('Physical replay path outside owned private fixture')
        protected = [Path(m['data_dir']).resolve() for n,m in self.q.cfg['members'].items() if n != 'r4']
        if any(p.resolve().is_relative_to(x) or x.is_relative_to(p.resolve()) for x in protected):
            raise AssertionError('Physical replay cannot touch another member data directory')
        if p.exists() and any(x.is_symlink() for x in p.rglob('*')):
            raise AssertionError('Physical replay symlink denied')
        return p

    def majority_current(self, label):
        membership = self.q.etcd.call('/v3/cluster/member/list', {})
        voters = {str(m['ID']) for m in membership['members'] if not m.get('isLearner')}
        target, revision = Root(self.lab.rootcfg).read(self.lab.namespace)
        statuses = {}
        for n, original in self.majority.items():
            m = self.q.cfg['members'][n]
            if any(m[k] != original[k] for k in ('id','pid','data_dir')) or not self.q._owned(m):
                raise AssertionError('Original current majority identity/process changed')
            status = self.q.etcd.call('/v3/maintenance/status', {}, endpoint=m['endpoint'])
            if str(m['id']) not in voters or str(status['header']['member_id']) != str(m['id']):
                raise AssertionError('Original majority membership mismatch')
            def current_local():
                result=self.q.etcd.range('/cac-h/'+self.lab.namespace+'/state',serializable=True,endpoint=m['endpoint'])
                rows=result.get('kvs',[])
                return len(rows)==1 and int(rows[0]['mod_revision'])==revision and json.loads(unb64(rows[0]['value']))==target
            self.q._wait(current_local)
            statuses[n] = {k: status[k] for k in ('raftTerm','raftIndex','raftAppliedIndex')}
        print(BANNER, 'L ORIGINAL CURRENT MAJORITY', json.dumps(dict(label=label,
              ids={n:m['id'] for n,m in self.majority.items()}, statuses=statuses,
              head=target['head'],revision=revision,policy=target['policy'],seq=target['seq'],all_three_local_state_equal=True)), flush=True)
        return statuses

    def inventory(self, directory):
        directory = self.path(directory)
        result = {}
        for p in sorted(directory.rglob('*')):
            if p.is_file():
                digest = hashlib.sha256()
                with p.open('rb') as stream:
                    for block in iter(lambda: stream.read(1024*1024), b''): digest.update(block)
                result[str(p.relative_to(directory))] = dict(size=p.stat().st_size, sha256=digest.hexdigest())
        return result

    def spawn(self, name='r4', small_snapshot=False):
        if name != 'r4': raise AssertionError('Physical spawn restricted to minority r4')
        m = self.q.cfg['members'][name]
        if self.q._owned(m): raise AssertionError('Concurrent same-ID process forbidden')
        if any(self.q._owned(record) for record in self.stopped_records):
            raise AssertionError('Prior minority process remains live; spawn forbidden')
        data = self.path(m['data_dir']); data.mkdir(mode=0o700, parents=True, exist_ok=True)
        args = [self.q.cfg['binary'], '--name', m['name'], '--data-dir', str(data),
                '--listen-client-urls', m['endpoint'], '--advertise-client-urls', m['endpoint'],
                '--listen-peer-urls', m['peer_url'], '--initial-advertise-peer-urls', m['peer_url'],
                '--initial-cluster', self.q._initial_cluster(), '--initial-cluster-state', 'existing',
                '--initial-cluster-token', self.q.cfg['root_id'], '--client-cert-auth=true',
                '--trusted-ca-file', self.q.cfg['etcd']['ca'], '--cert-file', m['cert'], '--key-file', m['key'],
                '--peer-client-cert-auth=true', '--peer-trusted-ca-file', self.q.cfg['etcd']['ca'],
                '--peer-cert-file', m['cert'], '--peer-key-file', m['key'], '--logger', 'zap', '--log-level', 'info']
        if small_snapshot: args += ['--snapshot-count=10']
        log = self.private / ('native-' + uuid4().hex + '.log')
        fd = os.open(log, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
        with os.fdopen(fd, 'ab') as output:
            child = subprocess.Popen(args, stdout=output, stderr=output, start_new_session=True)
        self.q.children[name] = child; m['pid'] = child.pid; self.q.save()
        self.last_native = (child, log)
        self.last_local = None # Never present a pre-restart read as a live response.
        # Full commands remain private (TLS paths); safe receipt records exact flags.
        flags = [a.split('=',1)[0] for a in args[1:] if a.startswith('--')]
        self.command_receipts.append(dict(member=m['id'], flags=flags, small_snapshot=small_snapshot))
        print(BANNER, 'L NATIVE SPAWN', json.dumps(self.command_receipts[-1]), flush=True)
        return child, log

    def local(self):
        self.q.etcd._authenticate(self.q.cfg['members']['r1']['endpoint'])
        result = self.q.etcd.range('/cac-h/'+self.lab.namespace+'/state', serializable=True,
                                   endpoint=self.q.cfg['members']['r4']['endpoint'])
        if len(result.get('kvs',[])) != 1: raise Denied('Minority namespace not yet applied')
        row = result['kvs'][0]
        value=json.loads(unb64(row['value']))
        self.last_local=dict(head=value['head'],policy=value['policy'],seq=value['seq'],revision=int(row['mod_revision']),member=result['header']['member_id'])
        return value, int(row['mod_revision']), result['header']

    def caught_up(self):
        target, revision, history = Root(self.lab.rootcfg).read(self.lab.namespace, True)
        def current():
            state, observed, header = self.local()
            if state != target or observed != revision: return False
            if str(header['member_id']) != str(self.q.cfg['members']['r4']['id']):
                raise AssertionError('Wrong native member ID after catch-up')
            rows = self.q.etcd.range('/cac-h/'+self.lab.namespace+'/journal/', prefix=True,
                                     revision=revision, serializable=True,
                                     endpoint=self.q.cfg['members']['r4']['endpoint']).get('kvs',[])
            if [(r['key'],r['value'],r['mod_revision']) for r in rows] != [(r['key'],r['value'],r['mod_revision']) for r in history]:
                return False
            return dict(member=header['member_id'], cluster=header['cluster_id'], revision=revision,
                        head=target['head'], policy=target['policy'], seq=target['seq'], complete_journal=len(rows))
        try:
            receipt = self.q._wait(current)
        except RuntimeError:
            child, log = self.last_native
            messages=[]
            for line in log.read_text().splitlines():
                try: record=json.loads(line)
                except ValueError: continue
                msg=str(record.get('msg',''))
                safe={k:record[k] for k in ('level','local-member-id','cluster-id','term','index','commit-index','applied-index') if k in record}
                safe['msg']=msg[:200]
                error=str(record.get('error','')).lower()
                if error:safe['error_categories']=[w for w in ('removed','corrupt','wal','snapshot','bind','already','timeout','auth','refused','mismatch') if w in error]
                messages.append(safe)
            print(BANNER,'L NATIVE CONVERGENCE FAILURE DIAGNOSTICS',json.dumps(dict(exit=child.poll(),
                  target_head=target['head'],target_revision=revision,last_local=self.last_local,
                  rpc_code=getattr(self.q.etcd,'last_rpc_code',None),native=messages[-22:])),flush=True)
            raise
        self.majority_current('after-native-catchup')
        print(BANNER, 'L LITERAL NATIVE CATCHUP', json.dumps(receipt), flush=True)
        return receipt

    def archive_current(self):
        self.majority_current('before-native-archive')
        self.stop()
        self.spawn(small_snapshot=True)
        self.q._wait(lambda: self.local())
        # Native member-local Raft snapshots, not an application export.
        for i in range(40):
            self.q.etcd.call('/v3/kv/put', dict(key=b64('/cac-l-snapshot/'+uuid4().hex), value=b64(str(i))))
        data = self.path(self.q.cfg['members']['r4']['data_dir'])
        self.q._wait(lambda: list((data/'member/snap').glob('*.snap')))
        self.old = self.caught_up()
        self.old_response = self.local()
        self.stop()
        if self.q._owned(self.q.cfg['members']['r4']): raise AssertionError('Archive requires stopped member')
        shutil.copytree(data, self.archive)
        self.manifest = self.inventory(self.archive)
        if self.manifest != self.inventory(data): raise AssertionError('Stopped native archive copy mismatch')
        if not any(p.endswith('.wal') for p in self.manifest) or not any(p.endswith('.snap') for p in self.manifest) or 'member/snap/db' not in self.manifest:
            raise AssertionError('L_PHYSICAL_IMPORT_NOT_RUN: native WAL/snapshot/db missing')
        print(BANNER, 'L STOPPED NATIVE ARCHIVE', json.dumps(dict(member=self.original['id'],
              old=self.old, files=self.manifest, method='SIGTERM wait; shutil.copytree full stopped data-dir; sha256 each file')), flush=True)
        self.majority_current('archive-stopped-r4-only')
        return self.old

    def copy_archive(self, target):
        if self.q._owned(self.q.cfg['members']['r4']): raise AssertionError('Cannot restore running member')
        target = self.path(target)
        if target.exists(): raise AssertionError('Physical restore requires absent target')
        if self.inventory(self.archive) != self.manifest: raise AssertionError('Private source archive changed')
        shutil.copytree(self.archive, target)
        if self.inventory(target) != self.manifest: raise AssertionError('Imported bytes differ before native restart')
        print(BANNER, 'L EXACT NATIVE BYTES REIMPORTED before spawn', json.dumps(self.manifest), flush=True)

    def replay(self):
        self.majority_current('before-stale-native-replay')
        current, revision = Root(self.lab.rootcfg).read(self.lab.namespace)
        if current['head'] == self.old['head'] or revision <= self.old['revision']:
            raise AssertionError('Native archive must predate genuine committed authority transition')
        self.stop()
        data = self.path(self.q.cfg['members']['r4']['data_dir'])
        quarantine = self.private / ('superseded-'+uuid4().hex)
        data.rename(quarantine)
        self.copy_archive(data)
        self.spawn()
        result = self.caught_up()
        print(BANNER, 'L ARCHIVED HEAD != CURRENT HEAD', self.old['head'], result['head'], flush=True)
        return result

    def incompatible_attempt(self, learner_identity=False):
        # Native replacement first; removed old ID is never concurrently active.
        self.stop(); self.q.replace('r4')
        self.caught_up()
        fresh = copy.deepcopy(self.q.cfg['members']['r4'])
        self.stop(); fresh['pid'] = None
        fresh_data = self.path(fresh['data_dir'])
        backup = self.private / ('valid-learner-'+uuid4().hex)
        fresh_data.rename(backup)
        attempt = copy.deepcopy(fresh if learner_identity else self.original)
        attempt['pid'] = None
        attempt['data_dir'] = str(fresh_data)
        self.q.cfg['members']['r4'] = attempt; self.q.save()
        self.copy_archive(fresh_data)
        child, log = self.spawn()
        try:
            child.wait(timeout=25)
            messages = []
            for line in log.read_text().splitlines():
                try: record=json.loads(line)
                except ValueError: continue
                msg=record.get('msg',''); error=record.get('error','')
                if any(w in msg.lower() for w in ('removed','restarting','local member','initialized')) or 'permanently removed' in error.lower():
                    safe={k:record[k] for k in ('level','msg','local-member-id','local-member-id-from-data-dir','cluster-id') if k in record}
                    if 'permanently removed' in error.lower():safe['error']='etcdserver: the member has been permanently removed from the cluster'
                    messages.append(safe)
            if not any('permanently removed' in (m.get('msg','')+' '+m.get('error','')).lower() for m in messages):
                raise AssertionError('Native incompatible bytes did not produce evidenced removed-member refusal: '+json.dumps(messages))
            old_hex = format(int(self.original['id']), 'x')
            if not any(str(m.get('local-member-id','')).lower().removeprefix('0x').lstrip('0') == old_hex.lstrip('0') for m in messages):
                raise AssertionError('Native removed-member diagnostic lacks original on-disk member identity: '+json.dumps(messages))
            receipt=dict(mode='learner-config-old-bytes' if learner_identity else 'removed-old-member',
                         old_id=self.original['id'], expected_learner_id=fresh['id'], exit=child.returncode, native=messages)
            print(BANNER, 'L NATIVE INCOMPATIBLE REFUSAL', json.dumps(receipt), flush=True)
            self.majority_current('native-refusal-majority-untouched')
            return receipt
        finally:
            self.stop()
            self.q.cfg['members']['r4'] = fresh; self.q.save()
            bad = self.private / ('rejected-data-'+uuid4().hex)
            fresh_data.rename(bad); backup.rename(fresh_data)
            self.q.etcd._authenticate(self.q.cfg['members']['r1']['endpoint'])
            self.q.start('r4'); self.caught_up()
            self.q._wait(lambda: self.q.promote('r4'))
            self.majority_current('valid-fresh-learner-recovery')

    def classified_replay_after_progress(self):
        """Issue47 permits actual catch-up OR evidenced native refusal.

        A leader may remember a match index newer than physically restored WAL.
        Native Raft's explicit out-of-range fail-stop is availability evidence,
        not recovered membership and never permission to use old authority.
        """
        try:
            return dict(kind='caught_up',receipt=self.replay())
        except RuntimeError:
            child, log = self.last_native
            if child.poll()!=2:raise
            messages=[]; identities=[]
            for line in log.read_text().splitlines():
                try:record=json.loads(line)
                except ValueError:continue
                if record.get('local-member-id'):identities.append(str(record['local-member-id']).lower())
                msg=str(record.get('msg',''))
                if record.get('level')=='panic' and re.fullmatch(r'tocommit\(\d+\) is out of range \[lastIndex\(\d+\)\]\. Was the raft log corrupted, truncated, or lost\?',msg):
                    messages.append(msg)
            expected=format(int(self.q.cfg['members']['r4']['id']),'x')
            if len(messages)!=1 or expected not in identities:raise
            self.majority_current('native-raft-fail-stop-current-majority')
            receipt=dict(kind='native_raft_fail_stop',member=self.q.cfg['members']['r4']['id'],exit=2,panic=messages[0])
            print(BANNER,'L ACTUAL NATIVE RAFT FAIL_STOP not catchup',json.dumps(receipt),flush=True)
            return receipt

    def repair_fresh_after_native_refusal(self):
        old=self.q.cfg['members']['r4']['id']
        self.stop(); fresh=self.q.replace('r4')
        if fresh==old:raise AssertionError('Native refusal repair must use fresh learner identity')
        result=self.caught_up(); self.q._wait(lambda:self.q.promote('r4'))
        self.majority_current('fresh-identity-after-actual-native-refusal')
        print(BANNER,'L FRESH LEARNER REPAIR AFTER literal old-byte refusal',old,'->',fresh,flush=True)
        return result

    def close(self):
        # Never erase active data dirs. Actual archive bytes contain synthetic
        # auth state and remain private; only their hashes go to safe artifacts.
        if self.private.exists(): shutil.rmtree(self.private)
