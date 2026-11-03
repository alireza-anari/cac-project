"""Real independent-cluster baseline RED before adding any fencing implementation."""
import unittest
import psycopg
from psycopg.types.json import Jsonb
from recovery_fencing.lab import Lab,P1,S1

class ParentUnsafeRestore(unittest.TestCase):
    def test_restored_service_cannot_issue_previous_response(self):
        lab=Lab();lab.seed()
        with lab.connect('A','cac_ctx_runtime') as runtime:
            h=runtime.execute('SELECT poc.challenge()').fetchone()[0]
            with lab.connect('A','cac_ctx_issuer') as issuer:
                issuer.execute('SELECT poc.issue(%s,%s,%s,%s,%s,%s)',(h,lab.cfg['A']['poc_proofs'][0],S1,'read',P1,Jsonb({}))).fetchone()
            lab.restore()
            with lab.connect('B','cac_ctx_issuer') as issuer:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    issuer.execute('SELECT poc.issue(%s,%s,%s,%s,%s,%s)',(h,lab.cfg['A']['poc_proofs'][0],S1,'read',P1,Jsonb({}))).fetchone()

result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ParentUnsafeRestore))
assert len(result.failures)==1 and not result.errors and not result.skipped,'Need assertion RED, not infrastructure error'
print('S009C PARENT EXPECTED RED: unfenced independent restore issues old ledger response',flush=True)
