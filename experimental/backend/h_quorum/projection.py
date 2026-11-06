"""Q_SURVIVAL_ONLY. Non-authoritative W public materialization of actual R history."""
import hashlib
import json
from h_quorum.common import canonical,digest,Denied
from h_quorum.etcd import unb64

def public_state(state):
    result=json.loads(canonical(state))
    for operation in result['ops'].values():operation.pop('ticket',None)
    return result

def journal_hash(hashes):return hashlib.sha256('\n'.join(hashes).encode()).hexdigest()

def validate_projection(root,state,history,projection,mode,operation=None):
    expected={'root_id','namespace','seq','head','state_hash','journal_hash','count','wsid'}
    if not isinstance(projection,dict) or set(projection)!=expected:raise Denied('denied')
    seq=projection['seq']
    if (type(seq) is not int or not 0<=seq<=state['seq'] or type(projection['count']) is not int
        or projection['count']!=seq+1 or projection['root_id']!=state['root_id'] or projection['namespace']!=state['namespace']
        or projection['wsid']!=root.cfg.get('w_sid')):raise Denied('denied')
    entries=[json.loads(unb64(row['value'])) for row in history[:seq+1]]
    hashes=[digest(entry) for entry in entries];head=hashes[-1]
    snapshot=dict(entries[-1]['state'],head=head)
    if (projection['head']!=head or projection['state_hash']!=digest(public_state(snapshot)) or projection['journal_hash']!=journal_hash(hashes)):raise Denied('denied')
    if mode=='active' and seq!=state['seq']:raise Denied('denied')
    if mode=='guard' and (operation is None or seq<operation.get('grant_seq',state['seq']+1)):raise Denied('denied')

def publish(lab):
    from h_quorum.authority import Root
    state,revision,rows=Root(lab.rootcfg).read(lab.namespace,True)
    entries=[json.loads(unb64(row['value'])) for row in rows]
    hashes=[digest(entry) for entry in entries]
    body=canonical(public_state(state)).decode()
    with lab.connect('C') as c:
        for seq,head in enumerate(hashes):
            c.execute('INSERT INTO h_w.journal(namespace,seq,entry_hash) VALUES(%s,%s,%s) ON CONFLICT(namespace,seq) DO UPDATE SET entry_hash=EXCLUDED.entry_hash',(lab.namespace,seq,head))
        c.execute('INSERT INTO h_w.cache(namespace,seq,head,body) VALUES(%s,%s,%s,%s) ON CONFLICT(namespace) DO UPDATE SET seq=EXCLUDED.seq,head=EXCLUDED.head,body=EXCLUDED.body WHERE EXCLUDED.seq>=h_w.cache.seq',(lab.namespace,state['seq'],state['head'],body))
    return dict(seq=state['seq'],head=state['head'],revision=revision,open=sum(op['phase']=='OPEN' for op in state['ops'].values()),unknown=sum(op['phase']=='UNKNOWN' for op in state['ops'].values()))
