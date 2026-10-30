# ADR/CR candidates, dependencies and S0-09 proposal

**All entries PROPOSED / NOT APPROVED / NOT IMPLEMENTED.** Decision authority: CAC Architecture through #9; Management prioritizes; Work implements only a separately authorized reviewed scope. This document does not amend APR-033/034/035/036 or pending CR-S0-05-001.

## Review decisions and explicit compatibility diffs

| Decision / candidate | Recommended proposal vs alternative | API/DB/security impact, compatibility and required proof |
|---|---|---|
| D-01 / ADR-08-01 / CR-08-01 | Server-side revocable session + immutable principal; isolated identity adapter vs browser-signed standalone session | New principal/session/MFA epoch records, 12h absolute/30m idle/5m step-up proposed; provider/method/recovery/owner proof need decision. Integer standalone IDs cannot be assumed UUID identity. ID tests + AUTH-RACE; rollout with new schema/version, no legacy identity import until mapping review |
| D-02 / ADR-08-03 / CR-08-03 | Authoritative identity guards in same PostgreSQL security domain; explicit transactions and coarse Store guard vs remote eventual revocation | New guards/epochs and lock order; effective Store mutations increment epoch, with bounded authenticated PZ001 snapshot refresh distinct from hard actor/session denial; bounded in-flight completion, not instantaneous cancel. If remote identity chosen, present atomicity model invalid until redesigned. POOL/AUTH-RACE tests; rollback must not resurrect epochs/sessions |
| D-03 / ADR-08-02 / CR-08-02 | Isolated issuer + DB-authenticated challenge, HMAC initially vs colocated signer/asymmetric extension | v1 seven claims/single key/300s -> v2 explicit kid/version/audience/epochs/action/challenge, 60s proposed. Approve the recommended separate HMAC challenge key, protected transaction-binding registry and independently committed first-issuance ledger/window (savepoint rollback defense), or specify an alternative with equivalent proof, plus key custody and rotation before coding. No implicit compatibility or downgrade. CTX tests; staged v2 separate verifier, retire v1 before integration; emergency revoke/generation rotation on rollback |
| D-04 / CR-08-03 | Narrow named onboarding commands with nonowner NOLOGIN function owner vs broad provisioner DML | New login/function roles, EXECUTE/RLS matrix. Current provisioner only permits own-principal insert; actor≠target only via approved command. Explicit function signatures and policies must be reviewed before implementation; DB-01..04, scope tests and rollback ACL snapshot |
| D-05 / ADR-08-04 / CR-08-04 | Store guard serializes issue/accept/revoke; preserve whole multi-cap invite invalidation and fresh post-revoke invitations | New invitation/grant lifecycle, protected owner mapping; target MFA on high-risk accept and no returned raw token are changes from standalone. Decide vocabulary/delegability, first-store eligibility, TTL, lock timing and encrypted delivery; ONB + eight races. No bulk conversion or destructive schema migration without real mapping/diff |
| D-06 / CR-08-05 | Transactional audit/outbox/idempotency with at-least-once dispatch vs non-durable on_commit-only callback | New tables, unique keys, leases, scoped audit sequence; retention/PII/security-event policy and delivery custody unresolved. Proposed 24h key retention not enough alone for permanent business dedupe; AUD tests. Data-preserving rollback/export/erasure plan required before live use |
| D-07 / CR-08-06 linked CR-S0-05-001 | Uniform safe-denial HTTP mapping; If-Match/version and idempotency semantics | Existing standalone OpenAPI not edited. Propose 401/403/400/404/409/412/429/503 distinctions; determine route/status/body/version compatibility before client changes. Contract lint + HTTP identity/CSRF/invite negative tests; versioned API rollout, not reinterpretation of SQLite exceptions |

For each CR approval record, Architecture must supply: accepted/rejected option, exact contract/schema/API version, effective scope, migration and backout strategy, security owner, required tests and accepted residual risks. Silence, a Draft PR or successful experiment is not approval. A rollback that re-enables stale signing keys or revoked identities is forbidden even if it restores old application code. Safe fallback is fail-closed maintenance, not old unsigned context.

## Unknowns that prevent direct integration

