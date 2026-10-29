"""Real PostgreSQL tests. Synthetic issuer only; no production identities."""
import hashlib
import hmac
import json
import os
import time
import unittest
from pathlib import Path
from uuid import UUID
import psycopg

CFG = json.loads(Path(os.environ['CAC_TEST_CONFIG']).read_text())
T1,T2,S1,S2,S3,P1,P2,M1,M2,M3 = [str(UUID(int=i)) for i in range(1,11)]
def connect(role):
    return psycopg.connect(**CFG['connection'], user=role, password=CFG['passwords'][role])
def context(conn, tenant=T1, store=S1, principal=P1, purpose='runtime', **overrides):
    tx,pid=conn.execute('SELECT txid_current(), pg_backend_pid()').fetchone()
    claims=dict(tenant=tenant,store=store,principal=principal,purpose=purpose,expires=int(time.time())+60,tx=str(tx),pid=pid)
    claims.update(overrides)
    payload=json.dumps(claims,sort_keys=True,separators=(',',':')).encode()
    token=payload.hex()+'.'+hmac.new(bytes.fromhex(CFG['issuer_key']),payload,hashlib.sha256).hexdigest()
    conn.execute("SELECT set_config('cac.context', %s, true)",(token,))
    return token

class SecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with connect('postgres') as c:
            c.execute('TRUNCATE foundation.scoped_grant, foundation.membership, foundation.store, foundation.tenant CASCADE')
            c.execute('INSERT INTO foundation.tenant(id,name) VALUES (%s,%s),(%s,%s)',(T1,'Synthetic A',T2,'Synthetic B'))
            for t,s in [(T1,S1),(T1,S2),(T2,S3)]:
                c.execute('INSERT INTO foundation.store(id,tenant_id,name) VALUES (%s,%s,%s)',(s,t,'Synthetic store'))
            for m,t,s,p in [(M1,T1,S1,P1),(M2,T1,S2,P2),(M3,T2,S3,P2)]:
                c.execute('INSERT INTO foundation.membership(id,tenant_id,store_id,principal_id,active) VALUES (%s,%s,%s,%s,true)',(m,t,s,p))
                c.execute('INSERT INTO foundation.scoped_grant(id,tenant_id,store_id,membership_id,capability) VALUES (%s,%s,%s,%s,%s)',(str(UUID(int=100+UUID(m).int)),t,s,m,'store.view'))
    def denied(self, sql, params=(), role='cac_runtime', sqlstate='42501', scoped=True):
        with connect(role) as c:
            if scoped: context(c,purpose='provision' if role=='cac_provisioner' else 'runtime')
            with self.assertRaises(psycopg.Error) as e: c.execute(sql,params).fetchall()
            self.assertEqual(e.exception.sqlstate,sqlstate)
    def test_actual_nonowner_roles_and_force_rls(self):
        with connect('postgres') as c:
            rows=c.execute("SELECT rolname,rolsuper,rolbypassrls,rolcreaterole,rolcreatedb FROM pg_roles WHERE rolname IN ('cac_runtime','cac_provisioner')").fetchall()
            self.assertEqual(len(rows),2)
            for row in rows: self.assertEqual(row[1:],(False,False,False,False))
            rows=c.execute("SELECT relname,relrowsecurity,relforcerowsecurity,pg_get_userbyid(relowner) FROM pg_class WHERE relnamespace='foundation'::regnamespace AND relname IN ('tenant','store','membership','scoped_grant')").fetchall()
            self.assertEqual(len(rows),4)
            for row in rows: self.assertEqual(row[1:],(True,True,'cac_owner'))
        with connect('cac_runtime') as c: self.assertEqual(c.execute('SELECT session_user,current_user').fetchone(),('cac_runtime','cac_runtime'))
    def test_own_scope_read(self):
        with connect('cac_runtime') as c:
            context(c)
            self.assertEqual([str(r[0]) for r in c.execute('SELECT id FROM foundation.store')],[S1])
            self.assertEqual([str(r[0]) for r in c.execute('SELECT id FROM foundation.tenant')],[T1])
            self.assertEqual([str(r[0]) for r in c.execute('SELECT id FROM foundation.membership')],[M1])
            self.assertEqual(c.execute('SELECT capability FROM foundation.scoped_grant').fetchall(),[('store.view',)])
    def test_same_tenant_other_store_filtered(self):
        with connect('cac_runtime') as c:
            context(c)
            self.assertEqual(c.execute('SELECT id FROM foundation.store WHERE id=%s',(S2,)).fetchall(),[])
    def test_other_tenant_filtered(self):
        with connect('cac_runtime') as c:
            context(c)
            self.assertEqual(c.execute('SELECT id FROM foundation.tenant WHERE id=%s',(T2,)).fetchall(),[])
    def test_valid_signature_does_not_replace_membership(self):
        with connect('cac_runtime') as c:
            context(c,store=S2)
            for table in ['store','tenant','membership','scoped_grant']:
                self.assertEqual(c.execute('SELECT * FROM foundation.'+table).fetchall(),[])
    def test_missing_context(self): self.denied('SELECT * FROM foundation.store',scoped=False)
    def test_malformed_context(self):
        with connect('cac_runtime') as c:
            c.execute("SELECT set_config('cac.context','not-a-token',true)")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege): c.execute('SELECT * FROM foundation.store').fetchall()
    def test_unsigned_context_forgery(self):
        with connect('cac_runtime') as c:
            token=context(c); payload,sig=token.split('.')
            claims=json.loads(bytes.fromhex(payload));claims['principal']=P2;claims['store']=S2
            forged=json.dumps(claims,sort_keys=True,separators=(',',':')).encode().hex()+'.'+sig
            c.execute("SELECT set_config('cac.context',%s,true)",(forged,))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute('SELECT * FROM foundation.store').fetchall()
    def test_expired_context(self):
        with connect('cac_runtime') as c:
            context(c,expires=1)
            with self.assertRaises(psycopg.errors.InsufficientPrivilege): c.execute('SELECT * FROM foundation.store').fetchall()
    def test_context_purpose_bound_to_login(self):
        with connect('cac_runtime') as c:
            context(c,purpose='provision')
            with self.assertRaises(psycopg.errors.InsufficientPrivilege): c.execute('SELECT * FROM foundation.store').fetchall()
    def test_context_cleared_on_commit(self):
        with connect('cac_runtime') as c:
            context(c); c.commit()
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute('SELECT * FROM foundation.store').fetchall()
    def test_context_cleared_on_rollback(self):
        with connect('cac_runtime') as c:
            context(c); c.rollback()
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute('SELECT * FROM foundation.store').fetchall()
    def test_old_token_cannot_replay_in_next_transaction(self):
        with connect('cac_runtime') as c:
            token=context(c); c.commit();c.execute("SELECT set_config('cac.context',%s,true)",(token,))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute('SELECT * FROM foundation.store').fetchall()
    def test_independent_connections_and_token_replay(self):
        with connect('cac_runtime') as a,connect('cac_runtime') as b:
            token=context(a);context(b,tenant=T2,store=S3,principal=P2)
            self.assertEqual([str(r[0]) for r in a.execute('SELECT id FROM foundation.store')],[S1])
            self.assertEqual([str(r[0]) for r in b.execute('SELECT id FROM foundation.store')],[S3])
            b.execute("SELECT set_config('cac.context',%s,true)",(token,))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):b.execute('SELECT * FROM foundation.store').fetchall()
    def test_runtime_cannot_change_privileges(self):self.denied('UPDATE foundation.membership SET active=false RETURNING id')
    def test_runtime_cannot_insert_grants(self):self.denied("INSERT INTO foundation.scoped_grant(id,tenant_id,store_id,membership_id,capability) VALUES (%s,%s,%s,%s,'store.manage') RETURNING id",(str(UUID(int=200)),T1,S1,M1))
    def test_runtime_cannot_assume_provisioner(self):self.denied('SET ROLE cac_provisioner')
    def test_runtime_cannot_read_issuer_key(self):self.denied('SELECT * FROM cac_private.context_key')
    def test_runtime_cannot_ddl(self):self.denied('CREATE TABLE foundation.escalation(id int)')
    def test_runtime_cannot_disable_rls(self):self.denied('ALTER TABLE foundation.store DISABLE ROW LEVEL SECURITY')
    def test_runtime_row_security_off_does_not_bypass(self):
        with connect('cac_runtime') as c:
            context(c);c.execute('SET LOCAL row_security=off')
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute('SELECT * FROM foundation.store').fetchall()
    def test_composite_store_fk_rejects_wrong_tenant(self):
        self.denied('INSERT INTO foundation.membership(id,tenant_id,store_id,principal_id,active) VALUES (%s,%s,%s,%s,true) RETURNING id',(str(UUID(int=201)),T2,S1,P1),role='postgres',sqlstate='23503',scoped=False)
    def test_composite_grant_fk_rejects_wrong_store(self):
        self.denied("INSERT INTO foundation.scoped_grant(id,tenant_id,store_id,membership_id,capability) VALUES (%s,%s,%s,%s,'store.manage') RETURNING id",(str(UUID(int=202)),T1,S2,M1),role='postgres',sqlstate='23503',scoped=False)
    def test_provisioner_insert_scope_and_rollback(self):
        t,s,m=[str(UUID(int=i)) for i in [301,302,303]]
        with connect('cac_provisioner') as c:
            context(c,tenant=t,store=s,purpose='provision')
            c.execute('INSERT INTO foundation.tenant(id,name) VALUES (%s,%s)',(t,'Synthetic new'))
            c.execute('INSERT INTO foundation.store(id,tenant_id,name) VALUES (%s,%s,%s)',(s,t,'Synthetic new'))
            c.execute('INSERT INTO foundation.membership(id,tenant_id,store_id,principal_id,active) VALUES (%s,%s,%s,%s,true)',(m,t,s,P1))
            c.execute("INSERT INTO foundation.scoped_grant(id,tenant_id,store_id,membership_id,capability) VALUES (%s,%s,%s,%s,'store.view')",(str(UUID(int=304)),t,s,m))
            self.assertEqual(c.execute('SELECT count(*) FROM foundation.scoped_grant').fetchone(),(1,));c.rollback()
        with connect('postgres') as c:self.assertEqual(c.execute('SELECT count(*) FROM foundation.tenant WHERE id=%s',(t,)).fetchone(),(0,))
    def test_provisioner_cannot_cross_scope_insert(self):self.denied('INSERT INTO foundation.store(id,tenant_id,name) VALUES (%s,%s,%s) RETURNING id',(str(UUID(int=305)),T2,'Denied'),role='cac_provisioner')
    def test_provisioner_cannot_update_or_delete(self):
        for sql in ['UPDATE foundation.membership SET active=false RETURNING id','DELETE FROM foundation.store RETURNING id']:
            self.denied(sql,role='cac_provisioner')
    def test_provisioner_cannot_assume_owner_or_read_key(self):
        for sql in ['SET ROLE cac_owner','SELECT * FROM cac_private.context_key']:
            self.denied(sql,role='cac_provisioner')
    def test_inactive_membership_denied(self):
        with connect('postgres') as c:c.execute('UPDATE foundation.membership SET active=false WHERE id=%s',(M1,))
        try:
            with connect('cac_runtime') as c:
                context(c)
                for table in ['tenant','store','membership','scoped_grant']:self.assertEqual(c.execute('SELECT * FROM foundation.'+table).fetchall(),[])
        finally:
            with connect('postgres') as c:c.execute('UPDATE foundation.membership SET active=true WHERE id=%s',(M1,))
    def test_membership_is_not_a_capability(self):
        with connect('postgres') as c:c.execute("UPDATE foundation.scoped_grant SET capability='store.manage' WHERE membership_id=%s",(M1,))
        try:
            with connect('cac_runtime') as c:
                context(c)
                self.assertEqual(c.execute('SELECT count(*) FROM foundation.membership').fetchone(),(1,))
                for table in ['tenant','store']:self.assertEqual(c.execute('SELECT * FROM foundation.'+table).fetchall(),[])
        finally:
            with connect('postgres') as c:c.execute("UPDATE foundation.scoped_grant SET capability='store.view' WHERE membership_id=%s",(M1,))
    def test_signed_context_missing_purpose_denied(self):
        with connect('cac_runtime') as c:
            context(c,purpose=None)
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute('SELECT * FROM foundation.store').fetchall()
    def test_owner_force_rls_without_context(self):
        # FORCE RLS + no applicable owner policy means zero rows (default deny).
        with connect('cac_owner') as c:
            self.assertEqual(c.execute('SELECT * FROM foundation.membership').fetchall(),[])
    def test_provisioner_cannot_grant_to_another_principal(self):
        self.denied('INSERT INTO foundation.membership(id,tenant_id,store_id,principal_id,active) VALUES (%s,%s,%s,%s,true) RETURNING id',(str(UUID(int=400)),T1,S1,P2),role='cac_provisioner')
