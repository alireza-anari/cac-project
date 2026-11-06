"""Q_SURVIVAL_ONLY. Shared ordered first-use and unresolved-operation barriers."""
def has_unresolved(state):
    return any(op['phase'] in ('OPEN','UNKNOWN') for op in state['ops'].values())

def first_use_valid(state,operation):
    if operation['phase']!='OPEN':return False
    if not operation['granted']:return state['phase']=='ACTIVE'
    if state['phase']=='ACTIVE':return True
    return state['phase']=='REVOKING' and operation.get('grant_seq',0)>0 and operation['grant_seq']<state.get('revoke_seq',0)
