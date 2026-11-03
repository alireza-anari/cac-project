"""Controlled PostgreSQL clock fixtures are distinct from real elapsed tests."""
import contextlib
from decimal import Decimal
import json
import time
import unittest
from psycopg.types.json import Jsonb
from context_poc.harness import connect, seed, challenge, issue, install, S1
from pool_recovery.lab import Lab

@contextlib.contextmanager
def frozen(name, now):
    with connect('postgres') as r:
        definition=r.execute('SELECT pg_get_functiondef(%s::regprocedure)',(name,)).fetchone()[0]
        assert 'clock_timestamp()' in definition
        r.execute(definition.replace('clock_timestamp()',f'to_timestamp({now})'))
    try: yield
    finally:
        with connect('postgres') as r: r.execute(definition)

def claims(token): return json.loads(bytes.fromhex(token.split('.')[0]), parse_float=Decimal)
def sign(p,kind):
    # Decimal round trip avoids Python float loss near exact boundaries.
    import psycopg
    with connect('postgres') as r:
        # JSON encoder below preserves decimal numerics via an exact JSON text cast.
        import re
        text=json.dumps(p,default=lambda x: '__numeric_'+str(x))
        text=re.sub(r'"__numeric_(-?[0-9.]+)"',r'\1',text)
        return r.execute('SELECT poc_private.pack(%s::jsonb,%s)',(text,kind)).fetchone()[0]

