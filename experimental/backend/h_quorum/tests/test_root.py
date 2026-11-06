"""Q_SURVIVAL_ONLY. Actual consensus and PostgreSQL transport preflight."""
import json
import secrets
import unittest
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
