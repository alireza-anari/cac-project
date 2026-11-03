"""Fail closed before artifact upload; never print matched credential bytes."""
import os
from pathlib import Path
from context_poc.harness import CFG,connect

root=Path(os.environ['CAC_SCAN_PATH'])
assert root.exists()
secrets=[*CFG['passwords'].values(),*CFG['poc_proofs'],CFG['issuer_key']]
with connect('postgres') as c:
    secrets.extend(x[0] for x in c.execute("SELECT encode(secret,'hex') FROM poc_private.keys"))
needles=[s.encode() for s in secrets if s]
files=[root] if root.is_file() else list(root.iterdir())
for p in files:
    if p.is_file() and any(n in p.read_bytes() for n in needles):
        raise SystemExit('Credential scan blocked artifact upload: '+p.name)
print('Credential scan PASS; known fixture passwords/proofs/key hex absent',flush=True)
with Path(os.environ['GITHUB_OUTPUT']).open('a') as f:f.write('safe=true\n')
