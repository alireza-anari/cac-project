"""SEC-REV-001 regressions against the real SQLite reference service.

Identity is the existing explicit test fake; no claim of IdP/PostgreSQL coverage.
"""
import sqlite3
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from cac_onboarding.policy import IdentityState, PolicyError
from cac_onboarding.service import OnboardingService
from cac_onboarding.storage import SQLiteReferenceRepository
from test_onboarding import NOW, TrustedVerifier


class RevocationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = SQLiteReferenceRepository(Path(self.tmp.name) / 'revoke.db')
        self.verifier = TrustedVerifier()
        for principal in range(1, 7):
            self.verifier.verify(principal, mfa=(principal == 1))
        self.service = OnboardingService(self.repo, self.verifier, now=lambda: NOW)
        request = self.service.request_first_store(1, 'Tenant A', 'Store A1', 'A'*32)
        self.first = self.service.fulfill_queued(request.request_id)
        self.store = self.first.store_id

    def invite(self, target=2, caps=None, store=None, owner=1):
        return self.service.issue_invitation(owner, store or self.store, target,
                                             caps or ['store.view'])

    def row(self, invitation):
        with self.repo.connection() as db:
            return dict(db.execute('SELECT * FROM invitations WHERE id=?',
                                   (invitation,)).fetchone())

    def audits(self):
        with self.repo.connection() as db:
            return [dict(r) for r in db.execute(
                "SELECT * FROM audit_events WHERE event='CAPABILITY_REVOKED' ORDER BY id")]

    def assert_denied(self, code, function, *args):
        with self.assertRaises(PolicyError) as caught:
            function(*args)
        self.assertEqual(code, caught.exception.code)

    def test_pending_only_invite_cannot_grant_after_revoke(self):
        inv, token = self.invite()
        self.service.revoke_capability(1, self.store, 2, 'store.view')
        self.assert_denied('INVITATION_EXPIRED_OR_USED',
                           self.service.accept_invitation, 2, inv, token)
        with self.repo.connection() as db:
            self.assertEqual(0, db.execute(
                'SELECT count(*) FROM grants WHERE principal_id=2').fetchone()[0])

    def test_pending_only_effective_revoke_is_audited(self):
        self.invite()
        self.service.revoke_capability(1, self.store, 2, 'store.view')
        events = self.audits()
        self.assertEqual(1, len(events))
        self.assertEqual((self.store, 1, '2:store.view', NOW.isoformat()),
                         (events[0]['store_id'], events[0]['actor_id'],
                          events[0]['entity_id'], events[0]['created_at']))

    def test_multi_capability_invite_is_invalidated_as_a_whole(self):
        inv, token = self.invite(caps=['store.view', 'knowledge.edit'])
        self.service.revoke_capability(1, self.store, 2, 'store.view')
        self.assertIsNotNone(self.row(inv)['revoked_at'])
        self.assert_denied('INVITATION_EXPIRED_OR_USED',
                           self.service.accept_invitation, 2, inv, token)

    def test_all_matching_pending_invites_are_invalidated(self):
        invitations = [self.invite(), self.invite(caps=['store.view', 'knowledge.edit'])]
        self.service.revoke_capability(1, self.store, 2, 'store.view')
        for inv, token in invitations:
            self.assert_denied('INVITATION_EXPIRED_OR_USED',
                               self.service.accept_invitation, 2, inv, token)
        self.assertEqual(1, len(self.audits()))

    def test_store_target_and_capability_scope_preserves_unrelated_invites(self):
        # A2 shares Tenant A. Add only fixture data, not another onboarding path.
        second_store = str(uuid4())
        with self.repo.transaction() as db:
            db.execute('INSERT INTO stores(id,tenant_id,display_name,created_at) VALUES(?,?,?,?)',
                       (second_store, self.first.tenant_id, 'Store A2', NOW.isoformat()))
            db.execute('''INSERT INTO grants(tenant_id,store_id,principal_id,capability,
                          granted_by,created_at) SELECT tenant_id,?,principal_id,capability,
                          granted_by,created_at FROM grants WHERE store_id=?''',
                       (second_store, self.store))
        request = self.service.request_first_store(4, 'Tenant B', 'Store B1', 'B'*32)
        foreign_store = self.service.fulfill_queued(request.request_id).store_id
        matched = self.invite()
        unrelated = [
            (3, *self.invite(target=3), self.store, {'store.view'}),
            (2, *self.invite(caps=['knowledge.edit']), self.store, {'knowledge.edit'}),
            (2, *self.invite(store=second_store), second_store, {'store.view'}),
            (2, *self.invite(store=foreign_store, owner=4), foreign_store, {'store.view'}),
        ]
        before = {inv: self.row(inv) for _, inv, _, _, _ in unrelated}
        self.service.revoke_capability(1, self.store, 2, 'store.view')
        self.assert_denied('INVITATION_EXPIRED_OR_USED',
                           self.service.accept_invitation, 2, *matched)
        for target, inv, token, store, expected in unrelated:
            self.assertEqual(before[inv], self.row(inv))
            self.service.accept_invitation(target, inv, token)
            self.assertEqual(expected, self.service.list_capabilities(target, store))

    def test_repeated_revoke_has_no_new_side_effects(self):
        inv, token = self.invite()
        self.service.revoke_capability(1, self.store, 2, 'store.view')
        first_row, first_audit = self.row(inv), self.audits()
        self.assertIsNotNone(first_row['revoked_at'])
        self.assertEqual(1, len(first_audit))
        self.service.now = lambda: NOW + timedelta(minutes=1)
        self.service.revoke_capability(1, self.store, 2, 'store.view')
        self.assertEqual(first_row, self.row(inv))
        self.assertEqual(first_audit, self.audits())
        self.assert_denied('INVITATION_EXPIRED_OR_USED',
                           self.service.accept_invitation, 2, inv, token)

    def test_no_effect_revoke_does_not_emit_effective_event(self):
        self.service.revoke_capability(1, self.store, 2, 'store.view')
        self.assertEqual([], self.audits())

    def test_new_authorized_invitation_after_revoke_remains_allowed(self):
        old_inv, old_token = self.invite()
        self.service.revoke_capability(1, self.store, 2, 'store.view')
        new_inv, new_token = self.invite()
        self.service.accept_invitation(2, new_inv, new_token)
        self.assertEqual({'store.view'}, self.service.list_capabilities(2, self.store))
        self.assert_denied('INVITATION_EXPIRED_OR_USED',
                           self.service.accept_invitation, 2, old_inv, old_token)

    def test_sensitive_pending_revoke_requires_fresh_mfa(self):
        inv, token = self.invite(caps=['assistant.activate'])
        for stamp in [None, NOW-timedelta(minutes=10, seconds=1)]:
            with self.subTest(stamp=stamp):
                self.verifier.identities[1] = IdentityState(True, True, stamp)
                self.assert_denied('FRESH_MFA_REQUIRED', self.service.revoke_capability,
                                   1, self.store, 2, 'assistant.activate')
                self.assertIsNone(self.row(inv)['revoked_at'])
                self.assertEqual([], self.audits())
        self.verifier.verify(1, mfa=True)
        self.service.revoke_capability(1, self.store, 2, 'assistant.activate')
        self.assert_denied('INVITATION_EXPIRED_OR_USED',
                           self.service.accept_invitation, 2, inv, token)

    def test_manager_cannot_revoke_unheld_or_sensitive_pending_capability(self):
        manager_inv, manager_token = self.invite(target=3, caps=['store.members.manage','store.view'])
        self.service.accept_invitation(3, manager_inv, manager_token)
        for cap in ['knowledge.edit', 'assistant.activate']:
            with self.subTest(cap=cap):
                inv, _ = self.invite(caps=[cap])
                self.assert_denied('DELEGATION_FORBIDDEN', self.service.revoke_capability,
                                   3, self.store, 2, cap)
                self.assertIsNone(self.row(inv)['revoked_at'])
        self.assertEqual([], self.audits())

    def test_authorized_manager_can_revoke_held_low_risk_pending_capability(self):
        manager_inv, manager_token = self.invite(target=3, caps=['store.members.manage','store.view'])
        self.service.accept_invitation(3, manager_inv, manager_token)
        inv, token = self.invite()
        self.service.revoke_capability(3, self.store, 2, 'store.view')
        self.assert_denied('INVITATION_EXPIRED_OR_USED',
                           self.service.accept_invitation, 2, inv, token)
        self.assertEqual(3, self.audits()[0]['actor_id'])

    def test_audit_failure_rolls_back_grant_and_invitation_revocation(self):
        accepted, accepted_token = self.invite()
        self.service.accept_invitation(2, accepted, accepted_token)
        pending, token = self.invite()
        with self.repo.transaction() as db:
            db.execute("""CREATE TRIGGER fail_revoke_audit BEFORE INSERT ON audit_events
                          WHEN NEW.event='CAPABILITY_REVOKED'
                          BEGIN SELECT RAISE(ABORT, 'synthetic audit failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.service.revoke_capability(1, self.store, 2, 'store.view')
        self.assertIsNone(self.row(pending)['revoked_at'])
        self.assertEqual({'store.view'}, self.service.list_capabilities(2, self.store))
        self.assertEqual([], self.audits())
        self.service.accept_invitation(2, pending, token)

    def test_pending_only_audit_failure_rolls_back_invitation_revocation(self):
        inv, token = self.invite()
        with self.repo.transaction() as db:
            db.execute("""CREATE TRIGGER fail_revoke_audit BEFORE INSERT ON audit_events
                          WHEN NEW.event='CAPABILITY_REVOKED'
                          BEGIN SELECT RAISE(ABORT, 'synthetic audit failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.service.revoke_capability(1, self.store, 2, 'store.view')
        self.assertIsNone(self.row(inv)['revoked_at'])
        self.assertEqual([], self.audits())
        self.service.accept_invitation(2, inv, token)


if __name__ == '__main__':
    unittest.main()
