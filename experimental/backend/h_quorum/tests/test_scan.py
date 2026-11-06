"""Synthetic artifact-scan regression; no database or external secrets."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from h_quorum.common import BANNER
from h_quorum.scan import main

class EvidenceScanTests(unittest.TestCase):
    def scan(self,config,body):
        with tempfile.TemporaryDirectory(prefix='cac-h-scan-') as temporary:
            root=Path(temporary);evidence=root/'evidence-s009h';evidence.mkdir()
            parent=root/'parent.json';parent.write_text(json.dumps(config))
            authority=root/'root.json';authority.write_text('{}')
            (evidence/'proof.log').write_text(BANNER+'\n'+body+'\n')
            output=root/'output'
            with patch.dict(os.environ,dict(CAC_C_CONFIG=str(parent),CAC_H_CONFIG=str(authority),GITHUB_WORKSPACE=str(root),GITHUB_OUTPUT=str(output))):main()
            return output.read_text()
    def test_every_known_fixture_credential_container_is_rejected(self):
        secret='synthetic-scan-negative-credential-only'
        for config in [dict(A=dict(passwords=dict(cac_ctx_runtime=secret))),dict(A=dict(anchor_password=secret)),dict(proof=secret),dict(A=dict(poc_proofs=[secret])),dict(signing_keys={'7':secret}),dict(roles=dict(A_check=dict(password=secret))),dict(fence_secret=secret)]:
            with self.subTest(container=next(iter(config))):
                with self.assertRaisesRegex(RuntimeError,'Evidence scan denied'):self.scan(config,secret)
    def test_safe_evidence_emits_upload_gate(self):
        self.assertEqual(self.scan(dict(A=dict(passwords=dict(cac_ctx_runtime='synthetic-unused-private-value'))),'public epoch=2 PID=123 fullxid=456'),'safe=true\n')
