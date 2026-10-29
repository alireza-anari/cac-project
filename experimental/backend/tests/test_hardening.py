"""S0-07B real PostgreSQL regressions; synthetic issuer only."""
import hashlib
import hmac
import json
import time
import unittest
from uuid import UUID
import psycopg
from tests import test_security as original
from tests.test_security import CFG, connect, context, T1, S1, P1, P2, M1

class HardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original.SecurityTests.setUpClass()

    def test_direct_other_principal_grant_denied_and_not_persisted(self):
        member, grant = str(UUID(int=501)), str(UUID(int=502))
        with connect('postgres') as c:
            c.execute('INSERT INTO foundation.membership(id,tenant_id,store_id,principal_id,active) VALUES (%s,%s,%s,%s,true)', (member,T1,S1,P2))
        try:
            with connect('cac_provisioner') as c:
                self.assertEqual(c.execute('SELECT session_user,current_user').fetchone(), ('cac_provisioner','cac_provisioner'))
                context(c, principal=P1, purpose='provision')
                c.execute("INSERT INTO foundation.scoped_grant(id,tenant_id,store_id,membership_id,capability) VALUES (%s,%s,%s,%s,'store.manage')", (grant,T1,S1,M1))
                c.rollback()
                context(c, principal=P1, purpose='provision')
                with self.assertRaises(psycopg.errors.InsufficientPrivilege) as error:
                    c.execute("INSERT INTO foundation.scoped_grant(id,tenant_id,store_id,membership_id,capability) VALUES (%s,%s,%s,%s,'store.manage')", (grant,T1,S1,member))
                self.assertEqual(error.exception.sqlstate, '42501')
                c.rollback()
            with connect('postgres') as c:
                self.assertEqual(c.execute('SELECT count(*) FROM foundation.scoped_grant WHERE id=%s OR membership_id=%s', (grant,member)).fetchone(), (0,))
        finally:
            with connect('postgres') as c:
                c.execute('DELETE FROM foundation.scoped_grant WHERE id=%s OR membership_id=%s',(grant,member))
                c.execute('DELETE FROM foundation.membership WHERE id=%s',(member,))

    def assert_invalid(self, changes=None, omit=None):
        for role,purpose in [('cac_runtime','runtime'),('cac_provisioner','provision')]:
            with self.subTest(role=role, changes=changes, omit=omit), connect(role) as c:
                self.assertEqual(c.execute('SELECT session_user,current_user').fetchone(), (role,role))
                token = context(c, purpose=purpose)
                claims = json.loads(bytes.fromhex(token.split('.')[0]))
                claims.update(changes or {})
                if omit: del claims[omit]
                payload = json.dumps(claims,sort_keys=True,separators=(',',':')).encode()
                token = payload.hex()+'.'+hmac.new(bytes.fromhex(CFG['issuer_key']),payload,hashlib.sha256).hexdigest()
                c.execute("SELECT set_config('cac.context',%s,true)",(token,))
                with self.assertRaises(psycopg.errors.InsufficientPrivilege) as error:
                    c.execute('SELECT * FROM foundation.store').fetchall()
                self.assertEqual(error.exception.sqlstate, '42501')
                self.assertEqual(error.exception.diag.message_primary, 'Invalid request context')

    def test_signed_missing_and_null_mandatory_claims(self):
        for field in ['tenant','store','principal','purpose','expires','tx','pid']:
            self.assert_invalid(omit=field)
            self.assert_invalid({field:None})

    def test_signed_invalid_uuids_and_wrong_types(self):
        for field in ['tenant','store','principal']:
            for value in ['not-a-uuid','',123,True,[],{}]: self.assert_invalid({field:value})

    def test_signed_malformed_expiry_transaction_and_pid(self):
        for field in ['expires','tx','pid']:
            for value in ['not-a-number','',True,[],{},1.5]: self.assert_invalid({field:value})
        self.assert_invalid({'tx':'0'})
        self.assert_invalid({'pid':-1})
        self.assert_invalid({'expires':10**30})

    def test_maximum_ttl_and_near_boundary_positive(self):
        self.assert_invalid({'expires':int(time.time())+600})
        for role,purpose in [('cac_runtime','runtime'),('cac_provisioner','provision')]:
            with self.subTest(role=role), connect(role) as c:
                now = c.execute('SELECT floor(extract(epoch FROM statement_timestamp()))::bigint').fetchone()[0]
                context(c,purpose=purpose,expires=now+299)
                self.assertEqual([str(r[0]) for r in c.execute('SELECT id FROM foundation.store')],[S1])

    def test_verifier_not_public_executable(self):
        # Transactional probe role isolates function permission from schema USAGE.
        with connect('postgres') as c:
            c.execute('CREATE ROLE cac_public_probe NOLOGIN NOSUPERUSER NOBYPASSRLS')
            c.execute('GRANT USAGE ON SCHEMA foundation TO cac_public_probe')
            self.assertEqual(c.execute("SELECT count(*) FROM pg_proc p CROSS JOIN LATERAL aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner))) a WHERE p.oid='foundation.verified_context()'::regprocedure AND a.grantee=0 AND a.privilege_type='EXECUTE'").fetchone(),(0,))
            c.execute('SET LOCAL ROLE cac_public_probe')
            with self.assertRaises(psycopg.errors.InsufficientPrivilege) as error: c.execute('SELECT foundation.verified_context()')
            self.assertIn('permission denied for function',error.exception.diag.message_primary)
            c.rollback()

    def test_future_owner_function_defaults_deny_public_and_apps(self):
        try:
            with connect('cac_owner') as c:
                c.execute('CREATE FUNCTION foundation.future_privilege_probe() RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$')
                self.assertEqual(c.execute("SELECT count(*) FROM pg_proc p CROSS JOIN LATERAL aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner))) a WHERE p.oid='foundation.future_privilege_probe()'::regprocedure AND a.grantee=0 AND a.privilege_type='EXECUTE'").fetchone(),(0,))
            for role in ['cac_runtime','cac_provisioner']:
                with self.subTest(role=role), connect(role) as c:
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege): c.execute('SELECT foundation.future_privilege_probe()')
        finally:
            with connect('cac_owner') as c: c.execute('DROP FUNCTION IF EXISTS foundation.future_privilege_probe()')
