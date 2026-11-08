"""Q_SURVIVAL_ONLY. Shared ordered first-use and unresolved-operation barriers."""
PROFILES = {1: 'cac-h-policy-generation-1', 2: 'cac-k-policy-generation-2'}

def has_retired_unresolved(state):
    return any(op['phase'] in ('OPEN','UNKNOWN') and op['binding']['policy'] != state['policy']
               for op in state['ops'].values())

def allows_guard_policy(state,operation,version):
    # Only exact already-granted operations may continue under a retired profile.
    # Never used to admit or grant NEW work; SQL binding checks remain unchanged.
    if type(version) is not int or state.get('policy_profile') != PROFILES.get(state['policy']):return False
    if version==state['policy']:return True
    retirement=state.get('retired_policies',{}).get(str(version))
    return bool(retirement and operation and operation['phase']=='OPEN' and operation['granted']
                and operation['binding']['policy']==version
                and 0<operation.get('grant_seq',0)<retirement['seq']
                and retirement['new']<=state['policy'])

def has_unresolved(state):
    return any(op['phase'] in ('OPEN','UNKNOWN') for op in state['ops'].values())

def first_use_valid(state,operation):
    if operation['phase']!='OPEN':return False
    if not operation['granted']:return state['phase']=='ACTIVE'
    if state['phase']=='ACTIVE':return True
    return state['phase']=='REVOKING' and operation.get('grant_seq',0)>0 and operation['grant_seq']<state.get('revoke_seq',0)
