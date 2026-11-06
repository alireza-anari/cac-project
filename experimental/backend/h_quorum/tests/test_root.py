"""Q_SURVIVAL_ONLY. Actual consensus and PostgreSQL transport preflight."""
import json
import secrets
import unittest
from pathlib import Path
import subprocess
import tempfile
from uuid import uuid4
import psycopg
from psycopg.conninfo import make_conninfo
from recovery_fencing.lab import Lab
from h_quorum.common import config,BANNER,b64,canonical,Denied
from h_quorum.cluster import Cluster
from h_quorum.etcd import Etcd,unb64
from h_quorum.rpc import Client

class RootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=config();cls.pg=Lab();cls.q=Cluster()
    @classmethod
    def tearDownClass(cls):cls.pg.close()
    def setUp(self):
        self.ns=str(uuid4());self.control=Client(self.cfg,'control',self.ns)
        actors={n:dict(sid=self.pg.cfg[n]['sid'],incarnation=str(uuid4()),manifest='a'*64,admitted=True) for n in ['A','B']}
        self.control.call('genesis',dict(actors=actors))
        self.a=Client(self.cfg,'A_coord',self.ns);self.b=Client(self.cfg,'B_coord',self.ns)
    def test_00_real_five_voters_and_actual_pg_dblink(self):
        evidence=self.q.snapshot('root-preflight')
        self.assertEqual(len(evidence['members']),5)
        self.assertTrue(all(not m['isLearner'] for m in evidence['members'].values()))
        self.assertEqual(len({m['id'] for m in evidence['members'].values()}),5)
        role='A_check'
        conn=make_conninfo(host=self.cfg['gateway_ip'],port=self.cfg['wire_port'],dbname='rcheck',user=role,
            password=self.cfg['roles'][role]['password'],sslmode='verify-full',sslrootcert='/tmp/cac-h-ca.crt',connect_timeout=2)
        request=dict(action='status',namespace=self.ns,args={})
        query="SELECT h_call('"+b64(canonical(request))+"')"
        with self.pg.connect() as c:
            data=c.execute('SELECT r FROM public.dblink(%s,%s) AS response(r text)',(conn,query)).fetchone()[0]
        reply=json.loads(data)
        self.assertEqual(reply['epoch'],0)
        self.assertEqual(reply['namespace'],self.ns)
        self.assertTrue(reply['revision']>0)
        print(BANNER,'REAL PG dblink verified TLS current Q status revision',reply['revision'],flush=True)
    def test_atomic_epoch_and_journal_require_actual_command(self):
        request=str(uuid4())
        receipt=self.a.call('reserve',dict(expected=0,request=request))
        self.assertEqual(receipt.get('epoch'),1,'Real quorum authority command not implemented')
        with self.assertRaises(Denied):self.b.call('reserve',dict(expected=0,request=str(uuid4())))
        snap=self.control.call('inspect',{})
        self.assertEqual(snap['state_revision'],snap['journal_revision'])
        self.assertEqual(snap['seq'],1)
        self.assertTrue(snap['complete'])
        print(BANNER,'ATOMIC state/journal MVCC',snap['state_revision'],'head',snap['head'],flush=True)
    def test_wrong_ca_plaintext_checker_credentials_and_mutating_wire_payload_deny(self):
        role='A_check';base=dict(host=self.cfg['gateway_ip'],port=self.cfg['wire_port'],dbname='rcheck',user=role,password=self.cfg['roles'][role]['password'],sslmode='verify-full',sslrootcert='/tmp/cac-h-ca.crt',connect_timeout=2)
        request=dict(action='status',namespace=self.ns,args={});valid="SELECT h_call('"+b64(canonical(request))+"')"
        def call(settings,query):
            with self.pg.connect() as c:return json.loads(c.execute('SELECT r FROM public.dblink(%s,%s) AS response(r text)',(make_conninfo(**settings),query)).fetchone()[0])
        before=self.control.call('status');self.assertEqual(call(base,valid)['head'],before['head'])
        with tempfile.TemporaryDirectory(prefix='cac-h-untrusted-ca-') as directory:
            ca=Path(directory)/'ca.crt';key=Path(directory)/'private.key';remote='/tmp/cac-h-untrusted-'+str(uuid4())+'.crt'
            subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(ca),'-days','1','-subj','/CN=synthetic-h-untrusted-ca'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=10)
            container=self.pg.cfg['A']['container'];subprocess.run(['docker','cp',str(ca),container+':'+remote],capture_output=True,check=True,timeout=10)
            try:
                cases=[('untrusted CA',dict(base,sslrootcert=remote),valid),('plaintext startup',dict(base,sslmode='disable'),valid),('wrong checker password',dict(base,password='synthetic-wrong-checker-password'),valid),('coordinator role on read-only wire',dict(base,user='A_coord',password=self.cfg['roles']['A_coord']['password']),valid),('SQL parser bypass',base,'SELECT 1'),('mutating RPC on checker wire',base,"SELECT h_call('"+b64(canonical(dict(action='reserve',namespace=self.ns,args=dict(expected=0,request=str(uuid4())))))+"')"),('duplicate JSON keys',base,"SELECT h_call('"+b64('{"action":"status","action":"admit","args":{},"namespace":"'+self.ns+'"}')+"')")]
                for label,settings,query in cases:
                    with self.subTest(label=label):
                        with self.assertRaises(psycopg.Error):call(settings,query)
                        self.assertEqual(call(base,valid)['head'],before['head'])
                        self.assertEqual(self.control.call('status'),before)
                        print(BANNER,'ACTUAL PG dblink TLS/wire negative',label,'denied; paired valid status and authoritative head unchanged',flush=True)
            finally:subprocess.run(['docker','exec',container,'rm','-f',remote],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=10)
