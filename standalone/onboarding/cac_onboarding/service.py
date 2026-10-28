"""Reference onboarding command handler with durable idempotency + delegation.

Public API must NOT take verification flags from users. In production, an
identity-service adapter supplies trusted verified status (outside the request).
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import secrets
import sqlite3
from uuid import uuid4
from .policy import (OWNER_CAPABILITIES, IdentityState, PolicyError, require_identity,
                     clean_display_name, validated_key, payload_hash, canonical_caps,
                     can_delegate, HIGH_RISK, MANAGER_DELEGABLE)


@dataclass(frozen=True)
class OnboardingStatus:
    request_id: str
    state: str
    tenant_id: str | None
    store_id: str | None
    error_code: str | None


class OnboardingService:
    def __init__(self, repo, trusted_identity_resolver, now=lambda: datetime.now(timezone.utc)):
        self.repo = repo
        self.identities = trusted_identity_resolver
        self.now = now

    def _identity(self, principal_id: int) -> IdentityState:
        if type(principal_id) is not int or principal_id <= 0:
            raise PolicyError('AUTH_REQUIRED')
        state = self.identities.resolve(principal_id)
        require_identity(state)
        return state

    def request_first_store(self, principal_id: int, tenant_name: str, store_name: str,
                            idempotency_key: str) -> OnboardingStatus:
        self._identity(principal_id)
        tenant_name, store_name = clean_display_name(tenant_name), clean_display_name(store_name)
        key_digest = hashlib.sha256(validated_key(idempotency_key).encode()).hexdigest()
        digest = payload_hash({'tenant_name':tenant_name,'store_name':store_name})
        with self.repo.transaction() as db:
            existing = db.execute('SELECT * FROM requests WHERE principal_id=? AND key_digest=?',
                                  (principal_id,key_digest)).fetchone()
            if existing:
                if existing['payload_digest'] != digest:
                    raise PolicyError('IDEMPOTENCY_CONFLICT')
                return self._status(existing)
            if db.execute('SELECT 1 FROM tenants WHERE owner_principal_id=?',(principal_id,)).fetchone():
                raise PolicyError('FIRST_TENANT_ALREADY_EXISTS')
            if db.execute("SELECT count(*) FROM requests WHERE principal_id=? AND state='QUEUED'",(principal_id,)).fetchone()[0] >= 3:
                raise PolicyError('ONBOARDING_QUEUE_LIMIT')
            request_id = str(uuid4())
            db.execute('''INSERT INTO requests(id,principal_id,key_digest,payload_digest,tenant_name,store_name,
                        state,created_at) VALUES(?,?,?,?,?,?,'QUEUED',?)''',
                       (request_id,principal_id,key_digest,digest,tenant_name,store_name,self.now().isoformat()))
            return OnboardingStatus(request_id,'QUEUED',None,None,None)

    @staticmethod
    def _status(row):
        return OnboardingStatus(row['id'],row['state'],row['tenant_id'],row['store_id'],row['error_code'])

    def status(self, principal_id: int, request_id: str) -> OnboardingStatus:
        self._identity(principal_id)
        with self.repo.connection() as db:
            r=db.execute('SELECT * FROM requests WHERE id=? AND principal_id=?',
                         (request_id,principal_id)).fetchone()
            if r is None:raise PolicyError('NOT_FOUND')
            return self._status(r)

    def fulfill_queued(self, request_id: str) -> OnboardingStatus:
        """Called ONLY by trusted isolated provisioner, never by public request handler.

        Requires DB role with narrowly scoped create grants (not cac_runtime).
        """
        with self.repo.transaction() as db:
            r=db.execute('SELECT * FROM requests WHERE id=?', (request_id,)).fetchone()
            if r is None:raise PolicyError('NOT_FOUND')
            if r['state']!='QUEUED':return self._status(r)
            try:
                self._identity(r['principal_id']) # repeat trust verification at execution
            except PolicyError:
                db.execute("UPDATE requests SET state='BLOCKED', error_code='VERIFIED_ACCOUNT_REQUIRED' WHERE id=?",(request_id,))
                return self._status(db.execute('SELECT * FROM requests WHERE id=?',(request_id,)).fetchone())
            if db.execute('SELECT 1 FROM tenants WHERE owner_principal_id=?',(r['principal_id'],)).fetchone():
                db.execute("UPDATE requests SET state='BLOCKED', error_code='FIRST_TENANT_ALREADY_EXISTS' WHERE id=?", (request_id,))
                return self._status(db.execute('SELECT * FROM requests WHERE id=?',(request_id,)).fetchone())
            tenant_id,store_id = str(uuid4()),str(uuid4())
            stamp=self.now().isoformat()
            db.execute('INSERT INTO tenants VALUES(?,?,?,?)',(tenant_id,r['principal_id'],r['tenant_name'],stamp))
            db.execute('INSERT INTO stores(id,tenant_id,display_name,created_at) VALUES(?,?,?,?)',
                       (store_id,tenant_id,r['store_name'],stamp))
            db.execute('INSERT INTO memberships VALUES(?,?,1)',(tenant_id,r['principal_id']))
            db.executemany('''INSERT INTO grants(tenant_id,store_id,principal_id,capability,granted_by,created_at)
                          VALUES(?,?,?,?,?,?)''',
                           [(tenant_id,store_id,r['principal_id'],cap,r['principal_id'],stamp)
                            for cap in sorted(OWNER_CAPABILITIES)])
            db.execute("UPDATE requests SET state='COMPLETED',tenant_id=?,store_id=? WHERE id=?",
                       (tenant_id,store_id,request_id))
            self._audit(db, store_id, r['principal_id'],'FIRST_STORE_PROVISIONED',request_id)
            return self._status(db.execute('SELECT * FROM requests WHERE id=?',(request_id,)).fetchone())

    def _store_actor(self, db, principal_id: int, store_id: str):
        row=db.execute('''SELECT s.id, s.tenant_id, t.owner_principal_id FROM stores s
                          JOIN tenants t ON t.id=s.tenant_id
                          JOIN memberships m ON m.tenant_id=s.tenant_id
                          WHERE s.id=? AND m.principal_id=? AND m.is_active=1''',
                       (store_id,principal_id)).fetchone()
        if row is None:raise PolicyError('NOT_FOUND')
        caps={x['capability'] for x in db.execute('''SELECT capability FROM grants WHERE
              store_id=? AND principal_id=? AND revoked_at IS NULL''',(store_id,principal_id))}
        return row, caps, row['owner_principal_id']==principal_id

    def issue_invitation(self, actor_id: int, store_id: str, target_id: int,
                         capabilities: list[str], ttl_hours: int=24) -> tuple[str, str]:
        actor_state=self._identity(actor_id)
        if type(target_id) is not int or target_id<=0 or target_id==actor_id:
            raise PolicyError('INVALID_INVITEE')
        self._identity(target_id)  # V1: only an already-verified user can be invited
        caps=canonical_caps(capabilities)
        if not (1 <= ttl_hours <= 72):raise PolicyError('INVALID_INVITATION_TTL')
        with self.repo.transaction() as db:
            store, actor_caps, is_owner=self._store_actor(db,actor_id,store_id)
            can_delegate(is_owner=is_owner,actor_caps=actor_caps,requested=caps,
                         identity=actor_state,now=self.now())
            token=secrets.token_urlsafe(40)
            token_hash=hashlib.sha256(token.encode()).hexdigest()
            invite_id=str(uuid4())
            db.execute('''INSERT INTO invitations VALUES(?,?,?,?,?,?,?,?,NULL,NULL)''',
                       (invite_id,store['tenant_id'],store_id,target_id,actor_id,
                        json.dumps(caps),token_hash,(self.now()+timedelta(hours=ttl_hours)).isoformat()))
            self._audit(db,store_id,actor_id,'INVITATION_ISSUED',invite_id)
            # Secret returned once only; production must deliver via safe channel, never log.
            return invite_id,token

    def accept_invitation(self, actor_id: int, invitation_id: str, token: str) -> None:
        self._identity(actor_id)
        if not isinstance(token,str) or len(token)<30:raise PolicyError('INVITATION_INVALID')
        token_digest=hashlib.sha256(token.encode()).hexdigest()
        with self.repo.transaction() as db:
            inv=db.execute('SELECT * FROM invitations WHERE id=?',(invitation_id,)).fetchone()
            if inv is None or inv['target_principal_id']!=actor_id:
                raise PolicyError('INVITATION_INVALID')
            if not secrets.compare_digest(inv['token_digest'],token_digest):
                raise PolicyError('INVITATION_INVALID')
            if inv['accepted_at'] or inv['revoked_at'] or datetime.fromisoformat(inv['expires_at'])<=self.now():
                raise PolicyError('INVITATION_EXPIRED_OR_USED')
            inviter_state=self._identity(inv['inviter_principal_id'])
            _, inviter_caps, is_owner=self._store_actor(db,inv['inviter_principal_id'],inv['store_id'])
            caps=canonical_caps(json.loads(inv['caps_json']))
            # Authority must still exist at redemption. Initial step-up was checked at issue time.
            if 'store.members.manage' not in inviter_caps or not set(caps).issubset(inviter_caps):
                raise PolicyError('INVITER_ACCESS_REVOKED')
            if not is_owner and not set(caps).issubset(MANAGER_DELEGABLE):
                raise PolicyError('INVITER_ACCESS_REVOKED')
            db.execute('''INSERT OR IGNORE INTO memberships(tenant_id,principal_id,is_active)
                          VALUES(?,?,1)''',(inv['tenant_id'],actor_id))
            db.execute('''UPDATE memberships SET is_active=1 WHERE tenant_id=? AND principal_id=?''',
                       (inv['tenant_id'],actor_id))
            stamp=self.now().isoformat()
            for cap in caps:
                db.execute('''INSERT INTO grants(tenant_id,store_id,principal_id,capability,granted_by,
                              created_at) VALUES(?,?,?,?,?,?) ON CONFLICT(store_id,principal_id,capability)
                              DO UPDATE SET revoked_at=NULL,granted_by=excluded.granted_by,created_at=excluded.created_at''',
                           (inv['tenant_id'],inv['store_id'],actor_id,cap,inv['inviter_principal_id'],stamp))
            db.execute('UPDATE invitations SET accepted_at=? WHERE id=?',(stamp,invitation_id))
            self._audit(db,inv['store_id'],actor_id,'INVITATION_ACCEPTED',invitation_id)

    def cancel_invitation(self, actor_id: int, invitation_id: str) -> None:
        self._identity(actor_id)
        with self.repo.transaction() as db:
            inv=db.execute('SELECT * FROM invitations WHERE id=?',(invitation_id,)).fetchone()
            if inv is None:raise PolicyError('NOT_FOUND')
            store, actor_caps, is_owner=self._store_actor(db,actor_id,inv['store_id'])
            if not is_owner and not (actor_id==inv['inviter_principal_id'] and 'store.members.manage' in actor_caps):
                raise PolicyError('DELEGATION_FORBIDDEN')
            if inv['accepted_at'] is None and inv['revoked_at'] is None:
                db.execute('UPDATE invitations SET revoked_at=? WHERE id=?',
                           (self.now().isoformat(),invitation_id))
                self._audit(db,inv['store_id'],actor_id,'INVITATION_CANCELLED',invitation_id)

    def revoke_capability(self, actor_id: int, store_id: str, target_id: int, cap: str) -> None:
        actor_state=self._identity(actor_id)
        if cap not in OWNER_CAPABILITIES:raise PolicyError('INVALID_CAPABILITY')
        with self.repo.transaction() as db:
            store,actor_caps,is_owner=self._store_actor(db,actor_id,store_id)
            if target_id==store['owner_principal_id']:
                raise PolicyError('OWNER_CAPABILITY_IMMUTABLE')
            if 'store.members.manage' not in actor_caps:
                raise PolicyError('DELEGATION_FORBIDDEN')
            if not is_owner and (cap in HIGH_RISK or cap not in actor_caps):
                raise PolicyError('DELEGATION_FORBIDDEN')
            if cap in HIGH_RISK and not actor_state.has_fresh_mfa(self.now()):
                raise PolicyError('FRESH_MFA_REQUIRED')
            changed=db.execute('''UPDATE grants SET revoked_at=? WHERE store_id=? AND principal_id=?
                                  AND capability=? AND revoked_at IS NULL''',
                               (self.now().isoformat(),store_id,target_id,cap)).rowcount
            # Revoke pending authority even when no active grant exists yet.
            # Keep grant changes, invitation invalidation and audit in this transaction.
            pending=db.execute('''SELECT id,caps_json FROM invitations WHERE store_id=? AND
                                 target_principal_id=? AND accepted_at IS NULL AND revoked_at IS NULL''',(store_id,target_id)).fetchall()
            invitations_revoked=0
            for invite in pending:
                if cap in json.loads(invite['caps_json']):
                    invitations_revoked += db.execute('UPDATE invitations SET revoked_at=? WHERE id=?',
                               (self.now().isoformat(),invite['id'])).rowcount
            if changed or invitations_revoked:
                self._audit(db,store_id,actor_id,'CAPABILITY_REVOKED',f'{target_id}:{cap}')

    def list_capabilities(self, actor_id: int, store_id: str) -> set[str]:
        self._identity(actor_id)
        with self.repo.connection() as db:
            _,caps,_=self._store_actor(db,actor_id,store_id)
            return caps

    def _audit(self,db,store_id,actor,event,entity):
        db.execute('INSERT INTO audit_events(store_id,actor_id,event,entity_id,created_at) VALUES(?,?,?,?,?)',
                   (store_id,actor,event,entity,self.now().isoformat()))
