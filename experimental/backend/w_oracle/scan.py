"""W_ORACLE_ASSUMED. Scan only explicit evidence; never upload private snapshots."""
import json
import os
from pathlib import Path
from w_oracle.lab import OracleLab, BANNER

lab = OracleLab()
values = [lab.cfg['password']]
values += lab.cfg.get('historical_keys',[])
for actor in lab.cfg['actors'].values():
    values += [actor['coord_password'], actor['check_password']]
for node in lab.parent.cfg.values():
    values += list(node.get('passwords', {}).values()) + node.get('poc_proofs', [])
    values += [node[k] for k in ['password','anchor_password','fence_secret','issuer_key'] if node.get(k)]
with lab.connect() as c:
    if c.execute("SELECT to_regclass('w.control')").fetchone()[0]:
        values += [r[0] for r in c.execute("SELECT encode(secret,'hex') FROM w.control")]
for p in Path(os.environ['GITHUB_WORKSPACE'], 'evidence-s009f').iterdir():
    if p.is_file():
        data = p.read_bytes()
        if BANNER.encode() not in data:
            raise SystemExit('Missing oracle assumption banner: '+p.name)
        if any(v.encode() in data for v in values if v):
            raise SystemExit('Private fixture scan blocked: '+p.name)
print(BANNER, 'evidence scan PASS', flush=True)
with Path(os.environ['GITHUB_OUTPUT']).open('a') as f:
    f.write('safe=true\n')
lab.close()
