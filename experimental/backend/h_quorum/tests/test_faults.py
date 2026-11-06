"""Q_SURVIVAL_ONLY. Real worker/service/quorum failures retain actual R holds."""
import json
import signal
import subprocess
import sys
import time
import unittest
from uuid import uuid4
import psycopg
from recovery_fencing.lab import S1
from h_quorum.common import BANNER,Denied,config
from h_quorum.integration_lab import IntegrationLab
from h_quorum.broker import Broker
from h_quorum.cluster import Cluster
from h_quorum.etcd import Etcd

class FaultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lab=IntegrationLab()
    @classmethod
    def tearDownClass(cls):cls.lab.close()
    def start(self,successor=True):
        self.lab.reset();a=Broker(self.lab);a.activate(0,str(uuid4()))
        with a.runtime() as g:self.scope(a,g)
        if successor:self.lab.restore()
        return a,Broker(self.lab,'B')
    def scope(self,a,g):g.install(a.issue(g.challenge()));self.assertEqual(g.records(),[S1])
    def test_00_actual_worker_sigkill_cuts_never_clear_unresolved_open(self):
        cases=[('before_open_commit',False,False,False),('after_durable_open',False,True,False),('before_first_use',False,True,False),('after_first_use',False,True,False),('after_final_guard',False,True,False),('before_local_commit',False,True,False),('after_local_commit_before_close',False,True,True),('before_r_close',False,True,True),('after_close_ack',False,False,True),('before_local_abort',True,True,False),('after_local_abort_before_close',True,True,False)]
        for cut,abort,held,committed in cases:
            a,b=self.start()
            result=subprocess.run([sys.executable,'-m','h_quorum.crash_worker'],input=json.dumps(dict(namespace=self.lab.namespace,actors=self.lab.actors,cut=cut,abort=abort)),text=True,capture_output=True,timeout=60)
            self.assertEqual(result.returncode,-signal.SIGKILL,'Worker did not reach requested actual crash')
            self.assertIn('ACTUAL WORKER SIGKILL '+cut,result.stdout)
            print(result.stdout.strip(),flush=True)
            # A real socket/process exit, not an application-raised simulation.
            with self.lab.connect() as observer:
                observer.autocommit=True;deadline=time.monotonic()+5
                while observer.execute("SELECT count(*) FROM pg_stat_activity WHERE usename IN ('cac_ctx_runtime','cac_ctx_issuer')").fetchone()!=(0,):
                    if time.monotonic()>deadline:self.fail('Killed worker backend did not leave actual PG')
                    time.sleep(.02)
                self.assertEqual(observer.execute('SELECT body FROM poc.records WHERE store=%s',(S1,)).fetchone(),('synthetic-crash-commit' if committed else 'synthetic',))
            before=a.inspect();self.assertEqual(before['unknown'],0);self.assertEqual(before['open'],int(held))
            self.lab.restart_service();self.assertEqual(a.inspect(),before,'Root-service restart lost or changed durable unresolved journal')
            if held:
                with self.assertRaises(Denied):b.activate(1,str(uuid4()))
                self.assertFalse(b.ready());self.assertEqual(b.command('status',{})['owner'],'A')
                # Actual PG is positively known idle here, but no orphan clearing
                # is authorized; lack of the worker's exact outcome ACK stays held.
                self.assertEqual(a.inspect()['open'],1)
            else:
                self.lab.restore();b=Broker(self.lab,'B');b.activate(1,str(uuid4()))
                with b.runtime() as g:self.scope(b,g)
            print(BANNER,'CRASH CUT VERIFIED',cut,'abort',abort,'durable hold',held,'actual persisted write',committed,flush=True)
    def test_01_actual_quorum_outage_denies_existing_scoped_sql_and_new_issuance(self):
        a,b=self.start();g=a.runtime();g.__enter__();self.scope(a,g);cluster=Cluster(config())
        try:
            cluster.stop(['r3','r4','r5'])
            self.assertFalse(a.ready())
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):g.records()
            with self.assertRaises(Denied):
                with a.runtime():self.fail('New scope authorized during actual quorum outage')
            with self.assertRaises(Denied):a.issue('synthetic-supplemental-outage')
        finally:
            for name in ('r3','r4','r5'):cluster.start(name)
        # The actual failed transaction has no positive exact pre-error fullxid
        # outcome ACK. Even after availability returns it remains UNKNOWN.
        g.__exit__(psycopg.errors.InsufficientPrivilege,Denied('denied'),None)
        self.assertEqual(a.inspect()['unknown'],1)
        with self.assertRaises(Denied):b.activate(1,str(uuid4()))
        self.assertFalse(b.ready())
    def test_02_live_open_survives_actual_minority_learner_replacement(self):
        a,b=self.start();cluster=Cluster(config());before=cluster.snapshot('live-open-before-replacement')
        with a.runtime() as g:
            self.scope(a,g);held=a.inspect()
            for name in ('r4','r5'):
                fresh=cluster.replace(name);phase=cluster.snapshot('live-open-learner-'+name)
                self.assertTrue(phase['members'][name]['isLearner']);self.assertNotEqual(fresh,before['members'][name]['id'])
                for survivor in ('r1','r2','r3'):self.assertEqual(phase['members'][survivor]['id'],before['members'][survivor]['id'])
                client=Etcd(cluster.cfg);voter=cluster.cfg['members']['r1']['endpoint'];learner=cluster.cfg['members'][name]['endpoint'];client._authenticate(voter)
                prefix='/cac-h/'+self.lab.namespace+'/';revision=held['state_revision']
                actual=client.range(prefix+'journal/',prefix=True,revision=revision,endpoint=voter)
                deadline=time.monotonic()+20
                while True:
                    try:local=client.range(prefix+'journal/',prefix=True,revision=revision,serializable=True,endpoint=learner)
                    except Denied:
                        if time.monotonic()>deadline:self.fail('Learner current revision/authentication not caught up')
                        client._authenticate(voter)
                        time.sleep(.1);continue
                    same=[(r['key'],r['value'],r['mod_revision']) for r in local.get('kvs',[])]==[(r['key'],r['value'],r['mod_revision']) for r in actual['kvs']]
                    if same:break
                    if time.monotonic()>deadline:self.fail('Current OPEN journal did not catch up in quarantined learner')
                    time.sleep(.1)
                self.assertTrue(same,'Learner current OPEN journal differs (private values not logged)')
                self.assertEqual(str(local['header']['member_id']),fresh)
                self.assertEqual(str(local['header']['cluster_id']),str(cluster.cfg['cluster_id']))
                self.assertEqual(a.inspect(),held)
                cluster.promote(name);after=cluster.snapshot('live-open-promoted-'+name)
                self.assertEqual(len(after['members']),5);self.assertTrue(all(not m['isLearner'] for m in after['members'].values()))
                self.assertEqual(g.records(),[S1])
                print(BANNER,'ACTUAL LIVE OPEN LEARNER JOURNAL',json.dumps(dict(phase=phase,promoted=after,revision=revision,head=held['head']),sort_keys=True),flush=True)
        self.assertEqual(a.inspect()['open'],0)
