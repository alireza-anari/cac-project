"""Disposable local issuer. This module must never import the all-role harness."""
import json
import os
import socket
import struct
import sys
import threading
from pathlib import Path
from uuid import UUID
import psycopg
from psycopg.types.json import Jsonb

LIMIT = 24000
FIELDS = {'challenge', 'proof', 'store', 'action', 'target', 'body'}

def validate(r):
    if type(r) is not dict or set(r) != FIELDS:
        raise ValueError('denied')
    for f in ['challenge', 'proof', 'store', 'action', 'target']:
        if type(r[f]) is not str or not r[f] or len(r[f]) > (16000 if f == 'challenge' else 256):
            raise ValueError('denied')
    for f in ['store', 'target']:
        if str(UUID(r[f])) != r[f]: raise ValueError('denied')
    if r['action'] not in ('read', 'probe') or type(r['body']) is not dict:
        raise ValueError('denied')
    return r

def serve(cfg_path, socket_path, runtime_uid):
    cfg = json.loads(Path(cfg_path).read_text())
    assert set(cfg) == {'connection', 'role', 'password'}
    assert cfg['role'] == 'cac_ctx_issuer'
    def handle(conn):
        with conn:
            try:
                _, uid, _ = struct.unpack('3i', conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                if uid != runtime_uid: raise ValueError('denied')
                conn.settimeout(4)
                data = b''
                while not data.endswith(b'\n'):
                    data += conn.recv(4096)
                    if not data or len(data) > LIMIT: raise ValueError('denied')
                # Duplicate keys and nonfinite numbers are rejected at the RPC boundary.
                def unique(pairs):
                    d = {}
                    for k, v in pairs:
                        if k in d: raise ValueError('denied')
                        d[k] = v
                    return d
                r = validate(json.loads(data, object_pairs_hook=unique,
                                        parse_constant=lambda _: (_ for _ in ()).throw(ValueError())))
                with psycopg.connect(**cfg['connection'], user=cfg['role'], password=cfg['password'],
                                     connect_timeout=2, options='-c statement_timeout=2000 -c lock_timeout=1000') as c:
                    token = c.execute('SELECT poc.issue(%s,%s,%s,%s,%s,%s)',
                        (r['challenge'], r['proof'], r['store'], r['action'], r['target'], Jsonb(r['body']))).fetchone()[0]
                # The connection context has committed AND closed before this write.
                response = {'ok': True, 'token': token}
            except Exception:
                response = {'ok': False, 'error': 'denied'}
            try: conn.sendall(json.dumps(response).encode() + b'\n')
            except OSError: pass  # lost response cannot undo the committed ledger
    with socket.socket(socket.AF_UNIX) as s:
        s.bind(socket_path)
        os.chmod(socket_path, 0o666)  # authentication is kernel SO_PEERCRED, directory is root-owned
        s.listen(16)
        while True:
            conn, _ = s.accept()
            threading.Thread(target=handle, args=(conn,), daemon=True).start()

if __name__ == '__main__': serve(sys.argv[1], sys.argv[2], int(sys.argv[3]))