class TimingTests(unittest.TestCase):
    def setUp(self): seed()
    def deny(self,c):
        import psycopg
        with self.assertRaises(psycopg.errors.InsufficientPrivilege): c.execute('SELECT * FROM poc.records').fetchall()

    def test_exact_challenge_start_plus_five_and_clock_skew(self):
        import psycopg
        for age,allowed in [(Decimal('0'),True),(Decimal('5'),True),(Decimal('5.000001'),False),(Decimal('-0.000001'),False)]:
            seed()
            with connect() as c:
                h=claims(challenge(c))
                with connect('postgres') as r:
                    now=r.execute('SELECT extract(epoch FROM clock_timestamp())').fetchone()[0]
                    r.execute('UPDATE poc_private.sessions SET mfa=to_timestamp(%s)',(now,))
                h['started']=now-age
                with frozen('poc.issue(text,text,uuid,text,uuid,jsonb)',now):
                    if allowed: self.assertTrue(issue(sign(h,'challenge')))
                    else:
                        with self.assertRaises(psycopg.errors.InsufficientPrivilege): issue(sign(h,'challenge'))

    def test_exact_token_expiry_and_future_iat(self):
        for delta,allowed in [(Decimal('0.000001'),True),(Decimal('0'),False),(Decimal('-0.000001'),False)]:
            seed()
            with connect() as c:
                t=issue(challenge(c)); p=claims(t); now=p['exp']-delta
                install(c,t)
                with frozen('poc.verify()',now):
                    if allowed:self.assertEqual(c.execute('SELECT count(*) FROM poc.records').fetchone(),(1,))
                    else:self.deny(c)
        for skew,allowed in [(Decimal('5'),True),(Decimal('5.000001'),False)]:
            seed()
            with connect() as c:
                p=claims(issue(challenge(c)))
                with connect('postgres') as r: now=r.execute('SELECT extract(epoch FROM clock_timestamp())').fetchone()[0]
                p['iat']=now+skew;p['exp']=now+30
                install(c,sign(p,'context'))
                with frozen('poc.verify()',now):
                    if allowed:self.assertEqual(c.execute('SELECT count(*) FROM poc.records').fetchone(),(1,))
                    else:self.deny(c)

    def test_exact_mfa_freshness_after_token_issuance(self):
        for age,allowed in [(Decimal('300'),True),(Decimal('300.000001'),False),(Decimal('-0.000001'),False)]:
            seed()
            with connect() as c:
                t=issue(challenge(c));install(c,t)
                with connect('postgres') as r:
                    now=r.execute('SELECT extract(epoch FROM clock_timestamp())').fetchone()[0]
                    r.execute('UPDATE poc_private.sessions SET mfa=to_timestamp(%s)',(now-age,))
                with frozen('poc.verify()',now):
                    if allowed:self.assertEqual(c.execute('SELECT count(*) FROM poc.records').fetchone(),(1,))
                    else:self.deny(c)

    def test_exact_cleanup_boundary_no_reissue_or_replay(self):
        import psycopg
        with connect() as c:
            h=challenge(c);t=issue(h)
            with connect('postgres') as r:
                started=r.execute('SELECT extract(epoch FROM started) FROM poc_private.ledger').fetchone()[0]
            with frozen('poc.purge_ledger()',started+120),connect('cac_ctx_issuer') as r:
                self.assertEqual(r.execute('SELECT poc.purge_ledger()').fetchone(),(0,))
            with frozen('poc.purge_ledger()',started+Decimal('120.000001')),connect('cac_ctx_issuer') as r:
                self.assertEqual(r.execute('SELECT poc.purge_ledger()').fetchone(),(1,))
            with frozen('poc.issue(text,text,uuid,text,uuid,jsonb)',started+121):
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):issue(h)
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):issue(challenge(c))
            install(c,t);self.deny(c)

    def test_real_elapsed_long_transaction_and_token_expiration(self):
        # Actual clock, actual runtime UID, actual transaction pool; no clock replacement.
        with Lab() as lab, lab.worker() as w:
            h=w.call('challenge');t=w.call('issue',h=h)['token'];w.call('install',token=t)
            self.assertEqual(w.call('records'),[S1]);w.call('sql',q='SAVEPOINT released_guards')
            time.sleep(5.1)
            self.assertEqual(w.call('issue',h=h),{'ok':False,'error':'denied'})
            # Still usable during issued TTL despite expired challenge.
            self.assertEqual(w.call('records'),[S1])
            print('ELAPSED token expiry wait: real 60+ seconds',flush=True)
            time.sleep(55.2)
            w.deny();w.call('rollback');w.deny()

    def test_real_elapsed_mfa_becomes_stale_after_issue(self):
        with Lab() as lab:
            with connect('postgres') as r:
                r.execute("UPDATE poc_private.sessions SET mfa=clock_timestamp()-interval '298 seconds'")
            with lab.worker() as w:
                t=w.call('issue')['token'];w.call('install',token=t)
                time.sleep(2.1)
                w.deny()

    def test_jsonb_canonicalization_interoperability_and_mac(self):
        # Compare typed values and exact bytes, NOT a proposed replacement wire format.
        import hashlib,hmac
        specimens=['{"a":1,"b":"é"}','{"b":"é","a":1.0}',
                   '{"z":-0,"a":[true,null,"\\u0061"]}', '{"a":1,"a":2}']
        with connect('postgres') as r:
            secret=r.execute("SELECT secret FROM poc_private.keys WHERE kind='context'").fetchone()[0]
            for raw in specimens:
                packed=r.execute("SELECT poc_private.pack(%s::jsonb,'context')",(raw,)).fetchone()[0]
                payload,mac=packed.split('.');b=bytes.fromhex(payload)
                self.assertTrue(hmac.compare_digest(hmac.new(bytes(secret),b,hashlib.sha256).hexdigest(),mac))
                value=json.loads(b)
                self.assertEqual(value['a'],json.loads(raw)['a'])
                py=json.dumps(value,sort_keys=True,ensure_ascii=False).encode()
                print('ENCODING WITNESS python_bytes_equal_postgres',py==b,'input_class',specimens.index(raw),flush=True)
        with connect() as c:
            t=issue(challenge(c));p,mac=t.split('.')
            # Correctly MACed but noncanonical bytes must still fail unpack.
            b=json.dumps(json.loads(bytes.fromhex(p)),separators=(',',':')).encode()
            with connect('postgres') as r:
                m=r.execute("SELECT encode(public.hmac(%s,secret,'sha256'),'hex') FROM poc_private.keys WHERE kind='context'",(b,)).fetchone()[0]
            install(c,b.hex()+'.'+m);self.deny(c)
