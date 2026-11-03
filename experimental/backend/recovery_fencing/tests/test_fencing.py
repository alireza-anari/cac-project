import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from uuid import uuid4
import psycopg
from recovery_fencing.lab import Lab,P1,S1,S2
from recovery_fencing.broker import Broker,FenceDenied

class FencingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lab=Lab();cls.lab.install_roles()
    @classmethod
    def tearDownClass(cls):cls.lab.close()
    def setUp(self):self.lab.reset();self.a=Broker(self.lab,'A');self.b=Broker(self.lab,'B')
    def activate_a(self):return self.a.activate(0,str(uuid4()))
    def restore_b(self):self.lab.restore();self.lab.bind('B')
    def positive(self,broker,store=S1):
        with broker.runtime() as s:
            h=s.challenge();t=broker.issue(h,store=store);s.install(t)
            self.assertEqual(s.records(),[store]);return h,t
    def test_three_independent_clusters_and_no_ready_before_activation(self):
        self.assertEqual(len({x['sid'] for x in self.lab.cfg.values()}),3)
        self.assertFalse(self.a.ready())
        with self.assertRaises(FenceDenied):self.positive(self.a)
        self.assertEqual(self.activate_a()['epoch'],1);self.positive(self.a)

    def test_restored_ready_and_ledger_do_not_authorize(self):
        self.activate_a();h,t=self.positive(self.a)
        self.lab.restore() # deliberately leave copied A identity/ready in B
        self.assertFalse(self.b.ready())
        with self.lab.connect('B','cac_ctx_issuer') as c:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                from psycopg.types.json import Jsonb
                c.execute('SELECT poc.issue(%s,%s,%s,%s,%s,%s)',(h,self.lab.cfg['A']['poc_proofs'][0],S1,'read',P1,Jsonb({})))
        with self.lab.connect('B') as c:self.assertEqual(c.execute('SELECT count(*) FROM poc_private.ledger').fetchone(),(1,))

    def test_takeover_fences_old_alive_primary(self):
        self.activate_a();self.positive(self.a);self.restore_b()
        receipt=self.b.activate(1,str(uuid4()));self.assertEqual(receipt['epoch'],2)
        self.assertFalse(self.a.ready());self.assertTrue(self.b.ready())
        with self.assertRaises(FenceDenied):self.positive(self.a)
        self.positive(self.b,store=S2)
        with self.lab.connect('C') as c:self.assertEqual(c.execute('SELECT epoch,phase,owner::text FROM anchor.state').fetchone(),(2,'active',self.b.instance))

    def test_concurrent_reservation_cas_has_one_winner(self):
        self.activate_a();self.restore_b()
        def attempt(b):
            try:return b,b.reserve(1,str(uuid4()))
            except FenceDenied:return b,None
        with concurrent.futures.ThreadPoolExecutor(2) as pool:r=list(pool.map(attempt,[self.a,self.b]))
        self.assertEqual(sum(v is not None for _,v in r),1)
        winner,receipt=next((b,v) for b,v in r if v is not None)
        self.assertEqual(receipt['epoch'],2)
        self.assertFalse(self.a.ready());self.assertFalse(self.b.ready())
        winner.activate(1,receipt['request']);self.positive(winner)

    def test_duplicate_activation_and_old_request_never_resurrect(self):
        req=str(uuid4());r=self.a.activate(0,req)
        self.assertEqual(self.a.activate(0,req)['epoch'],1)
        self.restore_b();self.b.activate(1,str(uuid4()))
        with self.assertRaises(FenceDenied):self.a.activate(2,req)
        self.assertEqual(self.b.status()['epoch'],2);self.assertEqual(r['epoch'],1)

    def test_apply_ack_requires_independently_committed_state(self):
        r=self.a.reserve(0,str(uuid4()))
        with self.a.local('cac_fence_activator') as c:
            c.execute('SELECT fence.apply(%s,%s,%s)',(r['epoch'],r['generation'],r['request']))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute('SELECT fence.ack(%s,%s)',(r['epoch'],r['request']))
            c.rollback()
        self.assertEqual(self.a.status()['phase'],'reserved');self.assertFalse(self.a.ready())
        self.a.activate(0,r['request']);self.positive(self.a)

    def test_direct_sql_and_ticket_replay_denied(self):
        self.activate_a()
        for q in ['SELECT poc.challenge()',"SELECT * FROM fence_private.config",'SET ROLE cac_ctx_guard','SET ROLE cac_fence_activator',"SELECT poc_private.challenge_unfenced()"]:
            with self.subTest(q=q),self.lab.connect('A','cac_ctx_runtime') as c:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute(q).fetchall()
        with self.a.runtime() as s:
            with self.lab.connect('A','cac_ctx_runtime') as other:
                other.execute("SELECT set_config('cac.fence_ticket',%s,true)",(s.ticket,))
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):other.execute('SELECT poc.challenge()')
        with self.lab.connect('A','cac_ctx_runtime') as c:
            c.execute("SELECT set_config('cac.fence_ticket',%s,true)",(s.ticket,))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute('SELECT poc.challenge()')

    def test_long_transaction_blocks_takeover_then_old_connection_denied(self):
        self.activate_a();self.restore_b()
        with self.a.runtime() as s:
            self.assertTrue(s.challenge())
            with self.assertRaises(FenceDenied):self.b.reserve(1,str(uuid4()))
            self.assertEqual(self.a.status()['epoch'],1)
        self.b.activate(1,str(uuid4()))
        with self.assertRaises(FenceDenied):
            with self.a.runtime():pass
        self.positive(self.b)

    def test_savepoint_and_rollback_do_not_undo_external_fence(self):
        self.activate_a()
        with self.a.runtime() as s:
            h=s.challenge();t=self.a.issue(h);s.c.execute('SAVEPOINT before_context');s.install(t)
            self.assertEqual(s.records(),[S1]);s.c.execute('ROLLBACK TO SAVEPOINT before_context')
            with self.assertRaises(FenceDenied):self.a.issue(h,store=S2)
            s.install(t);self.assertEqual(s.records(),[S1])
        with self.lab.connect('C') as c:self.assertEqual(c.execute("SELECT count(*) FROM anchor.operations WHERE phase='open'").fetchone(),(0,))

    def test_anchor_outage_denies_and_restart_preserves_epoch(self):
        self.activate_a();container=self.lab.cfg['C']['container']
        self.lab.docker('stop','--time','1',container)
        try:
            self.assertFalse(self.a.ready())
            with self.lab.connect('A','cac_ctx_runtime') as raw:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):raw.execute('SELECT poc.challenge()')
            with self.assertRaises(FenceDenied):self.positive(self.a)
            with self.assertRaises(FenceDenied):self.b.reserve(1,str(uuid4()))
        finally:self.lab.docker('start',container);self.lab.wait('C')
        self.assertEqual(self.a.status()['epoch'],1);self.positive(self.a)

    def test_wrong_anchor_identity_fails_closed(self):
        self.activate_a()
        with self.lab.connect() as c:c.execute("UPDATE fence_private.config SET anchor_sid='0'")
        self.assertFalse(self.a.ready())
        with self.assertRaises(FenceDenied):self.positive(self.a)

    def test_stale_signed_response_nonce_replay_denied(self):
        self.activate_a()
        with self.a.anchor() as c:
            proof=c.execute("SELECT anchor.attest(%s,'active','',%s,0,'0')",('0'*64,self.lab.cfg['A']['sid'])).fetchone()[0]
        with self.lab.mutate_anchor_return(proof):
            self.assertFalse(self.a.ready())
            with self.assertRaises(FenceDenied):self.positive(self.a)
        self.positive(self.a)

    def test_missing_bootstrap_and_wrong_acl_never_ready(self):
        self.activate_a();self.restore_b()
        with self.lab.connect('B') as c:c.execute('REVOKE EXECUTE ON FUNCTION pg_control_system() FROM cac_ctx_guard')
        with self.assertRaises(FenceDenied):self.b.activate(1,str(uuid4()))
        self.assertFalse(self.b.ready());self.assertFalse(self.a.ready())
        with self.lab.connect('B') as c:c.execute('GRANT EXECUTE ON FUNCTION pg_control_system() TO cac_ctx_guard')
        status=self.b.status();self.b.activate(1,status['request']);self.positive(self.b)
        with self.lab.connect('B') as c:c.execute('GRANT EXECUTE ON FUNCTION poc_private.issue_unfenced(text,text,uuid,text,uuid,jsonb) TO cac_ctx_issuer')
        self.assertFalse(self.b.ready())

    def test_bad_loopback_reader_prevents_confirmation(self):
        self.activate_a();self.restore_b()
        with self.lab.connect('B') as c:c.execute("UPDATE fence_private.config SET ack_conn=ack_conn||' password=incorrect'")
        with self.assertRaises(FenceDenied):self.b.activate(1,str(uuid4()))
        self.assertEqual(self.b.status()['phase'],'reserved');self.assertFalse(self.b.ready());self.assertFalse(self.a.ready())

    def test_activation_process_crash_matrix_and_retry(self):
        for stage in ['before_reserve','after_reserve','after_apply','after_confirm','after_ready']:
            with self.subTest(stage=stage):
                self.lab.reset();self.a=Broker(self.lab,'A');req=str(uuid4())
                result=self.lab.crash_worker('A',stage,request=req)
                self.assertEqual(result.returncode,91)
                state=self.a.status()
                self.assertEqual(state['epoch'],0 if stage=='before_reserve' else 1)
                self.assertEqual(self.a.ready(),stage=='after_ready')
                self.a.activate(0,req);self.positive(self.a)
                self.assertEqual(self.a.status()['epoch'],1)
                print('CRASH MATRIX',stage,'safe durable phase',state['phase'],flush=True)

    def test_issuance_process_crashes_leave_durable_unresolved_intent(self):
        for stage,count in [('before_issue_commit',0),('after_issue_commit',1)]:
            with self.subTest(stage=stage):
                self.lab.reset();self.a=Broker(self.lab,'A');self.activate_a();self.restore_b()
                r=self.lab.crash_worker('A',stage,operation='issue')
                self.assertEqual(r.returncode,91)
                self.lab.wait_local_quiet('A')
                with self.lab.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM poc_private.ledger').fetchone(),(count,))
                with self.lab.connect('C') as c:self.assertGreater(c.execute("SELECT count(*) FROM anchor.operations WHERE phase='open'").fetchone()[0],0)
                with self.assertRaises(FenceDenied):self.b.activate(1,str(uuid4()))
                self.assertFalse(self.a.ready());self.assertFalse(self.b.ready())
                print('ISSUE CRASH',stage,'ledger',count,'takeover blocked by durable OPEN',flush=True)

    def test_anchor_crash_after_attestation_blocks_new_owner(self):
        self.activate_a();self.restore_b()
        p=self.lab.paused_worker('A')
        try:
            self.assertEqual(json.loads(p.stdout.readline())['phase'],'after_local_body')
            self.lab.docker('kill','--signal','KILL',self.lab.cfg['C']['container'])
            self.lab.docker('start',self.lab.cfg['C']['container']);self.lab.wait('C')
            with self.assertRaises(FenceDenied):self.b.activate(1,str(uuid4()))
            p.stdin.write('resume\n');p.stdin.flush();self.assertEqual(p.wait(timeout=8),2)
            self.assertEqual(self.a.status()['epoch'],1)
            self.assertFalse(self.a.ready());self.assertFalse(self.b.ready())
            print('ANCHOR CRASH WITNESS durable intent prevents takeover after live lock loss',flush=True)
        finally:
            if p.poll() is None:p.kill();p.wait()
            p.stdin.close();p.stdout.close()

    def test_old_primary_restart_and_local_generation_rollback_cannot_revive(self):
        first=self.activate_a();self.positive(self.a);self.restore_b();self.b.activate(1,str(uuid4()))
        self.lab.docker('restart','--time','1',self.lab.cfg['A']['container']);self.lab.wait('A')
        with self.lab.connect() as c:
            c.execute('UPDATE poc_private.config SET generation=%s',(first['generation'],))
            c.execute('UPDATE fence_private.state SET ready=true,epoch=1,generation=%s,request=%s',(first['generation'],first['request']))
        self.assertFalse(self.a.ready())
        with self.assertRaises(FenceDenied):self.positive(self.a)
        self.positive(self.b)

    def test_durable_epoch_survives_anchor_crash_and_stale_cas(self):
        self.activate_a();self.positive(self.a)
        self.lab.docker('kill','--signal','KILL',self.lab.cfg['C']['container'])
        self.lab.docker('start',self.lab.cfg['C']['container']);self.lab.wait('C')
        self.assertEqual(self.a.status()['epoch'],1)
        with self.assertRaises(FenceDenied):self.b.reserve(0,str(uuid4()))
        self.positive(self.a)
