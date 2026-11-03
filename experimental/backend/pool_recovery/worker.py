"""Runtime process: one runtime DB credential, synthetic session proof, no issuer secret."""
import json
import os
from pathlib import Path
import socket
import sys
import psycopg

cfg = json.loads(Path(sys.argv[1]).read_text())
c = psycopg.connect(**cfg['connection'], user=cfg['role'], password=cfg['password'], prepare_threshold=None)

def rpc(r=None, raw=None):
    with socket.socket(socket.AF_UNIX) as s:
        s.settimeout(5)
        s.connect(cfg['socket'])
        s.sendall(raw.encode() if raw is not None else json.dumps(r).encode() + b'\n')
        s.shutdown(socket.SHUT_WR)
        b = b''
        while not b.endswith(b'\n'):
            part = s.recv(4096)
            if not part: raise ValueError('issuer closed')
            b += part
        return json.loads(b)

def request(h, **kw):
    r = dict(challenge=h, proof=cfg['proof'], store=sys.argv[4], action='read', target=sys.argv[5], body={})
    r.update(kw)
    return r

def run(op, a):
    if op == 'isolation':
        denied = []
        for p in [sys.argv[2], '/proc/'+sys.argv[3]+'/environ']:
            try: Path(p).read_bytes(); denied.append(False)
            except PermissionError: denied.append(True)
        return dict(different_uid=os.stat(sys.argv[2]).st_uid != os.getuid(),
                    issuer_file_denied=denied[0], issuer_proc_denied=denied[1], keys=sorted(cfg))
    if op == 'challenge': return c.execute('SELECT poc.challenge()').fetchone()[0]
    if op == 'request': return request(a.pop('h'), **a)
    if op == 'rpc': return rpc(a['request'])
    if op == 'raw': return rpc(raw=a['raw'])
    if op == 'issue':
        h = a.pop('h', None) or run('challenge', {})
        return rpc(request(h, **a))
    if op == 'install': return c.execute("SELECT set_config('cac.poc_context',%s,true)", (a['token'],)).fetchone()[0] is not None
    if op == 'scope':
        response = run('issue', a)
        if not response['ok']: return response
        run('install', response)
        return run('records', {})
    if op == 'records': return [str(r[0]) for r in c.execute('SELECT store FROM poc.records')]
    if op == 'sql':
        cursor = c.execute(a['q'], a.get('params'))
        return cursor.fetchall() if cursor.description else []
    if op == 'commit': c.commit(); return True
    if op == 'rollback': c.rollback(); return True
    if op == 'close': c.close(); return True
    raise ValueError('unknown command')

for line in sys.stdin:
    try:
        req = json.loads(line)
        result = {'ok': True, 'value': run(req['op'], req.get('args', {}))}
    except psycopg.Error as e:
        result = {'ok': False, 'state': e.sqlstate}  # never emit DB detail or arguments
    except Exception:
        result = {'ok': False, 'state': 'worker-denied'}
    print(json.dumps(result, default=str), flush=True)
c.close()
