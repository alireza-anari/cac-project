"""Q_SURVIVAL_ONLY. Authoritative state and journal use actual etcd transactions."""
import json
from uuid import UUID
from h_quorum.common import Denied,canonical,digest
from h_quorum.etcd import Etcd,b64,unb64

class Root:
    def __init__(self,cfg):self.cfg=cfg;self.etcd=Etcd(cfg)
    def prefix(self,namespace):
        if str(UUID(namespace))!=namespace:raise Denied('denied')
        return '/cac-h/'+namespace+'/'
    def commit(self,namespace,state,command,revision):
        prefix=self.prefix(namespace);state=dict(state);state.pop('head',None)
        entry=dict(seq=state['seq'],previous=state.pop('_previous','0'*64),command=command,state=state)
        head=digest(entry);state=dict(state,head=head)
        key=prefix+'state';journal=prefix+'journal/'+format(state['seq'],'020d')
        comparison=dict(key=b64(key),target='MOD',result='EQUAL',mod_revision=str(revision)) if revision else dict(key=b64(key),target='VERSION',result='EQUAL',version='0')
        result=self.etcd.txn([comparison],[{'request_put':{'key':b64(key),'value':b64(canonical(state))}},{'request_put':{'key':b64(journal),'value':b64(canonical(entry))}}])
        if not result.get('succeeded'):raise Denied('denied')
        return state,int(result['header']['revision'])
    def read(self,namespace):
        prefix=self.prefix(namespace);result=self.etcd.range(prefix+'state')
        if str(result['header']['cluster_id'])!=str(self.cfg['cluster_id']) or len(result.get('kvs',[]))!=1:raise Denied('denied')
        kv=result['kvs'][0];state=json.loads(unb64(kv['value']));revision=int(kv['mod_revision'])
        history=self.etcd.range(prefix+'journal/',prefix=True,revision=int(result['header']['revision']))
        rows=history.get('kvs',[])
        if len(rows)!=state['seq']+1:raise Denied('denied')
        previous='0'*64
        for seq,row in enumerate(rows):
            entry=json.loads(unb64(row['value']))
            if unb64(row['key']).decode()!=prefix+'journal/'+format(seq,'020d') or entry['seq']!=seq or entry['previous']!=previous:raise Denied('denied')
            previous=digest(entry)
        expected=dict(state);expected.pop('head')
        if previous!=state['head'] or entry['state']!=expected or int(rows[-1]['mod_revision'])!=revision:raise Denied('denied')
        return state,revision
    def dispatch(self,role,payload):
        record=self.cfg['roles'].get(role)
        if not record or set(payload)!={'action','args','namespace'} or not isinstance(payload['args'],dict):raise Denied('denied')
        action,args,namespace=payload['action'],payload['args'],payload['namespace']
        self.prefix(namespace)
        if action=='genesis':
            if record['kind']!='control' or set(args)!={'actors'} or set(args['actors'])!={'A','B'}:raise Denied('denied')
            state=dict(root_id=self.cfg['root_id'],namespace=namespace,cluster_id=self.cfg['cluster_id'],seq=0,epoch=0,owner=None,phase='EMPTY',policy=1,signer_epoch=1,actors=args['actors'],ops={},requests={},activations={})
            state,revision=self.commit(namespace,state,{'action':'genesis'},0)
        else:state,revision=self.read(namespace)
        if action in ('status','genesis'):
            return {k:state[k] for k in ('root_id','namespace','epoch','owner','phase','seq','head','policy','signer_epoch')}|{'revision':revision}
        if action=='inspect' and record['kind']=='control':return dict(state_revision=revision,journal_revision=revision,seq=state['seq'],head=state['head'],complete=True)
        if action=='reserve' and record['kind']=='coord':
            node=record['node']
            if set(args)!={'expected','request'} or type(args['expected']) is not int:raise Denied('denied')
            request=str(UUID(args['request']))
            actor=state['actors'].get(node)
            if not actor or actor.get('admitted') is not True:raise Denied('denied')
            previous=state['activations'].get(request)
            if previous:
                if previous!={'owner':node,'expected':args['expected'],'epoch':state['epoch']} or state.get('request')!=request:raise Denied('denied')
                return dict(epoch=state['epoch'],owner=node,request=request,revision=revision)
            if args['expected']!=state['epoch'] or state['phase'] not in ('EMPTY','REVOKING') or any(op['phase'] in ('OPEN','UNKNOWN') for op in state['ops'].values()):raise Denied('denied')
            state['_previous']=state['head'];state['seq']+=1;state['epoch']+=1;state['owner']=node;state['phase']='RESERVED';state['request']=request
            state['activations'][request]=dict(owner=node,expected=args['expected'],epoch=state['epoch'])
            state,revision=self.commit(namespace,state,dict(action=action,node=node,**args),revision)
            return dict(epoch=state['epoch'],owner=node,request=request,revision=revision)
        raise Denied('denied')
