import json
import os
import subprocess
import time
import unittest
import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
from context_poc.harness import CFG, connect, seed, S1, S2, P1
from pool_recovery.lab import Lab

class RecoveryTests(unittest.TestCase):
    def setUp(self): seed()

    def test_postgres_restart_persists_ledger_but_kills_old_transaction(self):
        container=os.environ['CAC_POSTGRES_CONTAINER']
        with Lab() as lab, lab.worker() as w:
            h=w.call('challenge');t=w.call('issue',h=h)['token'];w.call('install',token=t)
            self.assertEqual(w.call('records'),[S1])
            with connect('postgres') as r:
                before=r.execute('SELECT generation::text,tx,pid,token FROM poc_private.ledger').fetchall()
            subprocess.run(['docker','restart','--time','2',container],stdout=subprocess.DEVNULL,check=True,timeout=30)
            deadline=time.monotonic()+20
            while True:
                try:
                    with connect('postgres') as r:
                        self.assertEqual(r.execute('SELECT generation::text,tx,pid,token FROM poc_private.ledger').fetchall(),before)
                    break
                except psycopg.OperationalError:
                    if time.monotonic()>deadline:raise
                    time.sleep(.2)
            self.assertFalse(w.reply('records')['ok'])
            with lab.worker() as fresh:
                fresh.call('install',token=t);fresh.deny();fresh.call('rollback')
                self.assertEqual(fresh.call('scope',store=S2),[S2])
            print('RECOVERY WITNESS actual container restart; committed ledger persisted; old transaction dead',flush=True)

    def test_logical_restore_requires_explicit_generation_fence(self):
        container=os.environ['CAC_POSTGRES_CONTAINER'];dbname='cac_s009b_restore'
        with Lab() as lab,lab.worker() as w:
            h=w.call('challenge');t=w.call('issue',h=h)['token']
            with connect('postgres') as r:
                r.autocommit=True
                r.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(dbname)))
            conn=dict(CFG['connection'],dbname=dbname)
            def restored(role='postgres'):
                return psycopg.connect(**conn,user=role,password=CFG['passwords'][role],prepare_threshold=None)
            try:
                with restored() as r: r.execute('CREATE EXTENSION pgcrypto')
                # Dump is kept in memory only, never an uploaded artifact (contains synthetic keys).
                dump=subprocess.run(['docker','exec',container,'pg_dump','-U','postgres','-d','cac_s007_test',
                    '-Fc','-n','poc','-n','poc_private'],capture_output=True,check=True,timeout=20).stdout
                subprocess.run(['docker','exec','-i',container,'pg_restore','-U','postgres','-d',dbname,
                    '--exit-on-error'],input=dump,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=20)
                del dump
                with restored() as r:
                    self.assertEqual(r.execute('SELECT count(*) FROM poc_private.ledger').fetchone(),(1,))
                args=(h,CFG['poc_proofs'][0],S1,'read',P1,Jsonb({}))
                # Restore preserves signing authority and a still-current challenge!
                # This is a measured limitation, not success of automatic recovery fencing.
                with restored('cac_ctx_issuer') as r:
                    same=r.execute('SELECT poc.issue(%s,%s,%s,%s,%s,%s)',args).fetchone()[0]
                    self.assertTrue(same==t)
                with restored() as r:r.execute('UPDATE poc_private.config SET generation=public.gen_random_uuid()')
                with restored('cac_ctx_issuer') as r:
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):r.execute('SELECT poc.issue(%s,%s,%s,%s,%s,%s)',args)
                with restored('cac_ctx_runtime') as r:
                    r.execute("SELECT set_config('cac.poc_context',%s,true)",(t,))
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):r.execute('SELECT * FROM poc.records').fetchall()
                    r.rollback()
                    fresh=r.execute('SELECT poc.challenge()').fetchone()[0]
                    with restored('cac_ctx_issuer') as issuer:
                        new=issuer.execute('SELECT poc.issue(%s,%s,%s,%s,%s,%s)',(fresh,*args[1:])).fetchone()[0]
                    r.execute("SELECT set_config('cac.poc_context',%s,true)",(new,))
                    self.assertEqual([str(x[0]) for x in r.execute('SELECT store FROM poc.records')],[S1])
                print('RESTORE WITNESS unfenced issuer replays ledger response; explicit generation fence rejects old challenge/token',flush=True)
            finally:
                with connect('postgres') as r:
                    r.autocommit=True
                    r.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(dbname)))

    def test_generation_change_stale_runtime_and_session_revocation(self):
        from context_poc.harness import U1
        with Lab() as lab,lab.worker() as w:
            h=w.call('challenge');t=w.call('issue',h=h)['token'];w.call('install',token=t)
            with connect('postgres') as r:r.execute('UPDATE poc_private.config SET generation=public.gen_random_uuid()')
            w.deny();w.call('rollback')
            self.assertEqual(w.call('issue',h=h),{'ok':False,'error':'denied'})
            with connect('cac_ctx_identity') as r:r.execute('SELECT poc.revoke(%s,%s)',('session',U1))
            self.assertEqual(w.call('issue'),{'ok':False,'error':'denied'});w.deny()
