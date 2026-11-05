"""Trusted synthetic coordinator. No admin/MAC key is required by this class."""
import json
from pathlib import Path
import psycopg
from psycopg.types.json import Jsonb
from recovery_fencing.lab import P1,S1

class FenceDenied(Exception):pass

class Broker:
    def __init__(self,lab=None,node='A',cfg=None,hook=None):
        if cfg is None:
            n=lab.cfg[node]
            cfg=dict(connection=n['connection'],passwords={r:n['passwords'][r] for r in ['cac_ctx_runtime','cac_ctx_issuer','cac_fence_activator']},
                     anchor_connection=lab.cfg['C']['connection'],anchor_role=n['anchor_role'],anchor_password=n['anchor_password'],
                     anchor_sid=lab.cfg['C']['sid'],instance=n['instance'],proof=lab.cfg['A']['poc_proofs'][0])
        self.cfg=cfg;self.instance=cfg['instance'];self.hook=hook or (lambda stage:None)
    def local(self,role):
        return psycopg.connect(**self.cfg['connection'],user=role,password=self.cfg['passwords'][role],connect_timeout=2,prepare_threshold=None,options='-c statement_timeout=2500 -c lock_timeout=700')
    def anchor(self):
        c=psycopg.connect(**self.cfg['anchor_connection'],user=self.cfg['anchor_role'],password=self.cfg['anchor_password'],connect_timeout=2,prepare_threshold=None,options='-c statement_timeout=2500 -c lock_timeout=700')
        try:
            if c.execute('SELECT anchor.status()').fetchone()[0]['anchor_sid']!=self.cfg['anchor_sid']:raise FenceDenied('denied')
            return c
        except BaseException:c.close();raise
    def ready(self):
        try:
            with self.local('cac_ctx_runtime') as c:return c.execute('SELECT fence.is_ready()').fetchone()[0] is True
        except psycopg.Error:return False
    def status(self):
        try:
            with self.anchor() as c:return c.execute('SELECT anchor.status()').fetchone()[0]
        except psycopg.Error:raise FenceDenied('denied') from None
    def reserve(self,expected,request):
        try:
            with self.anchor() as c:return c.execute('SELECT anchor.reserve(%s,%s)',(expected,request)).fetchone()[0]
        except psycopg.Error:raise FenceDenied('denied') from None
    def activate(self,expected,request):
        try:
            self.hook('before_reserve')
            receipt=self.reserve(expected,request);self.hook('after_reserve')
            with self.local('cac_fence_activator') as c:
                c.execute('SELECT fence.apply(%s,%s,%s)',(receipt['epoch'],receipt['generation'],receipt['request']))
            self.hook('after_apply')
            with self.local('cac_fence_activator') as c:
                ack=c.execute('SELECT fence.ack(%s,%s)',(receipt['epoch'],receipt['request'])).fetchone()[0]
            with self.anchor() as c:c.execute('SELECT anchor.confirm(%s)',(ack,))
            self.hook('after_confirm')
            with self.local('cac_fence_activator') as c:c.execute('SELECT fence.mark_ready()')
            self.hook('after_ready')
            if not self.ready():raise FenceDenied('denied')
            return receipt
        except psycopg.Error:raise FenceDenied('denied') from None
    def runtime(self):return Gate(self,'cac_ctx_runtime')
    def issue(self,h,store=S1):
        try:
            with Gate(self,'cac_ctx_issuer') as g:
                token=g.c.execute('SELECT poc.issue(%s,%s,%s,%s,%s,%s)',(h,self.cfg['proof'],store,'read',P1,Jsonb({}))).fetchone()[0]
            return token # only after both local commit and independent postcheck/close
        except psycopg.Error:raise FenceDenied('denied') from None

class Gate:
    def __init__(self,broker,role):self.broker=broker;self.role=role;self.c=None;self.a=None;self.held=False;self.ticket=None
    def __enter__(self):
        try:
            if not self.broker.ready():raise FenceDenied('denied')
            self.c=self.broker.local(self.role)
            self.pid,self.tx,self.sid=self.c.execute('SELECT pg_backend_pid(),txid_current()::text,fence.system_id()').fetchone()
            self.a=self.broker.anchor()
            self.ticket=self.a.execute('SELECT anchor.prepare(%s,%s,%s)',(self.pid,self.tx,self.sid)).fetchone()[0]
            self.a.commit() # durable OPEN intent must precede any local authorization
            self.a.execute('SELECT anchor.hold(%s)',(self.ticket,));self.held=True
            self.c.execute("SELECT set_config('cac.fence_ticket',%s,true)",(self.ticket,))
            return self
        except (psycopg.Error,FenceDenied):
            # If holding failed, keep the durable OPEN intent unresolved. Availability
            # loss is safer than guessing whether an old local operation can finish.
            if self.c:
                try:self.c.rollback()
                except psycopg.Error:pass
                self.c.close()
            if self.a:
                if self.held:
                    try:self.a.execute('SELECT anchor.finish(%s)',(self.ticket,));self.a.commit()
                    except psycopg.Error:pass
                self.a.close()
            raise FenceDenied('denied') from None
    def __exit__(self,exc_type,exc,tb):
        try:
            if exc_type is None:
                if self.role=='cac_ctx_issuer':self.broker.hook('before_issue_commit')
                self.c.commit()
                if self.role=='cac_ctx_issuer':self.broker.hook('after_issue_commit')
            else:self.c.rollback()
            # finish validates the still-live exclusive ticket + owner while the
            # singleton SHARE lock remains held. Ambiguity leaves OPEN durable.
            self.a.execute('SELECT anchor.finish(%s)',(self.ticket,));self.a.commit()
        except psycopg.Error:raise FenceDenied('denied') from None
        finally:
            self.c.close();self.a.close()
        return False
    def challenge(self):return self.c.execute('SELECT poc.challenge()').fetchone()[0]
    def install(self,t):self.c.execute("SELECT set_config('cac.poc_context',%s,true)",(t,))
    def records(self):return [str(r[0]) for r in self.c.execute('SELECT store FROM poc.records')]
