import hashlib
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from cac_onboarding.policy import (IdentityState, PolicyError, OWNER_CAPABILITIES,
                                   clean_display_name, canonical_caps)
from cac_onboarding.storage import SQLiteReferenceRepository
from cac_onboarding.service import OnboardingService

NOW = datetime(2026, 10, 26, 10, 0, tzinfo=timezone.utc)
KEY1 = 'A'*32
KEY2 = 'B'*32
KEY3 = 'C'*32

class TrustedVerifier:
    """Fake trusted service; tests only. Never instantiate from client payload."""
    def __init__(self):
        self.identities = {}
    def resolve(self, principal_id):
        return self.identities.get(principal_id)
    def verify(self, principal_id, *, mfa=False):
        self.identities[principal_id] = IdentityState(True, True, NOW if mfa else None)

class ProvisioningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = SQLiteReferenceRepository(Path(self.tmp.name)/'cases.db')
        self.verifier = TrustedVerifier()
        for i in range(1,7): self.verifier.verify(i, mfa=(i==1))
        self.service = OnboardingService(self.repo,self.verifier,now=lambda:NOW)

    def tearDown(self): self.tmp.cleanup()

    def first(self):
        queued = self.service.request_first_store(1,'My Company','My Shop',KEY1)
        self.assertEqual('QUEUED',queued.state)
        done = self.service.fulfill_queued(queued.request_id)
        self.assertEqual('COMPLETED',done.state)
        return done

    def err(self, code, func, *args, **kwargs):
        with self.assertRaises(PolicyError) as cm:
            func(*args,**kwargs)
        self.assertEqual(code,cm.exception.code)

    def test_normalization(self):
        self.assertEqual('گالری آبی',clean_display_name('  گالری آبی  '))
        self.err('INVALID_DISPLAY_NAME',clean_display_name,'')
        self.err('INVALID_DISPLAY_NAME',clean_display_name,'\n')
        self.err('INVALID_DISPLAY_NAME',clean_display_name,'abc\x00')
        self.err('INVALID_DISPLAY_NAME',clean_display_name,'<script>')
        self.err('INVALID_DISPLAY_NAME',clean_display_name,'a'*121)

    def test_invalid_idempotency_key(self):
        self.err('INVALID_IDEMPOTENCY_KEY',self.service.request_first_store,1,'Shop','Shop','abc')

    def test_unknown_user_fails_closed(self):
        self.err('VERIFIED_ACCOUNT_REQUIRED',self.service.request_first_store,55,'Co','Shop',KEY1)
        self.verifier.identities[55]=IdentityState(True,False)
        self.err('VERIFIED_ACCOUNT_REQUIRED',self.service.request_first_store,55,'Co','Shop',KEY1)

    def test_anonymous_or_boolean_ids_not_accepted(self):
        self.err('AUTH_REQUIRED',self.service.request_first_store,0,'Co','Shop',KEY1)
        self.err('AUTH_REQUIRED',self.service.request_first_store,True,'Co','Shop',KEY1)

    def test_idempotent_request(self):
        a=self.service.request_first_store(1,' Company ',' Store ',KEY1)
        b=self.service.request_first_store(1,'Company','Store',KEY1)
        self.assertEqual(a.request_id,b.request_id)
        self.err('IDEMPOTENCY_CONFLICT',self.service.request_first_store,1,'Different','Store',KEY1)

    def test_verified_owner_first_store(self):
        result=self.first()
        self.assertEqual(OWNER_CAPABILITIES,self.service.list_capabilities(1,result.store_id))
        with self.repo.connection() as db:
            self.assertEqual(1,db.execute('SELECT COUNT(*) FROM stores').fetchone()[0])
            self.assertEqual(1,db.execute('SELECT COUNT(*) FROM audit_events').fetchone()[0])
            self.assertEqual('DRAFT',db.execute('SELECT state FROM stores').fetchone()['state'])

    def test_worker_repeat_idempotent(self):
        a=self.first()
        b=self.service.fulfill_queued(a.request_id)
        self.assertEqual(a,b)
        with self.repo.connection() as db:
            self.assertEqual(1,db.execute('SELECT COUNT(*) FROM stores').fetchone()[0])

    def test_second_first_store_blocked(self):
        self.first()
        self.err('FIRST_TENANT_ALREADY_EXISTS',self.service.request_first_store,1,'Another','Shop',KEY2)

    def test_concurrent_requests_distinct_keys_only_one_owner(self):
        a=self.service.request_first_store(1,'A','One',KEY1)
        b=self.service.request_first_store(1,'B','Two',KEY2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            fs=[pool.submit(self.service.fulfill_queued,x.request_id) for x in (a,b)]
            states=[f.result().state for f in fs]
        self.assertCountEqual(['COMPLETED','BLOCKED'],states)
        with self.repo.connection() as db:
            self.assertEqual(1,db.execute('SELECT COUNT(*) FROM tenants').fetchone()[0])
            self.assertEqual(1,db.execute('SELECT COUNT(*) FROM stores').fetchone()[0])

    def test_recheck_trust_at_worker_execution(self):
        queued=self.service.request_first_store(1,'Co','Shop',KEY1)
        self.verifier.identities[1]=IdentityState(False,True)
        self.assertEqual('BLOCKED',self.service.fulfill_queued(queued.request_id).state)
        with self.repo.connection() as db:self.assertEqual(0,db.execute('SELECT COUNT(*) FROM stores').fetchone()[0])

    def test_queued_status_hidden_from_another_user(self):
        q=self.service.request_first_store(1,'Co','Shop',KEY1)
        self.err('NOT_FOUND',self.service.status,2,q.request_id)

    def test_invite_low_risk_owner(self):
        first=self.first()
        inv,token=self.service.issue_invitation(1,first.store_id,2,['store.view','knowledge.edit'])
        self.service.accept_invitation(2,inv,token)
        self.assertEqual({'store.view','knowledge.edit'},self.service.list_capabilities(2,first.store_id))
        self.err('INVITATION_EXPIRED_OR_USED',self.service.accept_invitation,2,inv,token)

    def test_invite_wrong_user_and_token(self):
        first=self.first()
        inv,token=self.service.issue_invitation(1,first.store_id,2,['store.view'])
        self.err('INVITATION_INVALID',self.service.accept_invitation,3,inv,token)
        self.err('INVITATION_INVALID',self.service.accept_invitation,2,inv,'not-the-token')
        self.assertEqual(set(),self.err_or_empty(2,first.store_id))

    def err_or_empty(self,user,store):
        try:return self.service.list_capabilities(user,store)
        except PolicyError:return set()

    def test_high_risk_requires_owner_fresh_mfa(self):
        first=self.first()
        self.verifier.verify(1,mfa=False)
        self.err('FRESH_MFA_REQUIRED',self.service.issue_invitation,1,first.store_id,2,['conversation.read_transcript'])

    def test_high_risk_10_min_boundary(self):
        first=self.first()
        self.verifier.identities[1]=IdentityState(True,True,NOW-timedelta(minutes=10))
        inv,token=self.service.issue_invitation(1,first.store_id,2,['conversation.read_transcript'])
        self.service.accept_invitation(2,inv,token)
        self.assertIn('conversation.read_transcript',self.service.list_capabilities(2,first.store_id))

    def test_high_risk_old_mfa_denied(self):
        first=self.first()
        self.verifier.identities[1]=IdentityState(True,True,NOW-timedelta(minutes=10,seconds=1))
        self.err('FRESH_MFA_REQUIRED',self.service.issue_invitation,1,first.store_id,2,['assistant.activate'])

    def test_manager_cannot_grant_high_risk(self):
        first=self.first()
        inv,token=self.service.issue_invitation(1,first.store_id,2,['store.members.manage','store.view','knowledge.edit'])
        self.service.accept_invitation(2,inv,token)
        self.err('DELEGATION_FORBIDDEN',self.service.issue_invitation,2,first.store_id,3,['store.members.manage'])
        self.err('CANNOT_GRANT_UNHELD_CAPABILITY',self.service.issue_invitation,2,first.store_id,3,['assistant.activate'])

    def test_manager_delegates_subset_it_holds(self):
        first=self.first()
        inv,token=self.service.issue_invitation(1,first.store_id,2,['store.members.manage','store.view','knowledge.edit'])
        self.service.accept_invitation(2,inv,token)
        inv2,tok2=self.service.issue_invitation(2,first.store_id,3,['knowledge.edit'])
        self.service.accept_invitation(3,inv2,tok2)
        self.assertEqual({'knowledge.edit'},self.service.list_capabilities(3,first.store_id))

    def test_revoked_inviter_authority_blocks_pending_invite(self):
        first=self.first()
        invitation,token=self.service.issue_invitation(1,first.store_id,2,['store.members.manage','store.view'])
        self.service.accept_invitation(2,invitation,token)
        invitation2, token2=self.service.issue_invitation(2,first.store_id,3,['store.view'])
        self.service.revoke_capability(1,first.store_id,2,'store.members.manage')
        self.err('INVITER_ACCESS_REVOKED',self.service.accept_invitation,3,invitation2,token2)

    def test_cannot_revoke_owner_capabilities(self):
        first=self.first()
        self.err('OWNER_CAPABILITY_IMMUTABLE',self.service.revoke_capability,1,first.store_id,1,'assistant.activate')

    def test_foreign_store_cannot_be_managed(self):
        first=self.first()
        q=self.service.request_first_store(2,'Co Two','Shop Two',KEY2)
        second=self.service.fulfill_queued(q.request_id)
        self.err('NOT_FOUND',self.service.issue_invitation,1,second.store_id,3,['store.view'])
        self.err('NOT_FOUND',self.service.revoke_capability,2,first.store_id,1,'store.view')

    def test_database_prevents_cross_store_grant(self):
        a=self.first()
        q=self.service.request_first_store(2,'Company B','Store B',KEY2)
        b=self.service.fulfill_queued(q.request_id)
        with self.assertRaises(sqlite3.IntegrityError):
            with self.repo.transaction() as db:
                db.execute('INSERT INTO grants(tenant_id,store_id,principal_id,capability,granted_by,created_at) VALUES(?,?,?,?,?,?)',
                           (a.tenant_id,b.store_id,1,'store.view',1,NOW.isoformat()))

    def test_database_prevents_grants_without_membership(self):
        first=self.first()
        with self.assertRaises(sqlite3.IntegrityError):
            with self.repo.transaction() as db:
                db.execute('INSERT INTO grants(tenant_id,store_id,principal_id,capability,granted_by,created_at) VALUES(?,?,?,?,?,?)',
                           (first.tenant_id,first.store_id,2,'store.view',1,NOW.isoformat()))

    def test_sensitive_revoke_requires_mfa(self):
        first=self.first()
        inv,token=self.service.issue_invitation(1,first.store_id,2,['assistant.activate'])
        self.service.accept_invitation(2,inv,token)
        self.verifier.verify(1,mfa=False)
        self.err('FRESH_MFA_REQUIRED',self.service.revoke_capability,1,first.store_id,2,'assistant.activate')

    def test_reject_unknown_capability(self):
        self.err('INVALID_CAPABILITIES',canonical_caps,['become_superuser'])
        self.err('INVALID_CAPABILITIES',canonical_caps,['store.view','store.view'])


    def test_revoked_grant_does_not_get_resurrected_by_pending_invitation(self):
        first=self.first()
        inv1,tok1=self.service.issue_invitation(1,first.store_id,2,['store.view'])
        self.service.accept_invitation(2,inv1,tok1)
        inv2,tok2=self.service.issue_invitation(1,first.store_id,2,['store.view'])
        self.service.revoke_capability(1,first.store_id,2,'store.view')
        self.err('INVITATION_EXPIRED_OR_USED',self.service.accept_invitation,2,inv2,tok2)
        self.assertNotIn('store.view',self.service.list_capabilities(2,first.store_id))

    def test_queue_guardrail(self):
        self.service.request_first_store(1,'One','Shop',KEY1)
        self.service.request_first_store(1,'Two','Shop',KEY2)
        self.service.request_first_store(1,'Three','Shop',KEY3)
        self.err('ONBOARDING_QUEUE_LIMIT',self.service.request_first_store,1,'Four','Shop','D'*32)

    def test_invitation_cancelled_by_owner(self):
        first=self.first()
        inv,token=self.service.issue_invitation(1,first.store_id,2,['store.view'])
        self.service.cancel_invitation(1,inv)
        self.err('INVITATION_EXPIRED_OR_USED',self.service.accept_invitation,2,inv,token)

    def test_invitation_cancel_restricted_to_store(self):
        first=self.first()
        inv,token=self.service.issue_invitation(1,first.store_id,2,['store.view'])
        self.err('NOT_FOUND',self.service.cancel_invitation,3,inv)

    def test_invitation_expiry(self):
        first=self.first()
        inv,token=self.service.issue_invitation(1,first.store_id,2,['store.view'],ttl_hours=1)
        self.service.now=lambda:NOW+timedelta(hours=2)
        self.err('INVITATION_EXPIRED_OR_USED',self.service.accept_invitation,2,inv,token)

    def test_cannot_invite_unverified_target(self):
        first=self.first()
        self.verifier.identities[2]=IdentityState(False,True)
        self.err('VERIFIED_ACCOUNT_REQUIRED',self.service.issue_invitation,1,first.store_id,2,['store.view'])

    def test_canonical_caps_does_not_crash_on_mixed_types(self):
        self.err('INVALID_CAPABILITIES',canonical_caps,['store.view',3])

if __name__=='__main__': unittest.main()
