"""Contracts for the future Django/PostgreSQL integration (not wired to HTTP).

A production IdentityResolver MUST verify via a trusted IdP/server-side record,
not via fields supplied in a request body. A provisioner MUST use isolated DB
credentials; never invoke the privileged worker from an untrusted public route.
"""
from typing import Protocol
from cac_onboarding.policy import IdentityState


class IdentityResolver(Protocol):
    def resolve(self, principal_id: int) -> IdentityState | None:
        """Verify signed trusted identity/active status and MFA freshness."""
        ...


class VerifiedIdentityAdapter:
    """Fail-closed default until the production identity provider is configured."""
    def resolve(self, principal_id: int) -> IdentityState | None:
        return None
