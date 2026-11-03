import concurrent.futures
import time
import unittest
from context_poc.harness import connect, seed, S1, S2, U1, P1
from pool_recovery.lab import Lab

class PoolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.lab=Lab()
    @classmethod
    def tearDownClass(cls): cls.lab.close()
    def setUp(self): seed()
    def witness(self,w):
        row=w.call('sql',q='SELECT session_user,current_user,pg_backend_pid(),txid_current()::text')[0]
        self.assertEqual(row[:2], ['cac_ctx_runtime','cac_ctx_runtime'])
        print('POOL WITNESS login/role/pid/tx',row,flush=True)
        return row

    def test_backend_reuse_commit_rollback_and_session_set(self):
        with self.lab.worker() as a, self.lab.worker() as b:
            first=self.witness(a)
            token=a.call('issue')['token']; a.call('install',token=token)
            self.assertEqual(a.call('records'),[S1]); self.assertEqual(self.witness(a),first)
            # Deliberate hostile session-level SET survives pool transaction release.
            a.call('sql',q="SELECT set_config('cac.poc_context',%s,false)",params=[token])
            a.call('commit')
            second=self.witness(b)
            self.assertEqual(first[2],second[2]); self.assertNotEqual(first[3],second[3])
            b.deny(); b.call('rollback')
            self.assertEqual(b.call('scope',store=S2),[S2]); b.call('rollback')
            a.deny(); a.call('rollback')
            a.call('install',token=token); a.deny()

    def test_savepoint_does_not_erase_detached_ledger(self):
        with self.lab.worker() as w:
            w.call('sql',q='SAVEPOINT before_context')
            h=w.call('challenge'); token=w.call('issue',h=h)['token']
            w.call('install',token=token); self.assertEqual(w.call('records'),[S1])
            w.call('sql',q='ROLLBACK TO SAVEPOINT before_context')
            self.assertEqual(w.call('issue',h=h,store=S2),{'ok':False,'error':'denied'})
            self.assertEqual(w.call('issue',h=h)['token'],token)
            w.call('rollback'); w.deny()
        with connect('postgres') as c: self.assertEqual(c.execute('SELECT count(*) FROM poc_private.ledger').fetchone(),(1,))

    def test_cancel_and_sql_error_reset_pool(self):
        with self.lab.worker() as w:
            self.assertEqual(w.call('scope'),[S1]); pid=self.witness(w)[2]
            with concurrent.futures.ThreadPoolExecutor(1) as pool:
                future=pool.submit(w.reply,'sql',q='SELECT pg_sleep(10)')
                with connect('postgres') as c:
                    deadline=time.monotonic()+3
                    while c.execute("SELECT wait_event FROM pg_stat_activity WHERE pid=%s",(pid,)).fetchone()[0]!='PgSleep':
                        c.commit()
                        if time.monotonic()>deadline: self.fail('missing cancellation wait witness')
                        time.sleep(.01)
                    self.assertEqual(c.execute('SELECT pg_cancel_backend(%s)',(pid,)).fetchone(),(True,))
                self.assertEqual(future.result(timeout=3),{'ok':False,'state':'57014'})
            w.deny('sql',state='25P02',q='SELECT 1'); w.call('rollback'); w.deny(); w.call('rollback')
            w.deny('sql',state='22012',q='SELECT 1/0'); w.call('rollback')
            self.assertEqual(w.call('scope',store=S2),[S2]); w.call('commit')
        with self.lab.worker() as w: w.deny()

    def test_four_concurrent_scopes_with_distinct_backends(self):
        import threading
        barrier=threading.Barrier(4)
        def request(i):
            with self.lab.worker(many=True) as w:
                row=self.witness(w); h=w.call('challenge'); barrier.wait(timeout=4)
                r=w.call('issue',h=h,store=S1 if i%2==0 else S2)
                self.assertTrue(r['ok']); w.call('install',token=r['token'])
                result=w.call('records'); w.call('commit'); w.deny(); w.call('rollback')
                return row[2],result
        with concurrent.futures.ThreadPoolExecutor(4) as pool: results=list(pool.map(request,range(4)))
        self.assertEqual(len({x[0] for x in results}),4)
        self.assertEqual([x[1] for x in results],[[S1],[S2],[S1],[S2]])

    def test_revocation_under_concurrent_read_load_no_retry_resurrection(self):
        # New transactions after the acknowledged revocation must all deny issuance.
        with connect('cac_ctx_identity') as r: r.execute('SELECT poc.revoke(%s,%s)',('session',U1))
        def request(i):
            with self.lab.worker(many=True) as w:
                for _ in range(3):
                    self.assertEqual(w.call('issue',store=S1 if i%2==0 else S2),{'ok':False,'error':'denied'})
                    w.deny(); w.call('rollback')
        with concurrent.futures.ThreadPoolExecutor(4) as pool: list(pool.map(request,range(4)))
        with connect('postgres') as r:
            self.assertEqual(r.execute('SELECT active,epoch FROM poc_private.sessions WHERE id=%s',(U1,)).fetchone(),(False,2))
            self.assertEqual(r.execute('SELECT count(*) FROM poc_private.ledger').fetchone(),(0,))

    def test_lock_timeout_then_revoke_blocks_issuer_retry(self):
        with connect('postgres') as lock, self.lab.worker() as w:
            lock.execute('UPDATE poc_private.sessions SET active=false,epoch=epoch+1 WHERE id=%s',(U1,))
            h=w.call('challenge')
            self.assertEqual(w.call('issue',h=h),{'ok':False,'error':'denied'})
            lock.commit()
            self.assertEqual(w.call('issue',h=h),{'ok':False,'error':'denied'})
            w.deny()
        with connect('postgres') as r: self.assertEqual(r.execute('SELECT count(*) FROM poc_private.ledger').fetchone(),(0,))

    def test_store_epoch_contention_and_new_transaction_refresh(self):
        with self.lab.worker() as w:
            self.assertEqual(w.call('scope'),[S1]); pid=self.witness(w)[2]
            with connect('cac_ctx_identity') as r, concurrent.futures.ThreadPoolExecutor(1) as pool:
                rp=r.info.backend_pid
                future=pool.submit(r.execute,'SELECT poc.revoke(%s,%s)',('store',S1))
                try:
                    with connect('postgres') as observer:
                        end=time.monotonic()+3
                        while pid not in observer.execute('SELECT pg_blocking_pids(%s)',(rp,)).fetchone()[0]:
                            if time.monotonic()>end:self.fail('missing store epoch lock witness')
                            time.sleep(.01)
                        print('STORE LOCK WITNESS',pid,'blocks',rp,flush=True)
                finally: w.call('commit')
                future.result(timeout=3); r.commit()
            self.assertEqual(w.call('scope'),[S1]); w.call('rollback')

    def test_deadlock_aborts_one_transaction_and_pool_stays_usable(self):
        # Deliberate administrator fault injection locks synthetic principal then session
        # opposite to verifier order. No product lock schedule is claimed safe.
        with self.lab.worker() as w, connect('postgres') as lock:
            token=w.call('issue')['token']; w.call('install',token=token)
            lock.execute("SET LOCAL deadlock_timeout='100ms'")
            lock.execute('UPDATE poc_private.sessions SET epoch=epoch WHERE id=%s',(U1,))
            with concurrent.futures.ThreadPoolExecutor(1) as pool:
                future=pool.submit(w.reply,'records')
                with connect('postgres') as observer:
                    end=time.monotonic()+3
                    while not observer.execute('SELECT pg_blocking_pids(pid) FROM pg_stat_activity WHERE usename=%s AND wait_event_type=%s',('cac_ctx_runtime','Lock')).fetchall():
                        if time.monotonic()>end:self.fail('missing deadlock precursor')
                        time.sleep(.01)
                import psycopg
                try: lock.execute('UPDATE poc_private.principals SET epoch=epoch WHERE id=%s',(P1,)); outcome='runtime-victim'
                except psycopg.errors.DeadlockDetected: outcome='admin-victim'
                lock.rollback()
                result=future.result(timeout=4)
                print('DEADLOCK WITNESS',outcome,result.get('state','read-completed'),flush=True)
                if outcome=='runtime-victim': self.assertEqual(result,{'ok':False,'state':'42501'})
                else: self.assertEqual(result,{'ok':True,'value':[S1]})
                w.call('rollback'); self.assertEqual(w.call('scope'),[S1]); w.call('commit')

    def test_issuance_racing_principal_revoke_has_no_revived_authority(self):
        with connect('cac_ctx_identity') as revoker, concurrent.futures.ThreadPoolExecutor(4) as pool:
            workers=[self.lab.worker(many=True) for _ in range(4)]
            try:
                hs=[w.call('challenge') for w in workers]
                revoker.execute('SELECT poc.revoke(%s,%s)',('principal',P1))
                futures=[pool.submit(w.call,'issue',h=h) for w,h in zip(workers,hs)]
                with connect('postgres') as observer:
                    end=time.monotonic()+2
                    while not observer.execute("SELECT pid,pg_blocking_pids(pid) FROM pg_stat_activity WHERE usename='cac_ctx_issuer' AND wait_event_type='Lock'").fetchall():
                        if time.monotonic()>end:self.fail('missing issuance/revoke race witness')
                        time.sleep(.01)
                    print('REVOKE RACE WITNESS issuer blocked by uncommitted principal revocation',flush=True)
                revoker.commit()
                for w,future in zip(workers,futures):
                    self.assertEqual(future.result(timeout=3),{'ok':False,'error':'denied'})
                    w.deny();w.call('rollback')
                    self.assertEqual(w.call('issue'),{'ok':False,'error':'denied'})
            finally:
                revoker.rollback()
                for w in workers:w.close()
        with connect('postgres') as r:
            self.assertEqual(r.execute('SELECT active,epoch FROM poc_private.principals WHERE id=%s',(P1,)).fetchone(),(False,2))
            self.assertEqual(r.execute('SELECT count(*) FROM poc_private.ledger').fetchone(),(0,))
