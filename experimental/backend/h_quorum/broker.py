"""Q_SURVIVAL_ONLY. Owned PG transaction observer; unknown never releases R hold."""
from uuid import uuid4
import psycopg
from psycopg.types.json import Jsonb
from recovery_fencing.broker import Broker as CBroker,FenceDenied
from recovery_fencing.lab import P1,S1
from h_quorum.common import Denied
from h_quorum.rpc import Client

class Broker(CBroker):
    def __init__(self,lab,node='A',pool=None,hook=None):
        super().__init__(lab.parent,node,hook=hook);self.lab=lab;self.node=node;self.pool=pool
        self.root=Client(lab.rootcfg,node+'_coord',lab.namespace)
    def command(self,action,args):return self.root.call(action,args)
    def inspect(self):return Client(self.lab.rootcfg,'control',self.lab.namespace).call('inspect')
    def _direct(self,role):
        c=super().local(role)
        try:c.execute("SET LOCAL statement_timeout='30000ms'");return c
        except BaseException:c.close();raise
    def local(self,role):
        if not self.pool or role!='cac_ctx_runtime':return self._direct(role)
        c=self.pool.connect()
        try:c.execute("SET LOCAL statement_timeout='30000ms'");return c
        except BaseException:c.close();raise
    def ready(self):
        try:
            with self._direct('cac_ctx_runtime') as c:return c.execute('SELECT fence.is_ready()').fetchone()[0] is True
        except psycopg.Error:return False
    def activate(self,expected,request):
        try:
            receipt=self.command('reserve',dict(expected=expected,request=request));self.hook('after_r_reserve')
            # Legacy C is a generation cache, not the operation-hold authority.
            current=self.status()['epoch'];cache=self.reserve(current,request)
            with self._direct('cac_fence_activator') as c:c.execute('SELECT fence.apply(%s,%s,%s)',(cache['epoch'],cache['generation'],cache['request']))
            with self._direct('cac_fence_activator') as c:ack=c.execute('SELECT fence.ack(%s,%s)',(cache['epoch'],cache['request'])).fetchone()[0]
            with self.anchor() as c:c.execute('SELECT anchor.confirm(%s)',(ack,))
            with self._direct('cac_fence_activator') as c:
                c.execute('SELECT fence.mark_ready()');c.execute('SELECT h_guard.set_epoch(%s)',(receipt['epoch'],))
            self.hook('before_r_active');self.command('activate',dict(request=request))
            if not self.ready():raise Denied('denied')
            return receipt
        except (psycopg.Error,FenceDenied):raise Denied('denied') from None
    def runtime(self,store=S1,action='read',target=P1,body=None):return Gate(self,'cac_ctx_runtime',store=store,action=action,target=target,body={} if body is None else body)
    def issue(self,h,store=S1,action='read',target=P1,body=None):
        args=[h,self.cfg['proof'],store,action,target,Jsonb({} if body is None else body)]
        with Gate(self,'cac_ctx_issuer',args=args) as g:token=g.c.execute('SELECT poc.issue(%s,%s,%s,%s,%s,%s)',args).fetchone()[0]
        return token

class Gate:
    def __init__(self,broker,role,store=None,action=None,target=None,body=None,args=None):
        self.broker=broker;self.role=role;self.store=store;self.action=action;self.target=target;self.body=body;self.args=args
        self.c=None;self.ticket=None;self.binding=None;self.operation=str(uuid4());self.request=str(uuid4())
    def __enter__(self):
        try:
            if not self.broker.ready():raise Denied('denied')
            self.c=self.broker.local(self.role)
            self.pid,self.tx,self.sid=self.c.execute('SELECT pg_backend_pid(),txid_current()::text,fence.system_id()').fetchone()
            if self.role=='cac_ctx_runtime':intent=self.c.execute('SELECT h_guard.runtime_digest(%s,%s,%s,h_guard.body_digest(%s))',(self.store,self.action,self.target,Jsonb(self.body))).fetchone()[0]
            else:intent=self.c.execute('SELECT h_guard.issuer_digest(%s,%s,%s,%s,%s,%s)',self.args).fetchone()[0]
            actor=self.broker.lab.actors[self.broker.node]
            self.binding=dict(sid=self.sid,pid=self.pid,tx=self.tx,kind='runtime' if self.role=='cac_ctx_runtime' else 'issuer',login=self.role,digest=intent,incarnation=actor['incarnation'],manifest=actor['manifest'],policy=1)
            self.broker.hook('before_open_commit')
            receipt=self.broker.command('admit',dict(self.binding,request=self.request,operation=self.operation))
            self.ticket=receipt['ticket'];self.broker.hook('after_durable_open')
            self.broker.hook('before_first_use');self.broker.command('first_use',dict(self.binding,ticket=self.ticket))
            self.broker.hook('after_first_use')
            self.c.execute("SELECT set_config('cac.h_ticket',%s,true)",(self.ticket,));self.c.execute("SELECT set_config('cac.h_intent',%s,true)",(intent,))
            self.c.execute('SELECT h_guard.final_check()')
            return self
        except BaseException as error:
            if self.c:
                try:self.c.rollback()
                except psycopg.Error:pass
            self._unknown();self._close()
            if isinstance(error,AssertionError):raise
            raise Denied('denied') from None
    def _close(self):
        if self.c:self.c.close()
    def _unknown(self):
        if self.ticket and self.binding:
            try:self.broker.command('unknown',dict(self.binding,ticket=self.ticket))
            except Denied:pass # Durable OPEN remains an exclusion even without UNKNOWN ACK.
    def __exit__(self,exc_type,exc,tb):
        try:
            status=self.c.info.transaction_status
            if exc_type is not None and status==psycopg.pq.TransactionStatus.INERROR:
                self.c.rollback();self._unknown();return False
            if status!=psycopg.pq.TransactionStatus.INTRANS:raise Denied('Unexpected local outcome')
            actual=self.c.execute('SELECT pg_backend_pid(),txid_current()::text,fence.system_id()').fetchone()
            if actual!=(self.pid,self.tx,self.sid):raise Denied('Local transaction changed')
            if exc_type is None:
                self.c.execute('SELECT h_guard.final_check()');self.broker.hook('after_final_guard')
                self.broker.hook('before_local_commit');self.c.commit();outcome='commit';self.broker.hook('after_local_commit_before_close')
            else:
                self.broker.hook('before_local_abort');self.c.rollback();outcome='abort';self.broker.hook('after_local_abort_before_close')
            if self.c.info.transaction_status!=psycopg.pq.TransactionStatus.IDLE:raise Denied('Missing exact local ACK')
            self.broker.hook('before_r_close');self.broker.command('close',dict(self.binding,ticket=self.ticket,outcome=outcome));self.broker.hook('after_close_ack')
        except BaseException as error:
            self._unknown()
            if isinstance(error,AssertionError):raise
            raise Denied('denied') from None
        finally:self._close()
        return False
    def challenge(self):return self.c.execute('SELECT poc.challenge()').fetchone()[0]
    def install(self,token):self.c.execute("SELECT set_config('cac.poc_context',%s,true)",(token,))
    def records(self):return [str(row[0]) for row in self.c.execute('SELECT store FROM poc.records')]
