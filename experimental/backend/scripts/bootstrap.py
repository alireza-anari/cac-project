"""Explicitly disposable CI bootstrap. Credential output is private, never evidence."""
import json
import os
from pathlib import Path
import secrets
import psycopg
from psycopg import sql
if os.environ.get('CAC_EXPERIMENTAL_DISPOSABLE') != '1' or os.environ.get('PGDATABASE') != 'cac_s007_test':
    raise SystemExit('Refusing bootstrap: explicit disposable flag and cac_s007_test required')
path=Path(os.environ['CAC_TEST_CONFIG'])
if path.exists(): raise SystemExit('Refusing to overwrite existing credential file')
connection={'host':os.environ.get('PGHOST','127.0.0.1'),'port':int(os.environ.get('PGPORT','5432')),'dbname':'cac_s007_test'}
passwords={'postgres':os.environ['PGPASSWORD']}
for role in ['cac_owner','cac_runtime','cac_provisioner']:passwords[role]=secrets.token_urlsafe(40)
key=secrets.token_bytes(32)
with psycopg.connect(**connection,user='postgres',password=passwords['postgres']) as c:
    if c.execute("SELECT 1 FROM pg_namespace WHERE nspname IN ('foundation','cac_private')").fetchone():raise SystemExit('Refusing nonfresh schemas')
    c.execute((Path(__file__).resolve().parents[1]/'sql/roles.sql').read_text())
    for role,pw in passwords.items():
        if role!='postgres': c.execute(sql.SQL('ALTER ROLE {} PASSWORD {}').format(sql.Identifier(role),sql.Literal(pw)))
    c.execute('INSERT INTO cac_private.context_key VALUES (true,%s)',(key,))
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:json.dump({'connection':connection,'passwords':passwords,'issuer_key':key.hex()},f)
print('Disposable roles/schemas created; private random credentials written (not logged).')
