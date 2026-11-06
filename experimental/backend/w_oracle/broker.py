"""W_ORACLE_ASSUMED. Trusted synthetic outcome observer; no ambiguous release."""
from uuid import uuid4
import psycopg
from psycopg.types.json import Jsonb
from recovery_fencing.broker import Broker as CBroker, FenceDenied
from recovery_fencing.lab import P1,S1


class Broker(CBroker):
    def __init__(self,lab,node='A',pool=None,hook=None):
        super().__init__(lab.parent,node,hook=hook)
        self.lab=lab;self.node=node;self.pool=pool
    def local(self,role):
        return self.pool.connect() if self.pool and role=='cac_ctx_runtime' else super().local(role)
    def ready(self):
        try:
            # Never queue issuer readiness behind the size-one runtime backend.
            with super().local('cac_ctx_runtime') as c:
                return c.execute('SELECT fence.is_ready()').fetchone()[0] is True
        except psycopg.Error:return False
    def activate(self,expected,request):
        try:
            with self.lab.oracle.connect(self.node) as w:
                receipt=w.execute('SELECT w.reserve(%s,%s)',(expected,request)).fetchone()[0]
            self.hook('after_w_reserve')
            # C is retained as a secondary deny-only dependency. It cannot
            # authorize around W; all app paths and final-check require W.
            current=self.status()['epoch']
            local=self.reserve(current,request)
            with super().local('cac_fence_activator') as c:
                c.execute('SELECT fence.apply(%s,%s,%s)',(local['epoch'],local['generation'],local['request']))
            self.hook('after_apply')
            with super().local('cac_fence_activator') as c:
                ack=c.execute('SELECT fence.ack(%s,%s)',(local['epoch'],local['request'])).fetchone()[0]
            with self.anchor() as c:c.execute('SELECT anchor.confirm(%s)',(ack,))
            with super().local('cac_fence_activator') as c:
                c.execute('SELECT fence.mark_ready()')
                c.execute('SELECT w_guard.set_epoch(%s)',(receipt['epoch'],))
            self.hook('after_local_ready_before_w_active')
            with self.lab.oracle.connect(self.node) as w:w.execute('SELECT w.activate(%s)',(request,))
            if not self.ready():raise FenceDenied('denied')
            return receipt
        except psycopg.Error:raise FenceDenied('denied') from None
    def runtime(self,store=S1):return Gate(self,'cac_ctx_runtime',store=store)
    def issue(self,h,store=S1):
        try:
            args=[h,self.cfg['proof'],store,'read',P1,Jsonb({})]
            with Gate(self,'cac_ctx_issuer',args=args) as g:
                token=g.c.execute('SELECT poc.issue(%s,%s,%s,%s,%s,%s)',args).fetchone()[0]
            return token
        except psycopg.Error:raise FenceDenied('denied') from None


