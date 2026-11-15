"""Local transport-budget checks; these are not consensus observations."""
import importlib.util
import unittest


class OneShotTransportTests(unittest.TestCase):
    def test_lost_response_cannot_resend_membership_post(self):
        self.assertIsNotNone(importlib.util.find_spec('h_quorum.l_physical.o_transport'),
                             'O wire request budget is missing')
        from h_quorum.l_physical.o_transport import OneShotRequests
        transmitted = []
        def unavailable(endpoint, path, body, token=None):
            transmitted.append((endpoint, path))
            raise OSError('synthetic lost response')
        guarded = OneShotRequests(unavailable, lambda *args, **kwargs: None)
        path = '/v3/cluster/member/remove'
        with self.assertRaises(OSError):
            guarded('https://first', path, {'ID': '1'})
        with self.assertRaisesRegex(RuntimeError, 'duplicate wire'):
            guarded('https://second', path, {'ID': '1'})
        self.assertEqual(transmitted, [('https://first', path)])

    def test_successful_mutations_keep_one_wire_receipt_each(self):
        self.assertIsNotNone(importlib.util.find_spec('h_quorum.l_physical.o_transport'),
                             'O wire request budget is missing')
        from h_quorum.l_physical.o_transport import OneShotRequests
        events = []
        def transport(endpoint, path, body, token=None):
            return {'header': {'revision': '1'}}
        guarded = OneShotRequests(transport, lambda kind, **value: events.append((kind, value)))
        for operation in ('remove', 'add', 'promote'):
            path = '/v3/cluster/member/' + operation
            self.assertEqual(guarded('https://first', path, {}), {'header': {'revision': '1'}})
        self.assertEqual([value['operation'] for kind, value in events if kind == 'WIRE_REQUEST'],
                         ['remove', 'add', 'promote'])
        self.assertEqual([kind for kind, _ in events].count('WIRE_RESPONSE'), 3)
