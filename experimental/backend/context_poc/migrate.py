"""Fresh disposable SQL migration, independently reversible from legacy Django."""
import os
import secrets
import sys
import json
from pathlib import Path
from psycopg import sql
from context_poc.harness import CFG,connect
if os.environ.get('CAC_EXPERIMENTAL_DISPOSABLE')!='1' or CFG['connection']['dbname']!='cac_s007_test':
    raise SystemExit('Refusing non-disposable database')
root=Path(__file__).parent/'sql'
mode=sys.argv[1]
with connect('postgres') as c:
    if mode=='bootstrap':
        for role in ['cac_ctx_owner','cac_ctx_guard','cac_ctx_runtime','cac_ctx_issuer','cac_ctx_identity']:
            login=role not in ['cac_ctx_owner','cac_ctx_guard']
            c.execute(sql.SQL('CREATE ROLE {} {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS').format(sql.Identifier(role),sql.SQL('LOGIN' if login else 'NOLOGIN')))
            if login:
                CFG['passwords'][role]=secrets.token_urlsafe(40)
                c.execute(sql.SQL('ALTER ROLE {} PASSWORD {}').format(sql.Identifier(role),sql.Literal(CFG['passwords'][role])))
                c.execute(sql.SQL('GRANT CONNECT ON DATABASE cac_s007_test TO {}').format(sql.Identifier(role)))
        CFG['poc_proofs']=[secrets.token_urlsafe(40),secrets.token_urlsafe(40)]
    elif mode in ['up','down']:
        c.execute((root/('001_'+mode+'.sql')).read_text())
    else: raise SystemExit('Unknown migration mode')
if mode=='bootstrap':
    Path(os.environ['CAC_TEST_CONFIG']).write_text(json.dumps(CFG))
print('POC migration',mode,'PASS; no credentials emitted')