class Gate:
    def __init__(self,broker,role,store=None,args=None):
        self.broker=broker;self.role=role;self.store=store;self.args=args
        self.c=self.a=self.w=None;self.ticket=self.wticket=None;self.held=False
    def __enter__(self):
        try:
            if not self.broker.ready():raise FenceDenied('denied')
            self.c=self.broker.local(self.role)
            self.pid,self.tx,self.sid=self.c.execute('SELECT pg_backend_pid(),txid_current()::text,fence.system_id()').fetchone()
            if self.role=='cac_ctx_runtime':
                digest=self.c.execute('SELECT w_guard.runtime_digest(%s)',(self.store,)).fetchone()[0]
            else:
                digest=self.c.execute('SELECT w_guard.issuer_digest(%s,%s,%s,%s,%s,%s)',self.args).fetchone()[0]
            oracle=self.broker.lab.oracle;actor=oracle.cfg['actors'][self.broker.node]
            self.w=oracle.connect(self.broker.node)
            self.wticket=self.w.execute('SELECT w.admit(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (str(uuid4()),str(uuid4()),digest,self.sid,self.pid,self.tx,
                 'runtime' if self.role=='cac_ctx_runtime' else 'issuer',self.role,
                 oracle.namespace,oracle.cfg['policy'],actor['incarnation'],actor['manifest'])).fetchone()[0]
            self.broker.hook('before_open_commit')
            self.w.commit() # Durable OPEN acknowledged before any permit/hold.
            self.broker.hook('after_durable_open')
            self.w.execute('SELECT w.hold(%s)',(self.wticket,))
            self.a=self.broker.anchor()
            self.ticket=self.a.execute('SELECT anchor.prepare(%s,%s,%s)',(self.pid,self.tx,self.sid)).fetchone()[0]
            self.a.commit();self.a.execute('SELECT anchor.hold(%s)',(self.ticket,));self.held=True
            for key,value in [('cac.fence_ticket',self.ticket),('cac.w_ticket',self.wticket),('cac.w_intent',digest)]:
                self.c.execute('SELECT set_config(%s,%s,true)',(key,value))
            self.c.execute('SELECT w_guard.final_check()')
            self.broker.hook('before_first_use')
            return self
        except BaseException:
            # Before a returned Gate, any created W intent stays unresolved.
            # Cleanup must never guess release after delayed/ambiguous admission.
            if self.c:
                try:self.c.rollback()
                except psycopg.Error:pass
            self._connections_close()
            raise FenceDenied('denied') from None
    def _connections_close(self):
        for c in [self.c,self.a,self.w]:
            if c:c.close()
    def __exit__(self,exc_type,exc,tb):
        try:
            if exc_type is None:
                if self.c.info.transaction_status!=psycopg.pq.TransactionStatus.INTRANS:
                    raise FenceDenied('Unexpected local outcome')
                binding=self.c.execute('SELECT pg_backend_pid(),txid_current()::text,fence.system_id()').fetchone()
                if binding!=(self.pid,self.tx,self.sid):raise FenceDenied('Local transaction changed')
                self.c.execute('SELECT w_guard.final_check()');self.broker.hook('after_final_guard')
                self.broker.hook('before_local_commit');self.c.commit();outcome='commit'
                self.broker.hook('after_local_commit_before_close')
            else:
                # Gate exclusively owns the connection; callback may not commit
                # it itself. Unexpected IDLE is ambiguous and remains blocked.
                if self.c.info.transaction_status==psycopg.pq.TransactionStatus.INERROR:
                    # SQL cannot confirm fullxid in an aborted transaction. A
                    # ROLLBACK ACK alone cannot identify the original tx after
                    # hostile COMMIT;BEGIN. Deliberately sacrifice availability.
                    self.c.rollback();self._unknown();return False
                if self.c.info.transaction_status!=psycopg.pq.TransactionStatus.INTRANS:
                    raise FenceDenied('Unexpected local outcome')
                binding=self.c.execute('SELECT pg_backend_pid(),txid_current()::text,fence.system_id()').fetchone()
                if binding!=(self.pid,self.tx,self.sid):raise FenceDenied('Local transaction changed')
                self.c.rollback();outcome='abort';self.broker.hook('after_local_abort_before_close')
            if self.c.info.transaction_status!=psycopg.pq.TransactionStatus.IDLE:raise FenceDenied('Missing local ACK')
            # C may cause additional denial, never early W release. W CLOSE last.
            self.a.execute('SELECT anchor.finish(%s)',(self.ticket,));self.a.commit()
            self.broker.hook('after_c_finish_before_w_close')
            self.w.execute('SELECT w.close(%s,%s,%s,%s,%s)',(self.wticket,outcome,self.pid,self.tx,self.sid))
            self.broker.hook('after_w_close_before_commit');self.w.commit()
            self.broker.hook('after_close_ack')
        except BaseException:
            self._unknown()
            raise FenceDenied('denied') from None
        finally:self._connections_close()
        return False
    def _unknown(self):
        if self.w and self.wticket:
            try:
                self.w.rollback();self.w.execute('SELECT w.unknown(%s)',(self.wticket,));self.w.commit()
            except psycopg.Error:pass # Durable OPEN still excludes takeover.
    def challenge(self):return self.c.execute('SELECT poc.challenge()').fetchone()[0]
    def install(self,token):self.c.execute("SELECT set_config('cac.poc_context',%s,true)",(token,))
    def records(self):return [str(r[0]) for r in self.c.execute('SELECT store FROM poc.records')]
