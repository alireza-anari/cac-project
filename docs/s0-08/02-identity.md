# Identity, session, MFA and CSRF contract

**PROPOSED; ADR-08-01 and CR-08-01 require Architecture approval.** No IdP/provider or MFA implementation selected. Terms “verified” and “owner” must not be inferred from a client flag, email domain, widget identifier or Django staff/superuser boolean.

## Principal and authoritative state

Recommend immutable UUID principal, mapped uniquely to `(issuer, subject)` for any future external provider. Validate provider signatures, issuer/audience, nonce/state/PKCE where applicable in a separately reviewed adapter; never auto-link solely by matching email. Local-account alternative needs a separately reviewed credential and recovery policy. A verified communication channel and active principal are necessary for initial owner enrollment, but do not prove domain ownership, business authority or APR-033 contact eligibility.

Authority record proposal: principal active/verified state and epoch; server-side session handle/digest, principal FK, issued/last-auth/idle/absolute expiry, revoked time, session epoch; MFA evidence id, method/assurance, authentication time, expiry and session binding. Store ownership is an explicit protected relationship created by approved provisioning, never a claim accepted from login payload. Capability checks read current scoped state; membership alone confers none. Bootstrap identity reads use a dedicated identity adapter/role with narrow functions, not runtime tenant queries or unrestricted RLS bypass.

## Session and HTTP boundary

Use server-side revocable sessions; reject client-only signed session storage as the sole revocation authority. Proposed initial limits: absolute 12 hours, idle 30 minutes, step-up MFA age at most 5 minutes. These are Work proposals, not inherited policy; Security/Architecture approve values and methods. Authenticate and check active/verified/session expiry/epoch on every request and again at the operation gate. Do not cache a positive revocation result beyond the request/transaction. A blocked/revoked/expired session cannot be revived by a refresh token or invitation.

Cookie proposal: HTTPS, Secure, HttpOnly, SameSite=Lax, host-only (no Domain), Path=/, distinct admin name; no localStorage bearer replacement. Validate host and trusted proxy settings; trust forwarded scheme only from controlled proxy hops. Rotate session id on login and privilege step-up; invalidate old identifiers. Logout/recovery/password or MFA reset revokes affected sessions and increments epochs; scope (single/all sessions) must be explicit in the reviewed command. Recovery never grants fresh MFA by itself.

Login and every unsafe browser request require CSRF middleware/token and exact configured origin checks; no wildcard trusted origin or csrf_exempt shortcut for JSON. Cross-origin public widget credentials never authorize admin operations. GET/HEAD/OPTIONS must not mutate. SameSite and CORS are additional restrictions, not substitutes for CSRF. Browser tab store selection is a requested scope; issuer rechecks its association with the principal. An authentication failure uses generic unauthenticated denial; a CSRF failure does not reach domain mutation.

Django reference: [server-side session backends](https://docs.djangoproject.com/en/5.2/topics/http/sessions/) and [CSRF behavior](https://docs.djangoproject.com/en/5.2/ref/csrf/), checked 2026-10-30. Lifetimes, cookies and policy above are CAC proposals, not assertions that Django supplies the whole contract automatically.

## Sensitive action authorization

| Action | Proposed prerequisites beyond valid session |
|---|---|
| Scoped private read | Active membership and exact read capability; no automatic owner-by-email |
| First Tenant/Store creation | Verified principal, recent MFA, enrollment eligibility; unique provisioning intent |
| Invite lower-risk capabilities | Current members-management authority and permitted delegated subset; verified target |
| Invite/revoke high-risk capability | Current authority plus fresh session-bound MFA; nonowner cannot delegate outside reviewed manager allowlist |
| Owner transfer/deletion or last-owner change | Not part of V1 proposal; deny until a separate recovery/ownership CR exists |
| Key/issuer operation | Separate operator security domain; never ordinary store-owner privileges |

Copy exact capability classifications from the standalone policy only after review; experimental `store.view/store.manage` is not the final vocabulary. Sensitive-action MFA is checked at decision time and before mutation while locks are held. Evidence must come from trusted verification, not `mfa=true` or browser timestamp. Recommended phishing-resistant method preference is a proposal; allowed methods, fallback and recovery remain decision D-01. Boundary tests include exactly 300 seconds vs 301 seconds with controlled clock; future timestamps or evidence for another session/principal fail.

## Revocation linearization

Recommend authoritative principal/session guard rows in the same PostgreSQL security domain as action authorization. Operations hold shared locks on involved principal guards and active actor session; deactivation/session revocation obtains conflicting exclusive locks and increments epochs. Mutations also lock Store authorization guard. No validation-only transaction followed by an unlocked business transaction.

An operation that acquired valid guards first may finish before revocation commits. Once revoke/deactivation commits, no later operation may authorize with the old epoch/session. A response already computed or data already delivered cannot be recalled. Bound in-flight transaction duration; emergency incident response may terminate connections. Do not advertise instantaneous cancellation of all in-flight statements. If identity state lives elsewhere, equivalent linearization is unresolved (D-02); TTL alone is not equivalent.

Deny stale sessions before idempotency-result disclosure as well as before new mutations. Denied attempts go to a separate sanitized security event sink; successful business audit is atomic with business effects. Safe error mapping is proposed in [onboarding](05-onboarding.md), not applied to existing OpenAPI.