Historical v3.37/v3.38/v3.39 model/API/migration bytes remain missing; cannot assert compatibility. PR #11 is unmerged and has no auth sessions/IdP, owner relationship, invitations, durable audit/outbox or revocable grant timestamps. Standalone uses SQLite and different principal/membership/capability schemas. Existing HMAC key is synthetic and private DB row is not production key custody. A future default Django auth migration, roles, new claim format, RLS functions and API generation each require approved diffs. `store.manage` does not equal standalone `store.members.manage`. No proposed function owner or new login may be created by merely editing current role SQL before review.

## Risk register

| ID | Priority | Impact / dependency | Mitigation and owner / closure proof |
|---|---|---|---|
| R-01 | P0 | Unapproved canonical baseline and missing historical source | Management supplies provenance; Architecture separate baseline decision. SOURCE-001 stays BLOCKED regardless of new code |
| R-02 | P0 | Issuer/web confused deputy or signing-key compromise grants authority | Security owns D-01/D-03; isolate checks/custody, malicious-worker tests and incident drill. Web session theft and DB admin trust remain residual |
| R-03 | P0 | Split identity stores break revoke linearization | Architecture chooses D-02; lock/epoch proof before coding; distributed alternative needs new contract |
| R-04 | P0 | Broad SECURITY DEFINER/provisioner permissions bypass scope | Security reviews D-04; explicit creator/role ownership/search_path and direct-SQL negative tests |
| R-05 | P0 | Invitation grant resurrects after revoke or stale inviter authority | Work implements only approved guard model; all eight schedules + AUTH-RACE + ONB-06 with lock witnesses |
| R-06 | P0 | Pool/session context leaks or fails after failover | Infrastructure + Work pin configuration and test all selected modes; generation invalidation; discard dirty connections |
| R-07 | P1 | Audit/outbox loss, secret disclosure or unauthorized replay | Security/Privacy approve D-06; atomic fault injection, log scan, encrypted-delivery erasure and worker ACL tests |
| R-08 | P1 | Lock contention/issuer latency causes outages | Bound deadlines/retries; benchmark coarse guards after correctness, never remove serialization just for speed |
| R-09 | P1 | Error/constraint timing leaks target existence | D-07 safe mapping, rate limiting and authorized response equivalence tests; RLS alone cannot hide all FK timing |
| R-10 | P1 | MFA recovery, account linking or owner transfer bypasses authority | Security chooses allowed methods/recovery; deny undefined transitions; no guessed IdP flow |
| R-11 | P2 | Evidence expires or toolchain/pool drifts | Pin execution versions, retain sanitized commit-linked proof, dependency review; plans never substituted for rerun |

## Proposed S0-09, conditional implementation sequence

No code starts until the relevant ADR/CR rows are explicitly accepted and Management authorizes the exact slice. Suggested sequence:

1. **P0 contract ratification:** resolve D-01..04 trust/storage/challenge/role choices and D-05 delegation/locking semantics; Security threat review. Keep baseline promotion separate.
2. **P0 test-only identity/context adapter:** new branch/PR based on the then-authorized experimental source, synthetic authoritative sessions only; implement approved versioned envelope/challenge, epoch checks and explicit transaction adapter. No live IdP, external key service or public endpoint. Require ID/CTX/DB/POOL-negative tests and migration rollback evidence.
3. **P0 pooling and revocation proof:** independent-connection reuse/failure/epoch cases; direct/session mode first, transaction pool only once pinned/approved. Test actor/session deactivation linearization and failover generation.
4. **P1 onboarding service slice:** only after D-05..07 approval, new schema/command interfaces + atomic audit/outbox/idempotency using in-memory/local test delivery adapter; map standalone behavior, execute eight PostgreSQL races. Do not import standalone SQLite storage or expose HTTP by default.
5. **Separate future mission:** real IdP/MFA assurance, production custody, public admin endpoints, provider delivery and operational readiness require their own contracts/authorization; not included in proposed S0-09 automatically.

Exit of any S0-09 slice: reviewed diff and explicit source identity, real nonowner PostgreSQL negative evidence on final head/synthetic merge, actual rollback/cleanup proof, no unresolved P0 within slice, documented excluded gates and Draft PR for review. It does not clear historical SOURCE, approve product release or complete Sprint 0 by itself.
