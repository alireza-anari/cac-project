"""Q_SURVIVAL_ONLY. Experimental transcript; every decision rereads actual R."""
import hashlib
import hmac
import json
import re
from h_quorum.common import Denied,canonical,digest
from h_quorum.etcd import unb64
from h_quorum import policy

FIELDS={'sid','pid','tx','kind','login','digest','incarnation','manifest','policy','ticket','root_id','epoch','nonce','mode'}

def attest(root,state,revision,history,record,args,namespace,verify=False):
    if record['kind']!='check' or set(args)!=FIELDS|({'answer'} if verify else set()):raise Denied('denied')
    node=record['node'];actor=state['actors'].get(node)
    if (not actor or actor.get('admitted') is not True or state['owner']!=node
        or args['root_id']!=root.cfg['root_id'] or type(args['epoch']) is not int or args['epoch']!=state['epoch']
        or type(args['policy']) is not int or args['policy']!=state['policy']
        or args['sid']!=actor['sid'] or args['incarnation']!=actor['incarnation'] or args['manifest']!=actor['manifest']
        or type(args['pid']) is not int or args['pid']<=0 or not isinstance(args['tx'],str) or not args['tx'].isdecimal() or int(args['tx'])<=0
        or not isinstance(args['nonce'],str) or not re.fullmatch('[0-9a-f]{64}',args['nonce'])
        or not isinstance(args['ticket'],str) or len(args['ticket'])>128):raise Denied('denied')
    kinds={'cac_ctx_runtime':'runtime','cac_ctx_issuer':'issuer','cac_fence_activator':'activator'}
    if args['login'] not in kinds or args['kind']!=kinds[args['login']]:raise Denied('denied')
    if args['mode']=='active':
        if state['phase']!='ACTIVE' or args['ticket']!='' or args['digest']!='' or any(op['phase']=='UNKNOWN' for op in state['ops'].values()):raise Denied('denied')
    elif args['mode']=='guard':
        binding={key:args[key] for key in ('sid','pid','tx','kind','login','digest','incarnation','manifest','policy')}
        matches=[op for op in state['ops'].values() if hmac.compare_digest(op['ticket'],args['ticket'])]
        if len(matches)!=1:raise Denied('denied')
        op=matches[0]
        if op['node']!=node or op['epoch']!=state['epoch'] or op['binding']!=binding or not op['granted'] or not policy.first_use_valid(state,op):raise Denied('denied')
    else:raise Denied('denied')
    transcript={key:args[key] for key in FIELDS-{'ticket'}}
    transcript.update(v=1,domain='cac-s009h-q-survival',namespace=namespace,node=node,signer_epoch=state['signer_epoch'],ticket_hash=hashlib.sha256(args['ticket'].encode()).hexdigest())
    key=bytes.fromhex(root.cfg['signing_keys'][str(state['signer_epoch'])])
    if len(key)!=32:raise Denied('denied')
    if not verify:
        transcript.update(seq=state['seq'],head=state['head'],revision=revision)
        raw=canonical(transcript);answer=raw.hex()+'.'+hmac.new(key,raw,hashlib.sha256).hexdigest()
        return dict(answer=answer)
    answer=args['answer']
    if not isinstance(answer,str) or len(answer)>16000 or not re.fullmatch(r'[0-9a-f]+\.[0-9a-f]{64}',answer):raise Denied('denied')
    encoded,signature=answer.split('.');raw=bytes.fromhex(encoded)
    if not hmac.compare_digest(signature,hmac.new(key,raw,hashlib.sha256).hexdigest()):raise Denied('denied')
    proof=json.loads(raw)
    if canonical(proof)!=raw or set(proof)!=set(transcript)|{'seq','head','revision'} or any(proof[k]!=v or type(proof[k]) is not type(v) for k,v in transcript.items()):raise Denied('denied')
    seq=proof['seq']
    if type(seq) is not int or not 0<=seq<=state['seq'] or type(proof['revision']) is not int:raise Denied('denied')
    entry=json.loads(unb64(history[seq]['value']))
    if proof['head']!=digest(entry) or proof['revision']!=int(history[seq]['mod_revision']):raise Denied('denied')
    # A valid ancestor is accepted only after the current live operation/policy
    # checks above. Appending unrelated history does not invalidate an old grant.
    return dict(valid=True)
