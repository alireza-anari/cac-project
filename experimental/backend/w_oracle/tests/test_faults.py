"""W_ORACLE_ASSUMED. Crash/fault schedule evidence; not W-root or orphan recovery."""
import concurrent.futures
import os
import subprocess
import sys
import threading
import time
from uuid import uuid4
import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from recovery_fencing.broker import FenceDenied
from recovery_fencing.lab import S1,P1
from recovery_proof.pool_lab import Pool
from w_oracle.lab import BANNER
from w_oracle.broker import Broker,Gate
from w_oracle.ack_loss import CommitReplyLoss
from w_oracle.tests.test_integration import IntegrationFixture


class FaultTests(IntegrationFixture):
    def live_paths_fault(self,install,restore,label):
        observed=[]
        with self.assertRaises(FenceDenied):
            with self.a.runtime() as runtime:
                args=[runtime.challenge(),self.a.cfg['proof'],S1,'read',P1,Jsonb({})]
                with Gate(self.a,'cac_ctx_issuer',args=args) as issuer:
                    query='SELECT poc.issue(%s,%s,%s,%s,%s,%s)'
                    token=issuer.c.execute(query,args).fetchone()[0]
                    runtime.install(token);self.assertEqual(runtime.records(),[S1])
                    # Same live issuer ticket + exact arguments succeed before
                    # fault; missing ticket/invalid NULL args cannot mask it.
                    self.assertTrue(issuer.c.execute(query,args).fetchone()[0] is not None)
                    try:
                        install();self.assertFalse(self.a.ready())
                        with self.assertRaises(psycopg.errors.InsufficientPrivilege):issuer.c.execute(query,args)
                        with self.assertRaises(psycopg.errors.InsufficientPrivilege):runtime.records()
                        observed.append(True)
                    finally:restore()
        self.assertEqual(observed,[True],'Fault denied setup instead of tested valid issuer/RLS paths')
        print(BANNER,'LIVE PATH CAUSALITY',label,'same known-valid issuer args/ticket and installed context denied only after fault; unresolved holds retained',flush=True)
    def wait_w(self):
        end=time.monotonic()+15
        while True:
            try:
                with self.lab.oracle.connect() as w:w.execute('SELECT 1')
                return
            except psycopg.Error:
                if time.monotonic()>end:raise
                time.sleep(.05)
    def restart_w(self):
        self.lab.parent.docker('restart','--time','1',self.lab.oracle.cfg['container']);self.wait_w()
    def blocked(self):
        # Exercise the actual OPEN exclusion, never an unadmitted-actor denial.
        self.lab.restore()
        with self.lab.oracle.connect('B') as w:
            self.assertEqual(w.execute('SELECT w.status()').fetchone()[0]['epoch'],1)
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):w.execute('SELECT w.reserve(1,%s)',(str(uuid4()),))
        self.assertFalse(self.a.ready())
    def worker(self,stage):
        result=subprocess.run([sys.executable,'-m','w_oracle.worker',stage],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,77,'Actual process crash cut was not reached')
        self.assertTrue(BANNER in result.stdout and ('CRASH_CUT '+stage) in result.stdout,'Missing crash receipt')
        print(BANNER,'PROCESS os._exit77',stage,flush=True)
    def test_crash_cuts_durable_open_remain_blocked_across_w_restart(self):
        cuts=['after_durable_open','before_first_use','after_first_use','after_final_guard',
              'before_local_commit','after_local_commit_before_close','after_local_abort_before_close',
              'after_c_finish_before_w_close','after_w_close_before_commit']
        for index,stage in enumerate(cuts):
            with self.subTest(cut=stage):
                if index:
                    self.lab.reset();self.a=Broker(self.lab);self.b=Broker(self.lab,'B');self.a.activate(0,str(uuid4()))
                self.worker(stage);self.restart_w()
                with self.lab.oracle.connect() as w:
                    self.assertEqual(w.execute("SELECT count(*) FROM w.ops WHERE phase IN ('open','unknown')").fetchone(),(1,))
                self.blocked()
                print(BANNER,'CRASH/RESTART unresolved intent retained; no successor permit',stage,flush=True)
    def test_crash_before_open_commit_issued_no_permit(self):
        self.worker('before_open_commit')
        with self.lab.oracle.connect() as w:self.assertEqual(w.execute('SELECT count(*) FROM w.ops').fetchone(),(0,))
        self.takeover()
    def test_crash_after_close_ack_allows_new_epoch(self):
        self.worker('after_close_ack');self.no_open();self.takeover()
    def test_actual_lost_local_commit_reply_keeps_unknown(self):
        self.positive(self.a)
        with self.lab.connect() as c:
            before=c.execute('SELECT count(*) FROM poc_private.ledger').fetchone()[0]
            self.assertEqual(c.execute("SELECT current_setting('fsync'),current_setting('synchronous_commit')").fetchone(),('on','on'))
        proxy=CommitReplyLoss();self.addCleanup(proxy.close)
        class LossBroker(Broker):
            def local(inner,role):
                if role!='cac_ctx_issuer':return super().local(role)
                config=dict(inner.cfg['connection'],port=proxy.port)
                return psycopg.connect(**config,user=role,password=inner.cfg['passwords'][role],
                    sslmode='disable',connect_timeout=2,prepare_threshold=None,
                    options='-c statement_timeout=3000 -c lock_timeout=700')
        def hook(stage):
            if stage=='before_local_commit':proxy.armed.set()
        broker=LossBroker(self.lab,hook=hook)
        with self.assertRaises(FenceDenied):
            with self.a.runtime() as g:broker.issue(g.challenge())
        self.assertTrue(proxy.dropped.wait(2),'COMMIT CommandComplete was not actually intercepted')
        self.assertEqual(proxy.errors,[],'Wire fixture error instead of intended lost reply')
        with self.lab.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM poc_private.ledger').fetchone(),(before+1,))
        with self.lab.oracle.connect() as w:
            self.assertEqual(w.execute("SELECT kind,phase FROM w.ops WHERE phase='unknown'").fetchall(),[('issuer','unknown')])
        self.restart_w();self.blocked()
        print(BANNER,'WIRE COMMIT completed, reply dropped; committed ledger observed; issuer UNKNOWN durable; successor BLOCKED',flush=True)
    def test_actual_lost_open_commit_reply_never_issues_permit(self):
        proxy=CommitReplyLoss(target_port=5435);self.addCleanup(proxy.close)
        original=self.lab.oracle.connect;cfg=self.lab.oracle.cfg;actor=cfg['actors']['A']
        def connection(node=None,check=False):
            if node!='A' or check:return original(node,check)
            return psycopg.connect(**dict(cfg['connection'],port=proxy.port),user=actor['coord'],
                password=actor['coord_password'],sslmode='disable',connect_timeout=2,prepare_threshold=None,
                options='-c statement_timeout=3000 -c lock_timeout=700')
        self.lab.oracle.connect=connection
        self.a.hook=lambda stage:proxy.armed.set() if stage=='before_open_commit' else None
        try:
            with self.assertRaises(FenceDenied):
                with self.a.runtime():self.fail('Permit returned after ambiguous OPEN ACK')
        finally:self.lab.oracle.connect=original
        self.assertTrue(proxy.dropped.wait(2),'Durable OPEN COMMIT reply was not actually intercepted')
        self.assertEqual(proxy.errors,[],'Unexpected wire fixture error')
        with self.lab.oracle.connect() as w:self.assertEqual(w.execute('SELECT phase FROM w.ops').fetchall(),[('open',)])
        with self.lab.connect('C') as c:self.assertEqual(c.execute('SELECT count(*) FROM anchor.operations').fetchone(),(0,))
        self.restart_w();self.blocked()
        print(BANNER,'WIRE durable OPEN committed, reply dropped; no hold/permit/local authorization; OPEN durable, successor BLOCKED',flush=True)
    def test_delayed_open_ack_cannot_start_after_revoke_intent(self):
        self.lab.restore()
        self.positive(self.a)
        def hook(stage):
            if stage=='after_durable_open':
                with self.lab.oracle.connect('B') as w:w.execute('SELECT w.revoke(1)')
        self.a.hook=hook
        with self.assertRaises(FenceDenied):
            with self.a.runtime():self.fail('Delayed permit became usable after revoke')
        self.blocked()
        with self.lab.oracle.connect() as w:
            self.assertEqual(w.execute("SELECT phase FROM w.state").fetchone(),('revoking',))
        print(BANNER,'DELAYED admission ACK + revoke before hold/first use -> DENIED, OPEN retained',flush=True)
    def test_w_outage_denies_existing_rls_issuer_and_new_gate(self):
        def stop():self.lab.parent.docker('stop','--time','1',self.lab.oracle.cfg['container'])
        def start():self.lab.parent.docker('start',self.lab.oracle.cfg['container']);self.wait_w()
        self.live_paths_fault(stop,start,'actual W process outage')
        self.blocked()
        print(BANNER,'actual W process outage -> SQL/RLS/issuer/new admission fail-closed; original OPEN durable',flush=True)
    def test_one_channel_partition_denies_without_c_fallback(self):
        with self.lab.connect() as c:
            before=c.execute('SELECT checker_conn FROM w_guard.config').fetchone()[0]
        def install():
            with self.lab.connect() as c:c.execute("UPDATE w_guard.config SET checker_conn='host=127.0.0.1 port=1 dbname=unreachable connect_timeout=1'")
        def restore():
            with self.lab.connect() as c:c.execute('UPDATE w_guard.config SET checker_conn=%s',(before,))
        self.live_paths_fault(install,restore,'checker-only connection refusal')
        with self.lab.oracle.connect() as w:self.assertEqual(w.execute('SELECT epoch,phase FROM w.state').fetchone(),(1,'active'))
        self.blocked()
        print(BANNER,'checker-channel connection refusal while W coordinator is reachable -> DENIED; exact config restored',flush=True)
    def test_wrong_root_namespace_policy_and_old_actor_are_denied(self):
        cases=[('root',str(uuid4())),('namespace',str(uuid4())),('policy',999),('incarnation',str(uuid4())),('actor',str(uuid4()))]
        for index,(field,value) in enumerate(cases):
            with self.subTest(binding=field):
                if index:
                    # Independent synthetic test genesis, never OPEN recovery.
                    self.lab.reset();self.a=Broker(self.lab);self.b=Broker(self.lab,'B');self.a.activate(0,str(uuid4()))
                if field=='actor':
                    old=self.lab.oracle.cfg['actors']['A']['incarnation']
                    def install():
                        with self.lab.oracle.connect() as w:w.execute("UPDATE w.actors SET incarnation=%s WHERE node='A'",(value,))
                    def restore():
                        with self.lab.oracle.connect() as w:w.execute("UPDATE w.actors SET incarnation=%s WHERE node='A'",(old,))
                else:
                    with self.lab.connect() as c:old=c.execute(sql.SQL('SELECT {} FROM w_guard.config').format(sql.Identifier(field))).fetchone()[0]
                    def install():
                        with self.lab.connect() as c:c.execute(sql.SQL('UPDATE w_guard.config SET {}=%s').format(sql.Identifier(field)),(value,))
                    def restore():
                        with self.lab.connect() as c:c.execute(sql.SQL('UPDATE w_guard.config SET {}=%s').format(sql.Identifier(field)),(old,))
                self.live_paths_fault(install,restore,field)
                self.blocked()
    def test_valid_old_signed_response_cannot_satisfy_fresh_challenge(self):
        self.positive(self.a);actor=self.lab.oracle.cfg['actors']['A']
        with self.lab.oracle.connect('A',check=True) as w:
            proof=w.execute("SELECT w.attest(%s,'active','',%s,123,'456',%s,'','cac_ctx_runtime')",('e'*64,self.lab.cfg['A']['sid'],actor['manifest'])).fetchone()[0]
        signature='w.attest(text,text,text,text,int,text,text,text,text)'
        with self.lab.oracle.connect() as w:before=w.execute('SELECT pg_get_functiondef(%s::regprocedure)',(signature,)).fetchone()[0]
        def install():
            with self.lab.oracle.connect() as w:
                body="CREATE OR REPLACE FUNCTION w.attest(n text,mode_arg text,t text,sid_arg text,pid_arg int,tx_arg text,man text,d text,login_arg text) RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,w AS $stale$ BEGIN RETURN {};END $stale$"
                w.execute(sql.SQL(body).format(sql.Literal(proof)))
        def restore():
            with self.lab.oracle.connect() as w:w.execute(before)
            with self.lab.oracle.connect() as w:self.assertTrue(w.execute('SELECT pg_get_functiondef(%s::regprocedure)',(signature,)).fetchone()[0]==before,'Stale-response fixture restoration drift')
        self.live_paths_fault(install,restore,'actual valid stale signed response')
        self.blocked()
        print(BANNER,'actual valid old W signature replay denied on fresh nonce/mode/transcript; signer function restored',flush=True)
    def test_paired_takeover_cas_race_has_one_winner_no_early_ready(self):
        self.positive(self.a);self.lab.restore();barrier=threading.Barrier(2)
        requests={n:str(uuid4()) for n in ['A','B']}
        def reserve(node):
            barrier.wait(timeout=3)
            try:
                with self.lab.oracle.connect(node) as w:
                    result=w.execute('SELECT w.reserve(1,%s)',(requests[node],)).fetchone()[0]
                return node,result['epoch']
            except psycopg.errors.InsufficientPrivilege:return node,'DENIED'
        with concurrent.futures.ThreadPoolExecutor(2) as workers:results=list(workers.map(reserve,['A','B']))
        winners=[n for n,r in results if r==2]
        self.assertEqual(len(winners),1);self.assertEqual(sum(r=='DENIED' for _,r in results),1)
        self.assertFalse(self.a.ready());self.assertFalse(self.b.ready())
        winner=self.a if winners[0]=='A' else self.b
        self.assertEqual(winner.activate(1,requests[winners[0]])['epoch'],2);self.positive(winner)
        print(BANNER,'PAIRED CAS RACE',results,'reserved successor NOT_READY until committed app ACK and W activation',flush=True)
    def test_concurrent_local_transactions_hold_independent_bound_operations(self):
        self.lab.restore()
        barrier=threading.Barrier(2)
        def operation(_):
            broker=Broker(self.lab)
            with broker.runtime() as g:
                self.scope(broker,g)
                binding=g.c.execute('SELECT pg_backend_pid(),txid_current()::text').fetchone()
                barrier.wait(timeout=3)
                with self.lab.oracle.connect('B') as rival:
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):rival.execute('SELECT w.reserve(1,%s)',(str(uuid4()),))
                return binding
        with concurrent.futures.ThreadPoolExecutor(2) as workers:bindings=list(workers.map(operation,range(2)))
        self.assertNotEqual(bindings[0][0],bindings[1][0]);self.assertNotEqual(bindings[0][1],bindings[1][1])
        self.no_open()
        print(BANNER,'CONCURRENT local transactions distinct PID/fullxid',bindings,'each held until local ACK; successor denied',flush=True)
    def test_prepared_transaction_is_actually_prohibited(self):
        with self.assertRaises(FenceDenied):
            with self.a.runtime() as g:
                with self.assertRaises(psycopg.Error) as caught:g.c.execute("PREPARE TRANSACTION 'synthetic-s009f-forbidden'")
                self.assertEqual(caught.exception.sqlstate,'55000')
        self.assertEqual(caught.exception.sqlstate,'55000')
        for node in ['A','B','C']:
            with self.lab.connect(node) as c:
                self.assertEqual(c.execute('SHOW max_prepared_transactions').fetchone(),('0',))
                self.assertEqual(c.execute('SELECT count(*) FROM pg_prepared_xacts').fetchone(),(0,))
        self.blocked()
        print(BANNER,'real PREPARE TRANSACTION rejected SQLSTATE55000; no prepared transactions; UNKNOWN blocks successor',flush=True)
    def test_quarantine_drains_existing_pool_and_blocks_direct_login(self):
        pool=Pool(self.lab);self.addCleanup(pool.close)
        raw=pool.connect();self.addCleanup(raw.close)
        pid=raw.execute('SELECT pg_backend_pid()').fetchone()[0]
        self.lab.quarantine('A')
        with self.lab.connect() as c:
            self.assertEqual(c.execute("SELECT count(*) FROM pg_stat_activity WHERE usename IN ('cac_ctx_runtime','cac_ctx_issuer')").fetchone(),(0,))
            self.assertEqual(c.execute('SELECT count(*) FROM pg_stat_activity WHERE pid=%s',(pid,)).fetchone(),(0,))
        with self.assertRaises(psycopg.OperationalError):raw.execute('SELECT 1')
        with self.assertRaises(psycopg.OperationalError):self.lab.connect('A','cac_ctx_runtime')
        print(BANNER,'quarantine committed NOLOGIN, observed terminated pooled backend',pid,'and zero role sessions before restore',flush=True)
