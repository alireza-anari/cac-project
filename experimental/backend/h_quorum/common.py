"""Q_SURVIVAL_ONLY. Bounded fixture data, never production contracts."""
import base64
import hashlib
import json
import os
from pathlib import Path

BANNER='Q_SURVIVAL_ONLY / NONRESTORED_MAJORITY_REQUIRED / SECURITY_UNPROVEN'
class Denied(Exception):pass

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
def b64(value):return base64.b64encode(value.encode() if isinstance(value,str) else value).decode()
def unb64(value):return base64.b64decode(value,validate=True)
def config():
    if os.environ.get('CAC_EXPERIMENTAL_DISPOSABLE')!='1':raise Denied('Disposable only')
    return json.loads(Path(os.environ['CAC_H_CONFIG']).read_text())
