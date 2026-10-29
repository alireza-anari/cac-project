# NEW_IMPLEMENTATION_EXPERIMENTAL — contract inventory and proposed design

Source identity: CAC-NEW-ORIGIN-S0-07. Issue #10 execution; Issue #9 permits continued isolated experimentation; canonical baseline acceptance remains blocked. Historical SOURCE-001 remains BLOCKED. No legacy source is reconstructed.

## Definite requirements from available summaries

APR-033 verified qualifying contact before public Live; APR-034 one public Live assistant per Store; APR-035 confirmed final-contact loss pauses public access; APR-036 existing architecture approval is unchanged. None of these authorizes new public endpoints in this prototype.
Tenant/store isolation, composite FKs, ENABLE/FORCE RLS, nonowner runtime without BYPASSRLS, separate provisioner, and transaction-local trusted identity are required by docs/cac/03. GUC alone is explicitly insufficient against SQL injection.

## PROPOSED — not an approved frozen contract

- Django 5.2 LTS modular skeleton, PostgreSQL 17, no HTTP endpoints/DRF/admin/auth implementation.
- UUID Tenant/Store/Membership/ScopedGrant. External principal UUID is a test identity reference, not Django auth or verified IdP integration. Membership.active gates access; capabilities are a minimal experimental allowlist (store.view/store.manage), not final product vocabulary.
- Runtime SELECT only; it can see its active membership and own grants in exactly one tenant/store. Provisioner SELECT/INSERT only for bootstrap scope; no UPDATE/DELETE, role membership, schema ownership, DDL, TRUNCATE or key access. This does not implement invitations or ongoing membership administration.
- Signed JSON context binds principal, tenant, store, purpose, expiry, transaction ID and backend PID. A test-only trusted issuer signs HMAC-SHA256; DB verifies using an inaccessible key table. Runtime cannot mint valid contexts by changing custom settings. Real issuer authentication/MFA, key custody/rotation, revocation/session lifecycle and pooling integration remain open.
- Provisioner purpose grants initial own-principal membership/grants within an issuer-approved scope; full atomic/idempotent onboarding is not integrated.

## CR-S0-07-001 — PROPOSED / NOT APPROVED

Requester Work; approver CAC Architecture via #9. Schema diff: four new experimental tables, composite FK/unique constraints, active membership, two capability values and RLS roles/context function (see models and migrations). API diff: no endpoints; new internal DB/context interface only. Historical schema comparison is impossible without SOURCE-001 bytes.
Security impact: separates login privileges and prevents unsigned SQL-context spoofing; trusted issuer/migration superuser remain powerful boundaries. Compatibility with missing Freeze and legacy schemas is unknown. Rejected alternatives: trusting unsigned GUC, shared owner/runtime account, treating SQLite behavior as PostgreSQL evidence.
Acceptance proposal: nonowner isolation and role denial tests, context forgery/expiry/replay tests, constraint SQLSTATEs, rollback/reapply equality, review of key/issuer threat model, and Architecture signoff before any baseline promotion. This CR is implemented only as the user-authorized experiment, not approved for main/product use.

## S0-07B hardening — #12

No model, HTTP API, migration graph or business capability semantics changed. Existing role/context authorization rules are retained. The following fixes enforce their intended boundaries:

- `cac_owner` default function EXECUTE privileges revoke PUBLIC **globally within the current disposable database**, for future functions created by that role in any schema. This does not change defaults for other creators/databases, nor retroactively change existing functions. `verified_context()` continues its explicit PUBLIC revoke and explicit runtime/provisioner grants. Future functions need explicit grants. Fresh bootstrap only; no existing environment is silently upgraded.
- `CAC_DJANGO_SECRET` is required unless `CAC_EXPERIMENTAL_DISPOSABLE` is exactly `1`; missing/empty key otherwise raises ImproperlyConfigured. The fixed synthetic fallback is restricted to explicit disposable execution. Supplying a key does not authorize deployment or establish identity/session security.
- Direct cross-principal grant denial, signed missing/null/malformed claims, expiry limit, PUBLIC verifier ACL, future-function default ACL and startup configuration now have regressions. No unsigned-context or tenant/store assertion was weakened.

See [S0-07B handoff](../../../docs/S0_07B_HANDOFF.md) for exact implementation/tested commit and evidence. The final-head receipt in [Issue #12](https://github.com/alireza-anari/cac-project/issues/12) records both push and synthetic-merge SHAs/runs after the documentation commit (avoiding a self-referential commit SHA). Architecture #9 approves experiments only; canonical baseline, historical source and product gates remain blocked. All issuer/key, MFA/CSRF/session revocation, pooling, provisioning/audit and concurrency decisions above remain PROPOSED/unimplemented.
