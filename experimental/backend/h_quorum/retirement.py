"""S0-09K only: real Root cut and trusted controller adoption, never orphan recovery."""
from uuid import UUID
from h_quorum.common import Denied, BANNER
from h_quorum import policy


def retire_policy(root,record,args,namespace,state,revision,history):
    if record['kind'] != 'control':raise Denied('denied')
    if (set(args)!={'expected','new','request'} or type(args['expected']) is not int
        or type(args['new']) is not int or (args['expected'],args['new'])!=(1,2)):
        raise Denied('denied')
    request=str(UUID(args['request']))
    if request!=args['request']:raise Denied('denied')
    previous=state['policy_requests'].get(request)
    if previous:
        if previous['expected']!=args['expected'] or previous['new']!=args['new']:raise Denied('denied')
        # Recover an already committed exact result, never replay a mutation.
        return dict(policy=previous['new'],retired=previous['expected'],seq=previous['seq'],
                    revision=int(history[previous['seq']]['mod_revision']))
    if (state['policy']!=args['expected'] or state['policy_profile']!=policy.PROFILES[args['expected']]
        or str(args['expected']) in state['retired_policies']):raise Denied('denied')
    seq=state['seq']+1
    state['_previous']=state['head'];state['seq']=seq
    state['policy']=args['new'];state['policy_profile']=policy.PROFILES[args['new']]
    state['retired_policies'][str(args['expected'])]=dict(new=args['new'],seq=seq,request=request)
    state['policy_requests'][request]=dict(expected=args['expected'],new=args['new'],seq=seq)
    state,revision=root.commit(namespace,state,dict(action='retire_policy',**args,profile=state['policy_profile']),revision)
    return dict(policy=state['policy'],retired=args['expected'],seq=seq,revision=revision)


def adopt_policy(lab,node='A'):
    """Existing trusted lab controller, current R + unchanged catalog/ACL.

    No SQL acceptance rule, LOGIN flag or actor incarnation is weakened. R has
    already disallowed new old-policy work, so an empty old-hold set cannot grow.
    A newer simultaneous cut can only make this config stale and deny readiness.
    """
    from h_quorum.authority import Root
    state,revision=Root(lab.rootcfg).read(lab.namespace)
    actor=state['actors'].get(node)
    if (state['policy']!=2 or state['policy_profile']!=policy.PROFILES[2]
        or not actor or not actor['admitted'] or actor['manifest']!=lab.rootcfg['approved_manifest']
        or policy.has_retired_unresolved(state)):
        raise Denied('denied')
    if lab.measure(node)!=lab.rootcfg['approved_manifest']:raise Denied('denied')
    lab.validate_private_acl(node)
    with lab.connect(node) as connection:
        rows=connection.execute('SELECT root::text,namespace::text,node,incarnation::text,policy FROM h_guard.config').fetchall()
        if len(rows)!=1 or rows[0][:4]!=(lab.rootcfg['root_id'],lab.namespace,node,actor['incarnation']) or rows[0][4] not in (1,2):
            raise Denied('denied')
        if connection.execute('UPDATE h_guard.config SET policy=%s WHERE policy<=%s',(2,2)).rowcount!=1:
            raise Denied('denied')
    lab.replay()
    print(BANNER,'K TRUSTED CONTROLLER policy2 config adopted',node,'current R revision',revision,
          'catalog unchanged; no retired OPEN/UNKNOWN',flush=True)
    return dict(policy=2,revision=revision)
