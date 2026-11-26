"""Read-only Python trace of the original Unix issuer; no SQL or RPC substitute."""
import hashlib
import json
from pathlib import Path
import sys
import threading

import psycopg
from pool_recovery import issuer


def emit(kind, **value):
    print('P_LEGACY_EVENT', json.dumps(dict(kind=kind, **value), sort_keys=True), flush=True)


def main():
    source = Path(issuer.__file__).resolve()
    lines = source.read_text().splitlines()
    matches = [n for n, line in enumerate(lines, 1) if "token = c.execute('SELECT poc.issue(" in line]
    if len(matches) != 1:
        raise RuntimeError('Original issuer SQL call site not uniquely found')
    call_line = matches[0]
    seen = set()

    def trace(frame, event, value):
        if frame.f_code.co_filename != str(source) or frame.f_code.co_name != 'handle':
            return trace
        if event == 'line' and frame.f_lineno == call_line and id(frame) not in seen:
            seen.add(id(frame))
            c = frame.f_locals['c']
            # Observe the original connection; no proxy, ticket, SQL or role mutation.
            role, user, pid, tx, sid, now = c.execute(
                'SELECT current_user,session_user,pg_backend_pid(),txid_current()::text,fence.system_id(),'
                'extract(epoch FROM clock_timestamp())'
            ).fetchone()
            challenge = json.loads(bytes.fromhex(frame.f_locals['r']['challenge'].split('.')[0]))
            emit('ORIGINAL_SQL_CALL', source='pool_recovery/issuer.py', line=call_line,
                 role=role, session_user=user, pid=pid, fullxid=tx, system_id=sid,
                 challenge_pid=challenge['pid'], challenge_tx=challenge['tx'],
                 challenge_age_seconds=float(now) - float(challenge['started']),
                 driver_backend_pid=c.info.backend_pid, statement='SELECT poc.issue(6 parameters)')
        if event == 'exception' and id(frame) in seen and isinstance(value[1], psycopg.Error):
            error = value[1]
            context = error.diag.context or ''
            allow = ('h_guard.require', 'poc.issue', 'h_guard.issue_c', 'poc_private.issue_unfenced')
            emit('ORIGINAL_SQL_EXCEPTION', sqlstate=error.sqlstate,
                 functions=[name for name in allow if name in context])
        return trace

    threading.settrace(trace)
    emit('READY', source='pool_recovery/issuer.py', call_line=call_line,
         source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    # Original SO_PEERCRED validation, parser, SQL call, transaction and response.
    issuer.serve(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))


if __name__ == '__main__':
    main()
