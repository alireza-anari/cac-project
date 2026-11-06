"""Q_SURVIVAL_ONLY. Authoritative state and journal use actual etcd transactions."""
import json
import secrets
import re
from uuid import UUID
from h_quorum.common import Denied,canonical,digest
from h_quorum.etcd import Etcd,b64,unb64
from h_quorum import policy

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
    def read(self,namespace,with_history=False):
        prefix=self.prefix(namespace);result=self.etcd.range(prefix+'state')
        if str(result['header']['cluster_id'])!=str(self.cfg['cluster_id']) or len(result.get('kvs',[]))!=1:raise Denied('denied')
        kv=result['kvs'][0];state=json.loads(unb64(kv['value']));revision=int(kv['mod_revision'])
        if state['root_id']!=self.cfg['root_id'] or state['namespace']!=namespace:raise Denied('denied')
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
        return (state,revision,rows) if with_history else (state,revision)
    def dispatch(self,role,payload):
        record=self.cfg['roles'].get(role)
        if not record or set(payload)!={'action','args','namespace'} or not isinstance(payload['args'],dict):raise Denied('denied')
        action,args,namespace=payload['action'],payload['args'],payload['namespace']
        self.prefix(namespace)
        if action=='genesis':
            if record['kind']!='control' or set(args)!={'actors'} or set(args['actors'])!={'A','B'}:raise Denied('denied')
            state=dict(root_id=self.cfg['root_id'],namespace=namespace,cluster_id=self.cfg['cluster_id'],seq=0,epoch=0,owner=None,phase='EMPTY',policy=1,signer_epoch=1,actors=args['actors'],ops={},requests={},activations={})
            state,revision=self.commit(namespace,state,{'action':'genesis'},0)
        else:state,revision,history=self.read(namespace,True)
        if action in ('status','genesis'):
            return {k:state[k] for k in ('root_id','namespace','epoch','owner','phase','seq','head','policy','signer_epoch')}|{'revision':revision}
        if action=='inspect' and record['kind']=='control':return dict(state_revision=revision,journal_revision=revision,seq=state['seq'],head=state['head'],complete=True,open=sum(op['phase']=='OPEN' for op in state['ops'].values()),unknown=sum(op['phase']=='UNKNOWN' for op in state['ops'].values()),granted=sum(op.get('granted',False) and op['phase']=='OPEN' for op in state['ops'].values()))
        if action in ('guard','verify'):
            from h_quorum.attestation import attest
            return attest(self,state,revision,history,record,args,namespace,verify=action=='verify')
        if action=='retire_signer' and record['kind']=='control':
            if (set(args)!={'expected','new'} or type(args['expected']) is not int or type(args['new']) is not int
                or args['expected']!=state['signer_epoch'] or args['new']<=args['expected'] or str(args['new']) not in self.cfg['signing_keys']):raise Denied('denied')
            state['_previous']=state['head'];state['seq']+=1;state['signer_epoch']=args['new']
            state,revision=self.commit(namespace,state,dict(action=action,**args),revision)
            return dict(signer_epoch=state['signer_epoch'],revision=revision)
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
            if args['expected']!=state['epoch'] or state['phase'] not in ('EMPTY','REVOKING') or policy.has_unresolved(state):raise Denied('denied')
            state['_previous']=state['head'];state['seq']+=1;state['epoch']+=1;state['owner']=node;state['phase']='RESERVED';state['request']=request;state.pop('revoke_seq',None)
            state['activations'][request]=dict(owner=node,expected=args['expected'],epoch=state['epoch'])
            state,revision=self.commit(namespace,state,dict(action=action,node=node,**args),revision)
            return dict(epoch=state['epoch'],owner=node,request=request,revision=revision)
        if record['kind']!='coord':raise Denied('denied')
        node=record['node'];actor=state['actors'].get(node)
        if not actor or actor.get('admitted') is not True:raise Denied('denied')
        def write(command):
            state['_previous']=state['head'];state['seq']+=1
            return self.commit(namespace,state,dict(action=action,node=node,**command),revision)
        def summary(current,rev):return dict(epoch=current['epoch'],phase=current['phase'],owner=current['owner'],revision=rev)
        unresolved=policy.has_unresolved(state)
        if action=='activate':
            if set(args)!={'request'} or args['request']!=state.get('request') or state['owner']!=node or unresolved:raise Denied('denied')
            if state['phase']=='ACTIVE':return summary(state,revision)
            if state['phase']!='RESERVED':raise Denied('denied')
            state['phase']='ACTIVE';state,revision=write(args)
            return summary(state,revision)
        if action=='revoke':
            if set(args)!={'expected'} or type(args['expected']) is not int or args['expected']!=state['epoch'] or state['phase'] not in ('ACTIVE','REVOKING'):raise Denied('denied')
            if state['phase']=='REVOKING':return summary(state,revision)
            state['phase']='REVOKING';state['revoke_seq']=state['seq']+1;state,revision=write(args)
            return summary(state,revision)
        binding_keys={'sid','pid','tx','kind','login','digest','incarnation','manifest','policy'}
        def binding():
            b={key:args[key] for key in binding_keys}
            if (b['sid']!=actor['sid'] or b['incarnation']!=actor['incarnation'] or b['manifest']!=actor['manifest'] or type(b['policy']) is not int or b['policy']!=state['policy']
                or type(b['pid']) is not int or b['pid']<=0 or not isinstance(b['tx'],str) or not b['tx'].isdecimal() or int(b['tx'])<=0
                or b['kind'] not in ('runtime','issuer') or b['login']!={'runtime':'cac_ctx_runtime','issuer':'cac_ctx_issuer'}[b['kind']]
                or not isinstance(b['digest'],str) or not re.fullmatch('[0-9a-f]{64}',b['digest'])):raise Denied('denied')
            return b
        if action=='admit':
            if set(args)!=binding_keys|{'request','operation'} or state['phase']!='ACTIVE' or state['owner']!=node or any(op['phase']=='UNKNOWN' for op in state['ops'].values()):raise Denied('denied')
            b=binding();request=str(UUID(args['request']));operation=str(UUID(args['operation']))
            fingerprint=digest(dict(node=node,epoch=state['epoch'],args=args))
            previous=state['requests'].get(request)
            if previous:
                op=state['ops'][previous['operation']]
                if previous['fingerprint']!=fingerprint or op['phase']!='OPEN' or op['epoch']!=state['epoch']:raise Denied('denied')
                return dict(ticket=op['ticket'],epoch=op['epoch'],operation=operation,revision=revision)
            if operation in state['ops']:raise Denied('denied')
            ticket=secrets.token_urlsafe(32)
            state['ops'][operation]=dict(ticket=ticket,node=node,epoch=state['epoch'],binding=b,phase='OPEN',granted=False,admit_seq=state['seq']+1)
            state['requests'][request]=dict(operation=operation,fingerprint=fingerprint)
            state,revision=write(dict(request=request,operation=operation,binding=b))
            return dict(ticket=ticket,epoch=state['epoch'],operation=operation,revision=revision)
        if action not in ('first_use','unknown','close'):raise Denied('denied')
        expected=binding_keys|{'ticket'}|({'outcome'} if action=='close' else set())
        if set(args)!=expected:raise Denied('denied')
        b=binding();matches=[(key,op) for key,op in state['ops'].items() if secrets.compare_digest(op['ticket'],str(args['ticket']))]
        if len(matches)!=1:raise Denied('denied')
        operation,op=matches[0]
        if op['node']!=node or op['binding']!=b or op['epoch']!=state['epoch'] or state['owner']!=node:raise Denied('denied')
        if action=='unknown':
            if op['phase']=='UNKNOWN':return summary(state,revision)
            if op['phase']!='OPEN':raise Denied('denied')
            op['phase']='UNKNOWN'
        elif action=='first_use':
            if op['phase']!='OPEN':raise Denied('denied')
            if op['granted']:
                if not policy.first_use_valid(state,op):raise Denied('denied')
                return summary(state,revision)
            if not policy.first_use_valid(state,op):raise Denied('denied')
            op['granted']=True;op['grant_seq']=state['seq']+1
        else:
            if op['phase']!='OPEN' or not op['granted'] or args['outcome'] not in ('commit','abort') or state['phase'] not in ('ACTIVE','REVOKING'):raise Denied('denied')
            op['phase']='CLOSED_'+args['outcome'].upper();op['close_seq']=state['seq']+1
        state,revision=write(dict(operation=operation,binding=b,**({'outcome':args['outcome']} if action=='close' else {})))
        return summary(state,revision)
