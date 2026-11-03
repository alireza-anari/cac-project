import json
import os
from pathlib import Path
from uuid import UUID
import psycopg
from psycopg.types.json import Jsonb
CFG=json.loads(Path(os.environ['CAC_TEST_CONFIG']).read_text())
P1,P2,S1,S2,S3,T1,T2,U1,U2=[str(UUID(int=i)) for i in range(1001,1010)]
def connect(role='cac_ctx_runtime'):
    return psycopg.connect(**CFG['connection'],user=role,password=CFG['passwords'][role])
def challenge(c): return c.execute('SELECT poc.challenge()').fetchone()[0]
def issue(h,store=S1,action='read',target=P1,body=None,proof=None):
    # Dedicated login and independent COMMIT before returning any envelope.
    c=connect('cac_ctx_issuer')
    try:
      with c:
        token=c.execute('SELECT poc.issue(%s,%s,%s,%s,%s,%s)',(h,proof or CFG['poc_proofs'][0],store,action,target,Jsonb(body or {}))).fetchone()[0]
    finally:
        c.close()  # Also close when a deferred constraint rejects COMMIT.
    return token

def install(c,token): c.execute("SELECT set_config('cac.poc_context',%s,true)",(token,))
def seed():
    with connect('postgres') as c:
        c.execute('TRUNCATE poc.records,poc_private.ledger,poc_private.access,poc_private.sessions,poc_private.principals,poc_private.stores,poc_private.keys,poc_private.config CASCADE')
        c.execute('INSERT INTO poc_private.config VALUES(true,public.gen_random_uuid())')
        for kind in ['challenge','context']:
            c.execute("INSERT INTO poc_private.keys VALUES(%s,'k1',public.gen_random_bytes(32),'active')",(kind,))
        for p,u,proof in [(P1,U1,CFG['poc_proofs'][0]),(P2,U2,CFG['poc_proofs'][1])]:
            c.execute('INSERT INTO poc_private.principals VALUES(%s,true,1)',(p,))
            c.execute("INSERT INTO poc_private.sessions VALUES(%s,%s,public.digest(%s,'sha256'),true,1,clock_timestamp()+interval '1 hour',clock_timestamp())",(u,p,proof))
        for i,(s,t) in enumerate([(S1,T1),(S2,T1),(S3,T2)]):
            c.execute('INSERT INTO poc_private.stores VALUES(%s,%s,1)',(s,t))
            c.execute('INSERT INTO poc_private.access VALUES(%s,%s)',(P1 if i<2 else P2,s))
            c.execute('INSERT INTO poc.records VALUES(%s,%s,%s,%s)',(str(UUID(int=1100+i)),t,s,'synthetic'))
