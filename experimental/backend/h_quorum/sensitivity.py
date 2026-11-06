"""Q_SURVIVAL_ONLY. Independent actual-R sensitivity with parent-owned restoration."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
from h_quorum.common import BANNER,config
from h_quorum.integration_lab import IntegrationLab

# Narrow current-head mutation: select an authentic ancestor for readiness only.
# All local/transcript/signature/W checks still execute. Actual R ADMIT stays
# current and must deny old A; this RED is readiness, not an RLS bypass claim.
STALE_ACTIVE="""if args.get('mode')=='active' and isinstance(args.get('projection'),dict) and type(args['projection'].get('seq')) is int and 0<=args['projection']['seq']<state['seq']:
    old_seq=args['projection']['seq']
    old_entry=json.loads(unb64(history[old_seq]['value']))
    state=dict(old_entry['state'],head=digest(old_entry))
    revision=int(history[old_seq]['mod_revision'])
    history=history[:old_seq+1]"""
CASES=[
    ('current_head','h_quorum.tests.test_recovery.RecoveryTests.test_00_real_old_w_restore_never_revives_old_owner','attestation.py',('attest',STALE_ACTIVE),'Restored old W revived old-owner readiness under current R','STALE HEAD READINESS WITNESS'),
    ('guard_admission','h_quorum.tests.test_recovery.RecoveryTests.test_02_old_guard_is_quarantined_and_cannot_self_admit',None,None,'AssertionError not raised','UNSAFE ADMISSION WITNESS'),
    ('complete_replay','h_quorum.tests.test_recovery.RecoveryTests.test_04_live_scoped_sql_denies_incomplete_w_without_admit_repair','projection.py',('validate_projection','return'),'InsufficientPrivilege not raised','UNSAFE REPLAY WITNESS'),
    ('first_use_order','h_quorum.tests.test_ordering.OrderingTests.test_01_revoke_after_open_before_first_use_denies_and_retains_unknown','policy.py',('first_use_valid',"return operation['phase']=='OPEN'"),'Revoked ungranted operation reached application code','UNSAFE FIRST USE WITNESS'),
    ('hold_preservation','h_quorum.tests.test_ordering.OrderingTests.test_00_actual_late_protected_commit_holds_successor_until_root_close','policy.py',('has_unresolved','return False'),'Denied not raised','UNSAFE HOLD WITNESS'),
]

def execute(command,env=None):
    result=subprocess.run([sys.executable,'-m',*command],text=True,capture_output=True,timeout=180,env=env)
    print(result.stdout,flush=True);print(result.stderr,flush=True)
    return result

def restart_current():
    lab=IntegrationLab();lab.rootcfg=config();lab.namespace=lab.rootcfg['app_namespace']
    try:lab.restart_service()
    finally:lab.close()

def restore_admission(receipt):
    # Always quarantine, including a timeout before receipt/LOGIN. No subsequent
    # probe runs until the independent checks below complete successfully.
    lab=IntegrationLab()
    try:
        lab.quarantine('A')
        if receipt.exists():
            original=json.loads(receipt.read_text())
            if original['node']!='A' or original['flags']!=[['cac_ctx_issuer',False],['cac_ctx_runtime',False]]:raise AssertionError('Invalid mutation restoration receipt')
            with lab.connect() as c:actual=c.execute("SELECT rolname,rolcanlogin FROM pg_roles WHERE rolname IN ('cac_ctx_runtime','cac_ctx_issuer') ORDER BY rolname").fetchall()
            if [list(row) for row in actual]!=original['flags'] or lab.measure('A')!=original['manifest']:raise AssertionError('Admission mutation original catalog/ACL/LOGIN restoration mismatch')
            print(BANNER,'EXACT ADMISSION MUTATION RESTORED parent verified original SQL/catalog/ACL and both NOLOGIN flags',flush=True)
    finally:lab.close()

def main():
    config()
    for name,test,filename,insertion,message,witness in CASES:
        print(BANNER,'H05 HEALTHY ORIGINAL PROBE',name,flush=True)
        baseline=execute(['unittest','-v',test])
        if baseline.returncode or 'Ran 1 test' not in baseline.stderr:raise AssertionError('H05 baseline is not a healthy original probe: '+name)
        path=Path(__file__).with_name(filename) if filename else None
        original=path.read_bytes() if path else None
        with tempfile.TemporaryDirectory(prefix='cac-h05-parent-') as directory:
            receipt=Path(directory)/'admission.json';env=dict(os.environ,CAC_H_MUTATION_RECEIPT=str(receipt))
            try:
                if path:
                    function,statement=insertion;lines=original.decode().splitlines(keepends=True)
                    found=[i for i,line in enumerate(lines) if line.startswith('def '+function+'(')]
                    if len(found)!=1:raise AssertionError('Ambiguous exact mutation target')
                    lines.insert(found[0]+1,textwrap.indent(statement,'    ')+'\n');path.write_text(''.join(lines))
                print(BANNER,'H05 INTENTIONAL ONE CONTROL MUTANT',name,flush=True)
                mutant=execute(['h_quorum.sensitivity_worker',name,test],env=env)
            finally:
                if path:
                    path.write_bytes(original)
                    if path.read_bytes()!=original:raise AssertionError('H05 source restoration mismatch')
                    print(BANNER,'EXACT SOURCE MUTATION RESTORED',name,'sha256',hashlib.sha256(original).hexdigest(),flush=True)
                    restart_current() # exact source, same current R, no R restore
                if name=='guard_admission':restore_admission(receipt)
        combined=mutant.stdout+mutant.stderr
        if mutant.returncode!=1 or message not in combined or witness not in combined or 'FAILED (failures=1)' not in combined or 'ERROR:' in combined:raise AssertionError('H05 intended original security assertion RED was not demonstrated: '+name)
        print(BANNER,'H05 EXPECTED_MUTATION_RED',name,'original assertion',message,flush=True)
        green=execute(['unittest','-v',test])
        if green.returncode or 'Ran 1 test' not in green.stderr:raise AssertionError('H05 identical restored probe did not return GREEN: '+name)
        print(BANNER,'H05 RESTORED SAME PROBE GREEN',name,flush=True)
    print(BANNER,'H05 controls completed healthy/target RED/exact restoration/same GREEN; current-head RED covers stale readiness with current ADMIT still denied; no root-majority rollback claim',flush=True)

if __name__=='__main__':main()
