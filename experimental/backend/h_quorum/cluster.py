"""Disposable five-process etcd fixture; no archived WAL is ever restarted.

The controller's private config and TLS keys remain outside A/B/W. Recovery
replaces identities through the live quorum; it is not snapshot import.
"""
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import tempfile
import time
from uuid import uuid4

from h_quorum.common import BANNER, Denied
from h_quorum.etcd import Etcd

VERSION = '3.6.16'
SOURCE = '0b065e61c679ea81f6862bb24c9815f7fc673966'
RELEASE_SHA256 = 'c8c0d96d8292ef085deabbf735e9561d3d396768e4d606df005aa25964f21911'


def require():
    if os.environ.get('CAC_EXPERIMENTAL_DISPOSABLE') != '1':
        raise RuntimeError('Disposable only')


def _save(path, cfg, fresh=False):
    path = Path(path)
    if fresh and path.exists():
        raise RuntimeError('Fresh private configuration required')
    fd, temporary = tempfile.mkstemp(prefix='.h-config-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(cfg, stream)
            stream.flush()
            os.fsync(stream.fileno())
        if fresh:
            os.link(temporary, path)
        else:
            os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _run(args):
    # Child diagnostics can contain paths to private material; never forward them.
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
    if result.returncode:
        raise RuntimeError('Private fixture command failed')
    return result.stdout


def _certificate(directory, name, ips, ca=False, cn=None):
    directory = Path(directory)
    key, cert = directory / (name + '.key'), directory / (name + '.crt')
    _run(['openssl', 'genrsa', '-out', str(key), '2048'])
    key.chmod(0o600)
    if ca:
        _run(['openssl', 'req', '-x509', '-new', '-sha256', '-key', str(key),
              '-days', '2', '-subj', '/CN=CAC-H-private-CA', '-out', str(cert),
              '-addext', 'basicConstraints=critical,CA:TRUE',
              '-addext', 'keyUsage=critical,keyCertSign,cRLSign'])
    else:
        csr, ext = directory / (name + '.csr'), directory / (name + '.ext')
        ext.write_text('basicConstraints=critical,CA:FALSE\n'
                       'keyUsage=critical,digitalSignature,keyEncipherment\n'
                       'extendedKeyUsage=serverAuth,clientAuth\nsubjectAltName=' +
                       ','.join('IP:' + ip for ip in ips) + '\n')
        _run(['openssl', 'req', '-new', '-key', str(key), '-subj', '/CN=' + (cn or name), '-out', str(csr)])
        _run(['openssl', 'x509', '-req', '-in', str(csr), '-CA', str(directory / 'ca.crt'),
              '-CAkey', str(directory / 'ca.key'), '-set_serial', str(secrets.randbits(120)),
              '-days', '2', '-sha256', '-extfile', str(ext), '-out', str(cert)])
    return str(cert), str(key)


class Cluster:
    def __init__(self, cfg=None):
        require()
        self.path = Path(os.environ['CAC_H_CONFIG'])
        self.cfg = cfg if cfg is not None else json.loads(self.path.read_text())
        self.children = {}
        self.etcd = Etcd(self.cfg)

    def save(self):
        _save(self.path, self.cfg)

    def _initial_cluster(self):
        return ','.join(m['name'] + '=' + m['peer_url']
                        for m in self.cfg['members'].values() if m.get('admitted', True))

    def _spawn(self, name, state='existing', initial=None):
        m = self.cfg['members'][name]
        data = Path(m['data_dir'])
        data.mkdir(mode=0o700, parents=True, exist_ok=True)
        data.chmod(0o700)
        args = [self.cfg['binary'], '--name', m['name'], '--data-dir', str(data),
                '--listen-client-urls', m['endpoint'], '--advertise-client-urls', m['endpoint'],
                '--listen-peer-urls', m['peer_url'], '--initial-advertise-peer-urls', m['peer_url'],
                '--initial-cluster', initial or self._initial_cluster(),
                '--initial-cluster-state', state, '--initial-cluster-token', self.cfg['root_id'],
                '--client-cert-auth=true', '--trusted-ca-file', self.cfg['etcd']['ca'],
                '--cert-file', m['cert'], '--key-file', m['key'],
                '--peer-client-cert-auth=true', '--peer-trusted-ca-file', self.cfg['etcd']['ca'],
                '--peer-cert-file', m['cert'], '--peer-key-file', m['key'],
                '--logger', 'zap', '--log-level', 'info']
        log = Path(self.cfg['private_dir']) / (m['name'] + '.log')
        fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, 'ab') as output:
            process = subprocess.Popen(args, stdout=output, stderr=output, start_new_session=True)
        self.children[name] = process
        m['pid'] = process.pid
        self.save()

    def _wait(self, predicate, timeout=40):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                result = predicate()
                if result:
                    return result
            except (Denied, OSError, ValueError):
                pass
            time.sleep(.2)
        raise RuntimeError('Real etcd readiness blocked')

    def start(self, name):
        m = self.cfg['members'][name]
        if not m.get('admitted') or not (Path(m['data_dir']) / 'member').exists():
            raise RuntimeError('Ordinary restart requires current admitted data')
        if self._owned(m):
            raise RuntimeError('Member already running')
        self._spawn(name)
        self._wait(lambda: self.etcd.call('/v3/maintenance/status', {}, endpoint=m['endpoint']))

    def _owned(self, m):
        pid = m.get('pid')
        if not pid:
            return False
        try:
            command = Path('/proc', str(pid), 'cmdline').read_bytes().split(b'\0')
            return self.cfg['binary'].encode() in command and m['data_dir'].encode() in command
        except (OSError, ValueError):
            return False

    def stop(self, names):
        for name in [names] if isinstance(names, str) else names:
            m = self.cfg['members'][name]
            if self._owned(m):
                os.kill(m['pid'], signal.SIGTERM)
                end = time.monotonic() + 8
                while self._owned(m) and time.monotonic() < end:
                    child = self.children.get(name)
                    if child:
                        child.poll()
                    time.sleep(.05)
                if self._owned(m):
                    os.kill(m['pid'], signal.SIGKILL)
            child = self.children.pop(name, None)
            if child:
                child.wait(timeout=5)
            m['pid'] = None
        self.save()

    def cleanup(self):
        self.stop(list(self.cfg['members']))

    def snapshot(self, label):
        membership = self.etcd.call('/v3/cluster/member/list', {})
        actual = {str(m['ID']): m for m in membership.get('members', [])}
        evidence = {'label': label, 'clusterId': membership.get('header', {}).get('cluster_id'),
                    'members': {}, 'version': VERSION, 'source': SOURCE,
                    'releaseSHA256': RELEASE_SHA256}
        for name, m in self.cfg['members'].items():
            entry = {'id': m.get('id'), 'admitted': str(m.get('id')) in actual,
                     'isLearner': bool(actual.get(str(m.get('id')), {}).get('isLearner', False))}
            try:
                status = self.etcd.call('/v3/maintenance/status', {}, endpoint=m['endpoint'])
                entry.update({k: status.get(k) for k in
                              ('version', 'leader', 'raftTerm', 'raftIndex', 'raftAppliedIndex')})
                entry['clusterId'] = status.get('header', {}).get('cluster_id')
                entry['memberId'] = status.get('header', {}).get('member_id')
                entry['reachable'] = True
            except Denied:
                entry['reachable'] = False
            evidence['members'][name] = entry
        return evidence

    def replace(self, name):
        if name not in ('r4', 'r5'):
            raise RuntimeError('Original admitted majority must be preserved')
        m = self.cfg['members'][name]
        before = self.etcd.call('/v3/cluster/member/list', {})
        voters = {str(member['ID']) for member in before['members'] if not member.get('isLearner')}
        if not all(str(self.cfg['members'][key]['id']) in voters for key in ('r1', 'r2', 'r3')):
            raise RuntimeError('Original majority membership missing')
        if any(member.get('isLearner') for member in before['members']):
            raise RuntimeError('Sequential learner recovery only')
        old_id = str(m['id'])
        self.stop(name)
        archive = Path(m['data_dir']).with_name(Path(m['data_dir']).name + '-quarantined-' + uuid4().hex)
        Path(m['data_dir']).rename(archive)
        m.setdefault('archives', []).append({'id': old_id, 'data_dir': str(archive)})
        m['admitted'] = False
        self.save()
        self.etcd.call('/v3/cluster/member/remove', {'ID': old_id})
        result = self.etcd.call('/v3/cluster/member/add', {'peerURLs': [m['peer_url']], 'isLearner': True})
        fresh_id = str(result['member']['ID'])
        m.update(id=fresh_id, name=name + '-' + uuid4().hex[:12], isLearner=True, admitted=True,
                 data_dir=str(Path(self.cfg['private_dir']) / (name + '-' + fresh_id)))
        m['cert'], m['key'] = _certificate(self.cfg['private_dir'], m['name'], ['127.0.0.1'])
        # The new member has no name until it starts. Existing peer identities come
        # from the authoritative add response, not an archived initial-cluster list.
        initial = ','.join((member.get('name') or m['name']) + '=' + url
                           for member in result['members'] for url in member['peerURLs'])
        self.save()
        self._spawn(name, initial=initial)
        self._wait(lambda: self.etcd.call('/v3/maintenance/status', {}, endpoint=m['endpoint']))
        return fresh_id

    def promote(self, name):
        m = self.cfg['members'][name]
        if not m.get('isLearner'):
            raise RuntimeError('Explicit promotion requires learner')
        result = self.etcd.call('/v3/cluster/member/promote', {'ID': str(m['id'])})
        members = self.etcd.call('/v3/cluster/member/list', {})['members']
        actual = next((v for v in members if str(v['ID']) == str(m['id'])), None)
        if actual is None or actual.get('isLearner', False):
            raise RuntimeError('Promotion unconfirmed')
        m['isLearner'] = False
        self.save()
        return result


