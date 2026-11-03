"""Actual disposable process crash checkpoints. stdout never includes tokens/keys."""
import json
import os
from pathlib import Path
import sys
from recovery_fencing.broker import Broker,FenceDenied

cfg=json.loads(Path(sys.argv[1]).read_text())
operation,stage,req=sys.argv[2:5]
def hook(value):
    if value==stage:os._exit(91)
b=Broker(cfg=cfg,hook=hook)
try:
    if operation=='activate':b.activate(0,req)
    else:
        with b.runtime() as s:
            h=s.challenge();t=b.issue(h);s.install(t)
            if s.records()!=['00000000-0000-0000-0000-0000000003eb']:raise AssertionError('scope')
            if operation=='pause':
                print(json.dumps(dict(phase='after_local_body',pid=s.pid)),flush=True)
                sys.stdin.readline()
    raise SystemExit(0)
except FenceDenied:raise SystemExit(2)
