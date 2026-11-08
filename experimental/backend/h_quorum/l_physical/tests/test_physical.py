"""Literal stopped native bytes, actual current quorum and protected SQL only."""
import importlib.util
import copy
import os
import signal
import unittest
from uuid import uuid4
import psycopg
from h_quorum.authority import Root
from h_quorum.broker import Broker
from h_quorum.common import BANNER, Denied
from h_quorum.etcd import Etcd
from h_quorum.integration_lab import IntegrationLab
from h_quorum.retirement import adopt_policy
from h_quorum.rpc import Client
from recovery_fencing.lab import S1


class PhysicalTests(unittest.TestCase):
    def setUp(self):
        self.lab = IntegrationLab(); self.addCleanup(self.lab.close)
        self.lab.reset(); self.a = Broker(self.lab); self.a.activate(0, str(uuid4()))
        self.scope()

    def scope(self):
        with self.a.runtime() as gate:
            gate.install(self.a.issue(gate.challenge())); self.assertEqual(gate.records(), [S1])
            print(BANNER, 'L ACTUAL HEALTHY SCOPED SQL', gate.pid, gate.tx, gate.sid, flush=True)

    def physical(self):
        self.assertIsNotNone(importlib.util.find_spec('h_quorum.l_physical.fixture'),
                             'Literal native Raft archive/reimport fixture is not implemented')
        from h_quorum.l_physical.fixture import Physical
        fixture = Physical(self.lab); self.addCleanup(fixture.close)
        fixture.archive_current()
        return fixture

    def retire(self):
        result = Client(self.lab.rootcfg, 'control', self.lab.namespace).call(
            'retire_policy', dict(expected=1, new=2, request=str(uuid4())))
        self.lab.replay()
        self.assertEqual(result['policy'], 2)
        return result

    def current2(self):
        adopt_policy(self.lab,self.a.node)
        self.assertTrue(self.a.ready())
        self.scope()

    def state(self): return Root(self.lab.rootcfg).read(self.lab.namespace)

    def test_00_literal_native_archive_restart(self):
        from recovery_proof.pool_lab import Pool
        pool = Pool(self.lab); self.addCleanup(pool.close); self.a.pool = pool
        with self.a.runtime() as gate:
            token = self.a.issue(gate.challenge()); gate.install(token)
            self.assertEqual(gate.records(), [S1]); pid, tx = gate.pid, gate.tx
            for name, value in [('cac.poc_context',token),('cac.h_ticket',gate.ticket),('cac.h_intent',gate.binding['digest'])]:
                gate.c.execute('SELECT set_config(%s,%s,false)',(name,value))
        physical = self.physical()
        old_state, old_revision, old_header = physical.old_response
        self.assertEqual(old_state['policy'], 1)
        self.assertEqual(str(old_header['member_id']), physical.original['id'])
        # An actual unavailable minority endpoint is not evidence of local abort.
        reader = Etcd(physical.q.cfg); reader._authenticate(physical.q.cfg['members']['r1']['endpoint'])
        with self.assertRaises(Denied):
            reader.range('/cac-h/'+self.lab.namespace+'/state', endpoint=physical.original['endpoint'])
        self.retire(); authoritative = self.state()
        self.assertGreater(authoritative[1], old_revision)
        self.assertFalse(self.a.ready(), 'Unavailable stale minority revived old SQL readiness')
        with self.assertRaises(Denied):
            with self.a.runtime(): self.fail('Unavailable minority allowed old policy gate')
        receipt = physical.replay()
        self.assertEqual(receipt['policy'], 2); self.assertNotEqual(receipt['head'], old_state['head'])
        self.assertEqual(self.state(), authoritative)
        self.assertFalse(self.a.ready(), 'Replayed native minority revived old policy SQL readiness')
        with self.lab.connect('A','cac_ctx_issuer') as issuer:
            self.assertEqual(issuer.execute('SELECT fence.is_ready()').fetchone(), (False,))
        with self.assertRaises(Denied):
            with self.a.runtime(): self.fail('Old policy reached a protected gate after native replay')
        self.current2()
        with self.a.runtime() as current:
            self.assertEqual(current.binding['policy'], 2)
            with self.assertRaises(Denied):
                self.a.command('admit',dict(current.binding,policy=1,request=str(uuid4()),operation=str(uuid4())))
        with pool.connect() as connection:
            fresh_pid, fresh_tx = connection.execute('SELECT pg_backend_pid(),txid_current()::text').fetchone()
            self.assertEqual(fresh_pid,pid); self.assertNotEqual(fresh_tx,tx)
            self.assertEqual(connection.execute("SELECT current_setting('cac.poc_context',true)").fetchone()[0], token)
            with self.assertRaises(psycopg.errors.InsufficientPrivilege): connection.execute('SELECT store FROM poc.records')
            connection.rollback()
        self.scope()
        print(BANNER, 'L PHYSICAL POLICY2 + POOL NEGATIVE/POSITIVE', 'PID',pid,'old xid',tx,'new xid',fresh_tx,
              'retained authentic old minority response',old_revision,old_state['head'],
              'unavailable minority read denied; native catchup is not old authorization',flush=True)

    def test_01_pregranted_commit_hold_survives_literal_replay(self):
        self.lab.restore(); successor=Broker(self.lab,'B')
        physical = self.physical(); body={'body':'synthetic-l-old-grant-commit'}
        with self.a.runtime(action='probe',body=body) as gate:
            gate.install(self.a.issue(gate.challenge(),action='probe',body=body))
            self.assertEqual(gate.records(),[S1])
            gate.c.execute('UPDATE poc.records SET body=%s WHERE store=%s',(body['body'],S1))
            self.retire(); before=self.state()
            physical.replay(); self.assertEqual(self.state(),before)
            with self.assertRaises(Denied): adopt_policy(self.lab)
            with self.assertRaises(Denied): successor.activate(1,str(uuid4()))
            self.assertEqual(gate.records(),[S1])
            def hook(label):
                if label=='after_local_commit_before_close':
                    self.assertEqual(self.a.inspect()['open'],1)
                    with self.assertRaises(Denied): successor.activate(1,str(uuid4()))
            self.a.hook=hook
        self.a.hook=lambda _:None
        self.assertEqual(self.state()[0]['ops'][gate.operation]['phase'],'CLOSED_COMMIT')
        self.lab.restore(); self.a=Broker(self.lab,'B'); self.a.activate(1,str(uuid4()))
        self.current2()
        with self.lab.connect('B') as connection:
            self.assertEqual(connection.execute('SELECT body FROM poc.records WHERE store=%s',(S1,)).fetchone(),(body['body'],))
        print(BANNER,'L native older Raft omitted live grant; current complete OPEN retained through real COMMIT; known CLOSE only',flush=True)

    def test_02_unknown_never_cleared_by_native_repair(self):
        self.lab.restore(); successor=Broker(self.lab,'B')
        physical=self.physical()
        def hook(label):
            if label=='after_durable_open': self.retire()
        self.a.hook=hook; gate=self.a.runtime()
        with self.assertRaises(Denied):
            with gate: self.fail('Retired ungranted operation reached protected SQL')
        self.a.hook=lambda _:None
        before=self.state(); self.assertEqual(self.a.inspect()['unknown'],1)
        physical.replay(); self.assertEqual(self.state(),before)
        with self.assertRaises(Denied): adopt_policy(self.lab)
        with self.assertRaises(Denied): self.a.command('close',dict(gate.binding,ticket=gate.ticket,outcome='abort'))
        with self.assertRaises(Denied): successor.activate(1,str(uuid4()))
        self.assertEqual(self.a.inspect()['unknown'],1)
        print(BANNER,'L genuine UNKNOWN retained after native catchup; no inferred abort/timeout/reconciliation',flush=True)

    def test_03_removed_member_original_native_bytes_refused(self):
        physical=self.physical(); self.retire(); before=self.state()
        result=physical.incompatible_attempt(learner_identity=False)
        self.assertNotEqual(result['old_id'],result['expected_learner_id'])
        self.assertEqual(self.state(),before)
        self.current2()

    def test_04_new_learner_config_with_old_native_bytes_refused(self):
        physical=self.physical(); self.retire(); before=self.state()
        result=physical.incompatible_attempt(learner_identity=True)
        self.assertNotEqual(result['old_id'],result['expected_learner_id'])
        self.assertEqual(self.state(),before)
        self.current2()

    def test_05_physical_replay_cannot_authorize_retirement_coordinator(self):
        physical=self.physical()
        # Real epoch advance while retaining policy1, so unauthorized policy1→2
        # is eligible except for the exact control-role check being tested.
        self.a.activate(1,str(uuid4())); before=self.state()
        physical.replay(); self.assertEqual(self.state(),before)
        self.assertEqual(before[0]['policy'],1); self.assertEqual(before[0]['epoch'],2)
        with self.assertRaises(Denied,msg='Physical replay accepted non-control policy retirement'):
            Client(self.lab.rootcfg,'A_coord',self.lab.namespace).call(
                'retire_policy',dict(expected=1,new=2,request=str(uuid4())))
            self.assertEqual(self.state()[0]['policy'],2)
            print(BANNER,'UNSAFE L PHYSICAL AUTHORITY WITNESS native import completed then coordinator committed policy2',flush=True)
        self.assertEqual(self.state(),before)
        self.retire(); self.current2()

    def test_06_forced_nonchild_stop_proved_before_native_reimport(self):
        from h_quorum.cluster import Cluster
        physical=self.physical()
        child,_=physical.spawn(); physical.caught_up()
        record=copy.deepcopy(physical.q.cfg['members']['r4'])
        os.kill(record['pid'],signal.SIGSTOP) # real unresponsive minority, quorum stays current
        physical.q=Cluster() # emulate bootstrap-owned PID: deliberately no Popen child handle
        self.assertFalse(physical.q.children)
        physical.stop()
        self.assertFalse(physical.q._owned(record), 'Old executable still running before byte replacement')
        self.assertEqual(child.wait(timeout=5),-signal.SIGKILL)
        self.retire(); physical.replay(); self.current2()
        print(BANNER,'L ACTUAL SIGSTOP -> nonchild SIGKILL termination witnessed before byte replay; no concurrent same-ID',flush=True)
