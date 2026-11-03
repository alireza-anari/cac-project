"""Remove the public disposable bootstrap password BEFORE starting adversarial UIDs."""
import json
import os
from pathlib import Path
import secrets
from psycopg import sql
from context_poc.harness import CFG,connect

def rotate():
    if os.environ.get('CAC_EXPERIMENTAL_DISPOSABLE')!='1' or CFG['connection']['dbname']!='cac_s007_test':
        raise RuntimeError('Disposable fixture only')
    password=secrets.token_urlsafe(48)
    with connect('postgres') as c:
        c.execute(sql.SQL('ALTER ROLE postgres PASSWORD {}').format(sql.Literal(password)))
    CFG['passwords']['postgres']=password
    # Preserve private file identity/owner; no environment or stdout export.
    fd=os.open(os.environ['CAC_TEST_CONFIG'],os.O_WRONLY|os.O_TRUNC|os.O_NOFOLLOW)
    with os.fdopen(fd,'w') as f:
        os.fchmod(f.fileno(),0o600)
        json.dump(CFG,f)
    print('Disposable administrator credential randomized before process adversary; no secret emitted',flush=True)

if __name__=='__main__':rotate()
