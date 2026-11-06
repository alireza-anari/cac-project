"""Q_SURVIVAL_ONLY. Test-process-only admission mutation; no executable guard option."""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from h_quorum.common import BANNER
from h_quorum.integration_lab import IntegrationLab

def main():
    control,test=sys.argv[1:];original_admit=IntegrationLab.admit
    def admission(lab,node):
        with lab.connect(node) as c:old=c.execute("SELECT to_regclass('h_guard.config') IS NULL").fetchone()[0]
        if not old:return original_admit(lab,node)
        # Parent owns this durable restoration receipt BEFORE any LOGIN mutation.
        path=Path(os.environ['CAC_H_MUTATION_RECEIPT'])
        flags=None
        with lab.connect(node) as c:flags=c.execute("SELECT rolname,rolcanlogin FROM pg_roles WHERE rolname IN ('cac_ctx_runtime','cac_ctx_issuer') ORDER BY rolname").fetchall()
        if flags!=[('cac_ctx_issuer',False),('cac_ctx_runtime',False)]:raise AssertionError('Admission mutant lacks quarantined baseline')
        path.write_text(json.dumps(dict(node=node,manifest=lab.measure(node),flags=flags)));path.chmod(0o600)
        # Disable only the independent quarantine/current-verifier admission
        # boundary. Old restored C-only SQL and its function/table ACL stay exact.
        with lab.connect(node) as c:c.execute('ALTER ROLE cac_ctx_runtime LOGIN;ALTER ROLE cac_ctx_issuer LOGIN')
        try:
            from recovery_fencing.broker import Broker as LegacyBroker
            from recovery_fencing.lab import S1
            legacy=LegacyBroker(lab.parent,node)
            with legacy.runtime() as g:
                g.install(legacy.issue(g.challenge()))
                if g.records()!=[S1]:raise AssertionError('Admission mutant did not reach genuine old verifier scope')
            print(BANNER,'UNSAFE ADMISSION WITNESS old verifier fresh issuance and actual scoped RLS read under bypassed quarantine',flush=True)
        finally:lab.quarantine(node)
        # Parent independently rechecks exact flags/catalog even on child death.
    if control=='guard_admission':
        with patch.object(IntegrationLab,'admit',admission):result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName(test))
    else:result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName(test))
    raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)

if __name__=='__main__':main()