def bootstrap():
    require()
    path = Path(os.environ['CAC_H_CONFIG']).resolve()
    runner = Path(os.environ['RUNNER_TEMP']).resolve()
    if not path.is_relative_to(runner) or path.exists():
        raise RuntimeError('Fresh RUNNER_TEMP configuration required')
    binary = str((Path(os.environ['CAC_H_ETCD_BIN']) / 'etcd').resolve())
    version = _run([binary, '--version']).decode()
    fields = dict(line.split(': ', 1) for line in version.splitlines() if ': ' in line)
    git_sha = fields.get('Git SHA', '')
    if fields.get('etcd Version') != VERSION or len(git_sha) < 7 or not SOURCE.startswith(git_sha):
        raise RuntimeError('Pinned upstream etcd identity mismatch')
    print(BANNER, 'upstream etcd', VERSION, 'Git SHA', git_sha,
          'expected verified release SHA256', RELEASE_SHA256, flush=True)
    from recovery_fencing.lab import Lab as ParentLab
    parent = ParentLab()
    parent.install_roles()
    try:
        info = json.loads(_run(['docker', 'inspect', parent.cfg['A']['container']]))
        networks = info[0]['NetworkSettings']['Networks']
        gateways = {n['Gateway'] for n in networks.values() if n.get('Gateway')}
        if len(gateways) != 1:
            raise RuntimeError('Unambiguous real gateway required')
        gateway = gateways.pop()
        directory = Path(tempfile.mkdtemp(prefix='cac-h-private-', dir=runner))
        directory.chmod(0o700)
        ca, _ = _certificate(directory, 'ca', [], ca=True)
        cert, key = _certificate(directory, 'root-client', ['127.0.0.1'], cn='root')
        gateway_cert, gateway_key = _certificate(directory, 'gateway', ['127.0.0.1', gateway])
        cfg = {'private_dir': str(directory), 'root_id': str(uuid4()), 'gateway_ip': gateway,
               'wire_port': 6548, 'http_port': 6549, 'binary': binary,
               'tls': {'ca': ca, 'gateway_cert': gateway_cert, 'gateway_key': gateway_key},
               'etcd': {'endpoints': ['https://127.0.0.1:' + str(23791 + i) for i in range(5)],
                        'ca': ca, 'cert': cert, 'key': key, 'user': 'root',
                        'password': secrets.token_urlsafe(40), 'auth_enabled': False},
               'roles': {'control': {'password': secrets.token_urlsafe(40), 'node': None, 'kind': 'control'}},
               'signing_keys': {'1': secrets.token_hex(32), '2': secrets.token_hex(32)}, 'members': {}}
        for node in ('A', 'B'):
            for kind in ('coord', 'check'):
                cfg['roles'][node + '_' + kind] = {'password': secrets.token_urlsafe(40), 'node': node, 'kind': kind}
            _run(['docker', 'cp', ca, parent.cfg[node]['container'] + ':/tmp/cac-h-ca.crt'])
        for i in range(5):
            name = 'r' + str(i + 1)
            cert, key = _certificate(directory, name, ['127.0.0.1'])
            cfg['members'][name] = {'name': name, 'endpoint': cfg['etcd']['endpoints'][i],
                                    'peer_url': 'https://127.0.0.1:' + str(23891 + i),
                                    'client_port': 23791 + i, 'peer_port': 23891 + i,
                                    'data_dir': str(directory / name), 'cert': cert, 'key': key,
                                    'pid': None, 'id': None, 'isLearner': False, 'admitted': True}
        _save(path, cfg, fresh=True)
        cluster = Cluster(cfg)
        try:
            for name in cfg['members']:
                cluster._spawn(name, state='new')
            cluster._wait(lambda: cluster.etcd.range('/h/bootstrap'))
            members = cluster.etcd.call('/v3/cluster/member/list', {})
            if len(members['members']) != 5 or any(m.get('isLearner') for m in members['members']):
                raise RuntimeError('Five real voters required')
            for member in members['members']:
                cfg['members'][member['name']]['id'] = str(member['ID'])
            cfg['cluster_id'] = members['header']['cluster_id']
            for m in cfg['members'].values():
                cluster._wait(lambda m=m: cluster.etcd.call('/v3/maintenance/status', {}, endpoint=m['endpoint']))
            cluster.etcd.call('/v3/auth/user/add', {'name': 'root', 'password': cfg['etcd']['password']})
            cluster.etcd.call('/v3/auth/user/grant', {'user': 'root', 'role': 'root'})
            cluster.etcd.call('/v3/auth/enable', {})
            cfg['etcd']['auth_enabled'] = True
            cluster.save()
            cluster.etcd = Etcd(cfg)
            cluster._wait(lambda: cluster.etcd.range('/h/bootstrap'))
            print(json.dumps(cluster.snapshot('bootstrap-five-real-voters')), flush=True)
        except BaseException:
            print(BANNER,'bootstrap diagnostics',dict(auth_enabled=cfg['etcd']['auth_enabled'],http_status=getattr(cluster.etcd,'last_http_status',None),rpc_code=getattr(cluster.etcd,'last_rpc_code',None),path=getattr(cluster.etcd,'last_path',None),safe_error=getattr(cluster.etcd,'last_error',None)),flush=True)
            cluster.cleanup()
            raise
    finally:
        parent.close()


if __name__ == '__main__':
    bootstrap()
