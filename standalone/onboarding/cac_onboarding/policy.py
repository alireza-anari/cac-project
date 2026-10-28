"""Framework-free authorization policy for first-store onboarding.

This module is executable and independently tested; it does not substitute for
PostgreSQL row-level security or verified identity-provider integration.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import hashlib
import json
import re
import unicodedata


class PolicyError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


OWNER_CAPABILITIES = frozenset({
    "store.view", "overview.read", "store.members.manage",
    "assistant.configure", "assistant.preview", "assistant.activate",
    "contact.manage", "contact.confirm", "domain.manage", "connector.manage",
    "knowledge.source.manage", "knowledge.edit", "knowledge.approve",
    "knowledge.publish", "knowledge.rollback", "knowledge.self_approve_low_risk",
    "conversation.read_metadata", "conversation.read_transcript", "subscription.read",
})

# Managers can delegate only a strict subset of rights they hold themselves.
MANAGER_DELEGABLE = frozenset({
    "store.view", "overview.read", "assistant.configure", "assistant.preview",
    "contact.manage", "knowledge.source.manage", "knowledge.edit",
    "conversation.read_metadata", "subscription.read",
})
HIGH_RISK = frozenset({
    "store.members.manage", "assistant.activate", "contact.confirm", "domain.manage",
    "connector.manage", "knowledge.approve", "knowledge.publish", "knowledge.rollback",
    "knowledge.self_approve_low_risk", "conversation.read_transcript",
})

NAME_MAX = 120
KEY_RE = re.compile(r"^[A-Za-z0-9_-]{24,128}$")


def clean_display_name(name: str) -> str:
    if not isinstance(name, str):
        raise PolicyError("INVALID_DISPLAY_NAME")
    result = unicodedata.normalize("NFKC", name).strip()
    if not (1 <= len(result) <= NAME_MAX):
        raise PolicyError("INVALID_DISPLAY_NAME")
    if any(unicodedata.category(ch)[0] == "C" for ch in result):
        raise PolicyError("INVALID_DISPLAY_NAME")
    if any(ch in "<>" for ch in result):
        raise PolicyError("INVALID_DISPLAY_NAME")
    return result


def validated_key(key: str) -> str:
    if not isinstance(key, str) or KEY_RE.fullmatch(key) is None:
        raise PolicyError("INVALID_IDEMPOTENCY_KEY")
    return key


def canonical_caps(values) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple, set, frozenset)):
        raise PolicyError("INVALID_CAPABILITIES")
    if not values or len(values) > 16 or any(not isinstance(x, str) for x in values):
        raise PolicyError("INVALID_CAPABILITIES")
    result = tuple(sorted(values))
    if len(set(result)) != len(result) or not set(result).issubset(OWNER_CAPABILITIES):
        raise PolicyError("INVALID_CAPABILITIES")
    return result


def payload_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class IdentityState:
    verified: bool
    active: bool
    mfa_authenticated_at: datetime | None = None

    def has_fresh_mfa(self, now: datetime) -> bool:
        if self.mfa_authenticated_at is None or now.tzinfo is None or self.mfa_authenticated_at.tzinfo is None:
            return False
        age = now.astimezone(timezone.utc) - self.mfa_authenticated_at.astimezone(timezone.utc)
        return timedelta(0) <= age <= timedelta(minutes=10)


def require_identity(state: IdentityState | None) -> None:
    if state is None or not state.active or not state.verified:
        raise PolicyError("VERIFIED_ACCOUNT_REQUIRED")


def can_delegate(*, is_owner: bool, actor_caps: set[str], requested: tuple[str, ...],
                 identity: IdentityState, now: datetime) -> None:
    require_identity(identity)
    requested_set = set(requested)
    if "store.members.manage" not in actor_caps:
        raise PolicyError("DELEGATION_FORBIDDEN")
    if not requested_set.issubset(actor_caps):
        raise PolicyError("CANNOT_GRANT_UNHELD_CAPABILITY")
    if not is_owner and not requested_set.issubset(MANAGER_DELEGABLE):
        raise PolicyError("DELEGATION_FORBIDDEN")
    if requested_set & HIGH_RISK and (not is_owner or not identity.has_fresh_mfa(now)):
        raise PolicyError("FRESH_MFA_REQUIRED")
