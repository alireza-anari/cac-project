import concurrent.futures
import json
import time
import unittest
import psycopg
from psycopg.types.json import Jsonb
from context_poc.harness import *

class ContextTests(unittest.TestCase):
    def setUp(self): seed()
    def deny(self,c,sql='SELECT * FROM poc.records',args=(),state='42501'):
        with self.assertRaises(psycopg.Error) as e: c.execute(sql,args).fetchall()
        self.assertEqual(e.exception.sqlstate,state)
    def token(self,c,**kw):
        t=issue(challenge(c),**kw);install(c,t);return t
    def test_positive_nonowner_scope(self):
        with connect() as c:
            self.assertEqual(c.execute('SELECT session_user,current_user').fetchone(),('cac_ctx_runtime','cac_ctx_runtime'))
            self.token(c)
            self.assertEqual([str(r[0]) for r in c.execute('SELECT store FROM poc.records')],[S1])
    def test_runtime_arbitrary_sql_acl(self):
        for q in ['SELECT * FROM poc_private.keys','SELECT * FROM poc_private.ledger',"SELECT poc_private.pack('{}','context')",'SET ROLE cac_ctx_guard','ALTER TABLE poc.records DISABLE ROW LEVEL SECURITY','DELETE FROM poc.records',"SELECT poc.revoke('principal','"+P1+"')"]:
            with self.subTest(q=q),connect() as c:self.deny(c,q)
        with connect('postgres') as c:
            rows=c.execute("SELECT rolname,rolsuper,rolbypassrls,rolcreaterole FROM pg_roles WHERE rolname LIKE 'cac_ctx_%'").fetchall()
            self.assertEqual(len(rows),5)
            for r in rows:self.assertEqual(r[1:],(False,False,False))
            self.assertEqual(c.execute("SELECT relrowsecurity,relforcerowsecurity,pg_get_userbyid(relowner) FROM pg_class WHERE oid='poc.records'::regclass").fetchone(),(True,True,'cac_ctx_owner'))
            self.assertEqual(c.execute("SELECT count(*) FROM pg_proc p CROSS JOIN LATERAL aclexplode(p.proacl) a WHERE p.pronamespace IN ('poc'::regnamespace,'poc_private'::regnamespace) AND a.grantee=0").fetchone(),(0,))
    def test_issuer_rejects_forged_selectors(self):
        with connect() as c:
            h=challenge(c)
            for kw in [dict(target=P2),dict(store=S3),dict(action='admin'),dict(proof='invalid-session')]:
                with self.subTest(kw=kw),self.assertRaises(psycopg.errors.InsufficientPrivilege):issue(h,**kw)
            self.deny(c,'SELECT poc.issue(%s,%s,%s,%s,%s,%s)',(h,'invalid',S1,'read',P1,Jsonb({})))
    def test_action_target_digest_binding(self):
        for args in [(None,None,None),(None,P1,{'x':1}),('probe',None,{'x':1}),('probe',P1,None),('read',P1,{}),('probe',P2,{'x':1}),('probe',P1,{'x':2})]:
            with self.subTest(args=args),connect() as c:
                self.token(c,action='probe',body={'x':1})
                self.deny(c,'SELECT poc.authorize(%s,%s,%s)',(args[0],args[1],Jsonb(args[2]) if args[2] is not None else None))
        with connect() as c:
            self.token(c,action='probe',body={'x':1})
            self.assertEqual(c.execute('SELECT poc.authorize(%s,%s,%s)',('probe',P1,Jsonb({'x':1}))).fetchone(),(True,))
            self.deny(c)
    def test_forged_payload_and_missing_context(self):
        with connect() as c:self.deny(c)
        with connect() as c:
            t=self.token(c);p,s=t.split('.');d=json.loads(bytes.fromhex(p));d['store']=S3
            install(c,json.dumps(d).encode().hex()+'.'+s);self.deny(c)
    def test_cross_connection_and_transaction_replay(self):
        with connect() as a,connect() as b:
            t=self.token(a);install(b,t);self.deny(b)
            a.commit();install(a,t);self.deny(a)
    def test_cross_login_replay(self):
        with connect() as a,connect('cac_ctx_issuer') as b:
            t=self.token(a);install(b,t);self.deny(b,'SELECT poc.verify()')
    def test_savepoint_ledger_survives(self):
        with connect() as c:
            c.execute('SAVEPOINT before_install');h=challenge(c);t=issue(h);install(c,t)
            self.assertEqual(c.execute('SELECT count(*) FROM poc.records').fetchone(),(1,))
            c.execute('ROLLBACK TO SAVEPOINT before_install')
            with connect('postgres') as root:self.assertEqual(root.execute('SELECT count(*) FROM poc_private.ledger').fetchone(),(1,))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):issue(h,store=S2)
            self.assertEqual(issue(h),t)
            c.rollback()
            with connect('postgres') as root:self.assertEqual(root.execute('SELECT count(*) FROM poc_private.ledger').fetchone(),(1,))
            self.token(c,store=S2)
            self.assertEqual([str(r[0]) for r in c.execute('SELECT store FROM poc.records')],[S2])
    def test_concurrent_issuer_first_tuple(self):
        with connect() as c:
            h=challenge(c)
            def attempt(s):
                try:return ('ok',issue(h,store=s))
                except psycopg.errors.InsufficientPrivilege:return ('denied',None)
            with concurrent.futures.ThreadPoolExecutor(2) as pool:rs=list(pool.map(attempt,[S1,S2]))
            self.assertEqual(sorted(x[0] for x in rs),['denied','ok'])
            install(c,next(x[1] for x in rs if x[0]=='ok'))
            self.assertEqual(c.execute('SELECT count(*) FROM poc.records').fetchone(),(1,))
    def test_failed_ledger_commit_never_returns_token(self):
        with connect('postgres') as r:
            r.execute("CREATE FUNCTION poc_private.fail_commit() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'synthetic deferred failure'; END $$")
            r.execute('CREATE CONSTRAINT TRIGGER fail_commit AFTER INSERT ON poc_private.ledger DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION poc_private.fail_commit()')
        try:
            with connect() as c:
                h=challenge(c)
                with self.assertRaises(psycopg.Error):issue(h)
                with connect('postgres') as r:self.assertEqual(r.execute('SELECT count(*) FROM poc_private.ledger').fetchone(),(0,))
        finally:
            with connect('postgres') as r:r.execute('DROP TRIGGER fail_commit ON poc_private.ledger; DROP FUNCTION poc_private.fail_commit()')
        with connect() as c:self.token(c);self.assertEqual(c.execute('SELECT count(*) FROM poc.records').fetchone(),(1,))
    def test_uncommitted_ledger_not_usable(self):
        with connect() as c,connect('cac_ctx_issuer') as issuer:
            h=challenge(c);t=issuer.execute('SELECT poc.issue(%s,%s,%s,%s,%s,%s)',(h,CFG['poc_proofs'][0],S1,'read',P1,Jsonb({}))).fetchone()[0]
            install(c,t);self.deny(c);issuer.rollback()
    def test_stale_mfa_denied(self):
        with connect('postgres') as r:r.execute("UPDATE poc_private.sessions SET mfa=clock_timestamp()-interval '6 minutes'")
        with connect() as c,self.assertRaises(psycopg.errors.InsufficientPrivilege):issue(challenge(c))
    def test_store_refresh_and_hard_identity_revocation(self):
        for kind,id in [('store',S1),('session',U1),('principal',P1)]:
            seed()
            with self.subTest(kind=kind),connect() as c:
                self.token(c)
                with connect('cac_ctx_identity') as r:r.execute('SELECT poc.revoke(%s,%s)',(kind,id))
                self.deny(c,state='PZ001' if kind=='store' else '42501');c.rollback()
                if kind=='store':self.token(c);self.assertEqual(c.execute('SELECT count(*) FROM poc.records').fetchone(),(1,))
                else:
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):issue(challenge(c))
    def test_real_guard_lock_order_witness(self):
        with connect() as c:
            self.token(c);c.execute('SELECT * FROM poc.records').fetchall();pid=c.info.backend_pid
            with connect('cac_ctx_identity') as revoker,concurrent.futures.ThreadPoolExecutor(1) as pool:
                rp=revoker.info.backend_pid
                future=pool.submit(revoker.execute,'SELECT poc.revoke(%s,%s)',('session',U1))
                try:
                    with connect('postgres') as observer:
                        deadline=time.monotonic()+2
                        while pid not in observer.execute('SELECT pg_blocking_pids(%s)',(rp,)).fetchone()[0]:
                            if time.monotonic()>deadline:raise AssertionError('No blocking witness')
                            time.sleep(.01)
                    print('LOCK WITNESS runtime',pid,'blocks identity',rp,flush=True)
                finally:c.commit()
                future.result(timeout=2);revoker.commit()
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):issue(challenge(c))
    def test_key_rotation_revoke_and_generation(self):
        with connect() as c:
            h=challenge(c);t=issue(h)
            with connect('postgres') as r:
                r.execute("UPDATE poc_private.keys SET state='verify' WHERE kind='context'; INSERT INTO poc_private.keys VALUES('context','k2',public.gen_random_bytes(32),'active')")
            install(c,t);self.assertEqual(c.execute('SELECT count(*) FROM poc.records').fetchone(),(1,));c.commit()
            self.token(c);self.assertEqual(c.execute('SELECT count(*) FROM poc.records').fetchone(),(1,));c.commit()
            t=self.token(c)
            with connect('postgres') as r:r.execute("UPDATE poc_private.keys SET state='revoked' WHERE kind='context'")
            self.deny(c);c.rollback()
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):issue(challenge(c))
        seed()
        with connect() as c:
            self.token(c)
            with connect('postgres') as r:r.execute('UPDATE poc_private.config SET generation=public.gen_random_uuid()')
            self.deny(c)
    def test_issuer_unavailable_has_no_fallback(self):
        with connect('postgres') as r:r.execute('REVOKE EXECUTE ON FUNCTION poc.issue(text,text,uuid,text,uuid,jsonb) FROM cac_ctx_issuer')
        try:
            with connect() as c:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):issue(challenge(c))
                self.deny(c)
        finally:
            with connect('postgres') as r:r.execute('GRANT EXECUTE ON FUNCTION poc.issue(text,text,uuid,text,uuid,jsonb) TO cac_ctx_issuer')
    def test_connection_reuse_commit_rollback(self):
        with connect() as c:
            self.token(c);c.commit();self.deny(c);c.rollback()
            self.token(c,store=S2);self.assertEqual([str(r[0]) for r in c.execute('SELECT store FROM poc.records')],[S2]);c.rollback();self.deny(c)
    def test_retention_real_elapsed_savepoint_attack(self):
        with connect() as c:
            c.execute('SAVEPOINT original');h=challenge(c);old=self.token(c);c.execute('ROLLBACK TO SAVEPOINT original')
            print('RETENTION real120s interval started',flush=True)
            time.sleep(121)
            with connect('cac_ctx_issuer') as issuer:self.assertEqual(issuer.execute('SELECT poc.purge_ledger()').fetchone(),(1,))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):issue(h,store=S2)
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):issue(challenge(c),store=S2)
            install(c,old);self.deny(c)
    def sign_fixture(self,claims,kind='context'):
        # Trusted administrator fault injection only, never exposed to web/issuer roles.
        with connect('postgres') as r:return r.execute('SELECT poc_private.pack(%s,%s)',(Jsonb(claims),kind)).fetchone()[0]
    def test_signed_malformed_expiry_and_bindings(self):
        for field,value in [('v',3),('aud','other'),('principal',P2),('store',S2),('action','probe'),('target',P2),('digest','00'),('pid',0),('tx','0'),('session',U2),('pe',None),('exp',0),('iat',10**20)]:
            with self.subTest(field=field),connect() as c:
                token=self.token(c);claims=json.loads(bytes.fromhex(token.split('.')[0]));claims[field]=value
                install(c,self.sign_fixture(claims));self.deny(c)
        with connect() as c:
            token=self.token(c);claims=json.loads(bytes.fromhex(token.split('.')[0]));claims['exp']=claims['iat']+61
            install(c,self.sign_fixture(claims));self.deny(c)
    def test_duplicate_claims_and_key_separation(self):
        with connect() as c:
            token=self.token(c);raw=bytes.fromhex(token.split('.')[0]).decode();raw=raw[:-1]+', "principal": "'+P2+'"}'
            with connect('postgres') as r:
                forged=r.execute("SELECT encode(convert_to(%s,'UTF8'),'hex')||'.'||encode(public.hmac(convert_to(%s,'UTF8'),secret,'sha256'),'hex') FROM poc_private.keys WHERE kind='context' AND state='active'",(raw,raw)).fetchone()[0]
            install(c,forged);self.deny(c)
        with connect() as c:
            token=self.token(c);claims=json.loads(bytes.fromhex(token.split('.')[0]))
            install(c,self.sign_fixture(claims,'challenge'));self.deny(c)
    def test_challenge_forgery_and_revocation(self):
        with connect() as c:
            h=challenge(c)
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):issue(h[:-1]+('0' if h[-1]!='0' else '1'))
            t=issue(h)
            with connect('postgres') as r:r.execute("UPDATE poc_private.keys SET state='revoked' WHERE kind='challenge'")
            install(c,t);self.deny(c)
    def test_ledger_timeout_fails_closed(self):
        with connect() as c,connect('postgres') as locker:
            h=challenge(c);locker.execute('LOCK TABLE poc_private.ledger IN ACCESS EXCLUSIVE MODE')
            with connect('cac_ctx_issuer') as issuer:
                issuer.execute("SET LOCAL lock_timeout='100ms'")
                with self.assertRaises(psycopg.Error):issuer.execute('SELECT poc.issue(%s,%s,%s,%s,%s,%s)',(h,CFG['poc_proofs'][0],S1,'read',P1,Jsonb({})))
            locker.rollback()
            with connect('postgres') as r:self.assertEqual(r.execute('SELECT count(*) FROM poc_private.ledger').fetchone(),(0,))
            self.token(c);self.assertEqual(c.execute('SELECT count(*) FROM poc.records').fetchone(),(1,))
    def test_active_principal_session_epoch_only_denied(self):
        for table in ['principals','sessions']:
            seed()
            with self.subTest(table=table),connect() as c:
                self.token(c)
                with connect('postgres') as r:r.execute('UPDATE poc_private.'+table+' SET epoch=epoch+1')
                self.deny(c);c.rollback()
                self.token(c);self.assertEqual(c.execute('SELECT count(*) FROM poc.records').fetchone(),(1,))
    def test_principal_and_store_guard_blocking(self):
        for kind,id in [('principal',P1),('store',S1)]:
            seed()
            with self.subTest(kind=kind),connect() as c:
                self.token(c);c.execute('SELECT * FROM poc.records').fetchall();pid=c.info.backend_pid
                with connect('cac_ctx_identity') as r,concurrent.futures.ThreadPoolExecutor(1) as pool:
                    future=pool.submit(r.execute,'SELECT poc.revoke(%s,%s)',(kind,id))
                    try:
                        with connect('postgres') as observer:
                            deadline=time.monotonic()+2
                            while pid not in observer.execute('SELECT pg_blocking_pids(%s)',(r.info.backend_pid,)).fetchone()[0]:
                                if time.monotonic()>deadline:raise AssertionError('Missing '+kind+' lock witness')
                                time.sleep(.01)
                        print('LOCK WITNESS',kind,pid,'blocks',r.info.backend_pid,flush=True)
                    finally:c.commit()
                    future.result(timeout=2);r.commit()
                if kind=='principal':
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):issue(challenge(c))
                else:self.token(c);self.assertEqual(c.execute('SELECT count(*) FROM poc.records').fetchone(),(1,))
