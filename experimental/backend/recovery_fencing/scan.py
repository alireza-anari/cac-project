"""No known fixture credentials/keys may enter uploaded evidence."""
import os
from pathlib import Path
from recovery_fencing.lab import Lab
lab=Lab();values=[]
for name,n in lab.cfg.items():
    values.extend(n.get('passwords',{}).values())
    values.extend(n.get('poc_proofs',[]))
    for key in ['password','anchor_password','fence_secret','issuer_key']:
        if n.get(key):values.append(n[key])
    if name in ['A','B']:
        with lab.connect(name) as c:
            if c.execute("SELECT 1 FROM pg_namespace WHERE nspname='poc_private'").fetchone():
                values.extend(r[0] for r in c.execute("SELECT encode(secret,'hex') FROM poc_private.keys"))
for p in Path(os.environ['GITHUB_WORKSPACE'],'evidence-s009c').iterdir():
    if p.is_file() and any(v.encode() in p.read_bytes() for v in values if v):raise SystemExit('Known credential scan blocked upload: '+p.name)
print('S009C credential scan PASS',flush=True)
with Path(os.environ['GITHUB_OUTPUT']).open('a') as f:f.write('safe=true\n')
lab.close()
