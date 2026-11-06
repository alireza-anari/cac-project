"""Allowlisted, credential-scanned H evidence only; private logs never uploaded."""
import json
import os
from pathlib import Path
from h_quorum.common import BANNER

def main():
    directory=Path(os.environ['GITHUB_WORKSPACE'])/'evidence-s009h'
    allowed={'tested-sha.txt','pr-head-sha.txt','source-receipt.log','topology.log','quorum.log','proof.log','service.log'}
    secrets=[]
    credential_fields={'password','passwords','anchor_password','fence_secret','proof','poc_proofs','signing_keys'}
    def collect(value,key='',sensitive=False):
        sensitive=sensitive or key in credential_fields
        if isinstance(value,dict):
            for k,v in value.items():collect(v,k,sensitive)
        elif isinstance(value,list):
            for v in value:collect(v,key,sensitive)
        elif isinstance(value,str) and sensitive and value:secrets.append(value)
    for name in ('CAC_C_CONFIG','CAC_H_CONFIG'):
        path=Path(os.environ[name])
        if path.exists():collect(json.loads(path.read_text()))
    for path in directory.iterdir():
        if path.is_symlink() or not path.is_file() or path.name not in allowed:raise RuntimeError('Nonallowlisted evidence')
        data=path.read_text()
        if BANNER not in data or 'PRIVATE KEY' in data or any(secret in data for secret in secrets):raise RuntimeError('Evidence scan denied')
    with open(os.environ['GITHUB_OUTPUT'],'a') as stream:stream.write('safe=true\n')
    print(BANNER,'allowlisted evidence scan passed')
if __name__=='__main__':main()
