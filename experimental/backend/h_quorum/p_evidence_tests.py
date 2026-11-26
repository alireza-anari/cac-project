"""Local safe-snapshot checks; not additional real-route observations."""
import base64
import importlib.util
import json
import unittest


class SnapshotTests(unittest.TestCase):
    def test_secret_fields_are_hashed_in_state_and_decoded_journal(self):
        self.assertIsNotNone(importlib.util.find_spec('h_quorum.p_evidence'), 'P snapshot serializer missing')
        from h_quorum.p_evidence import snapshot
        secret = 'synthetic-only-ticket-never-upload'
        entry = {'command': {'action': 'first_use', 'ticket': secret}, 'seq': 1}
        row = dict(key='aw==', value=base64.b64encode(json.dumps(entry).encode()).decode(), mod_revision='7')
        result = snapshot({'ops': {'one': {'ticket': secret, 'phase': 'OPEN'}}}, 7, [row])
        encoded = json.dumps(result)
        self.assertNotIn(secret, encoded)
        self.assertEqual(len(result['redacted_fields']), 2)
        self.assertEqual(result['state']['ops']['one']['ticket']['redacted_sha256'],
                         result['journal'][0]['entry']['command']['ticket']['redacted_sha256'])

    def test_complete_order_and_nonsecret_fields_survive(self):
        self.assertIsNotNone(importlib.util.find_spec('h_quorum.p_evidence'), 'P snapshot serializer missing')
        from h_quorum.p_evidence import snapshot
        rows = [dict(key=str(n), value=base64.b64encode(json.dumps({'seq': n, 'command': {'action': 'read'}}).encode()).decode(),
                     mod_revision=str(n+10)) for n in range(3)]
        state = {'head': 'synthetic-head', 'policy': 2, 'ops': {}, 'actors': {'A': {'manifest': 'synthetic'}}}
        result = snapshot(state, 12, rows)
        self.assertEqual(result['state'], state)
        self.assertEqual(result['revision'], 12)
        self.assertEqual([r['entry']['seq'] for r in result['journal']], [0, 1, 2])
        self.assertEqual([r['key'] for r in result['journal']], ['0', '1', '2'])
        self.assertEqual([r['mod_revision'] for r in result['journal']], ['10', '11', '12'])
        self.assertEqual(result['redacted_fields'], [])
