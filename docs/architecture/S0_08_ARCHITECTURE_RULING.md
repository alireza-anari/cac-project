# CAC — S0-08 Architecture Review Decision

**Date:** 2026-10-30  
**Review:** Astra Management / CAC Architecture  
**Reviewed design:** S0-08 PR #14, head `cad5e19a9351f00858da3c13b802a6125a78a30c`  
**Publication:** docs-only PR #14 merged at `b0fdfad80a7ccc470a70cf3ed855b18282dc7dda`  
**Status:** `DESIGN_RECORDED / CONDITIONAL_DIRECTION / NOT_BASELINE_ACCEPTED`

The eight S0-08 files at [docs/s0-08](../s0-08/README.md) remain proposed implementation contracts. This record documents precisely which *directions* Architecture accepts for **isolated, synthetic, test-only exploration**, and which details require additional CR decisions and adversarial proofs.

## Decisions and boundaries

| Candidate | Architecture ruling | Unresolved / not authorized |
|---|---|---|
| D-01 / ADR-08-01 | Use immutable principal identity, independently revocable server-side session, session-bound MFA evidence, real CSRF boundary and verified ownership. | No external IdP, credential/recovery provider, production authentication, final numerical timeouts or owner proof selected. 12h absolute / 30m idle / 5m step-up are **experimental candidates**, not accepted production policy. Standalone MFA was 10 minutes; compatibility change must be explicit. |
| D-02 / ADR-08-03 | Use the same PostgreSQL security domain for experimental principal/session guards; ordered locks, epoch revalidation and one outer transaction for authorized work. | No approval of split-store eventual revocation. Store epoch snapshot refresh, retry SQLSTATE and savepoint behavior remain PROPOSED until actual concurrency evidence exists. |
| D-03 / ADR-08-02 | Isolate issuer from browser/web signing keys; bind principal/session/action/scope/transaction to verified DB challenge; maintain separate challenge/context keys, strict version/kid/audience and fail-closed key revocation. | **NOT approved as a protocol:** specific v2 wire encoding, independent durable issuance ledger, challenge signature, transaction generation, anti-switch/nonce proofs, HMAC key custody and 60s timing values are candidates requiring adversarial tests and focused Architecture/security review. PostgreSQL verifier HMAC key also grants minting ability to trusted DB admins. |
| D-04 / CR-08-03 | Require least-privilege distinct nonowner app logins and NOLOGIN function owners, FORCE RLS and composite FK checks; no arbitrary DML/EXECUTE. | Exact function signatures, grants/owners, provisioner command and upgrade strategy remain PROPOSED. |
| D-05 / ADR-08-04 | Preserve SEC-REV-001 semantics: pending invites invalidated even without active grant, whole matching multi-cap invitation invalidated, new authorized invite permitted after revoke; current inviter authority at acceptance; exact target; Store serialization and atomicity. | No final capability vocabulary/delegation, newly proposed target MFA rule, encrypted delivery, schemas/routes or HTTP changes approved. |
| D-06 / CR-08-05 | Business effects, audit, idempotency and durable outbox must be atomic; no successful event for rolled-back operations. | Security-event storage, ciphertext custody, retry/erasure and audit/outbox retention need privacy/security ruling; 24h key retention is not a settled policy. |
| D-07 / CR-08-06 | Safe and non-enumerating denial is required; no unauthorized state or secret leakage. | HTTP response codes/bodies, If-Match semantics and API versioning remain pending, including CR-S0-05-001. |

## Approval for next experimental slice

A *narrow* S0-09A adversarial proof-of-concept is authorized to evaluate **synthetic authoritative identity/session guards + signed DB context and challenge design** using disposable PostgreSQL and nonowner roles. It is NOT permission to integrate real identity, MFA provider, production HMAC keys, delivery, audit/outbox, onboarding, public endpoints or existing standalone SQLite code.

Do not treat the existing `CAC-NEW-ORIGIN-S0-07` S0-07B branch as a canonical implementation. S0-09A code must be a **stacked Draft PR** based on the current experimental PR #11 head, targeting the experimental branch. Keep #11 itself Draft and unmerged.

Before a protocol choice is ratified, S0-09A must provide an adversarial test matrix proving prevention of unauthorized cross-principal, cross-scope and same-outer-transaction scope-switch attempts. Include savepoint rollback before installation, independently committed first-issuance ledger atomicity/timeout/retention, challenge origin, nonce/pid/tx generation collisions, replay, key rotation/revocation, stale session/Store epoch, direct SQL under runtime and pool reuse. If a candidate cannot meet the contract, record failure and propose a safer alternative; never weaken guards to pass.

## Hard gates

- Architecture #9 remains **OPEN** for separately named canonical baseline acceptance.
- Historical SOURCE-001 #1 / GATE-SOURCE remain **BLOCKED**.
- PR #11 remains **DRAFT / NOT_MERGED** and new code retains `NEW_IMPLEMENTATION_EXPERIMENTAL`.
- S0-08 tests are **DESIGNED / NOT_RUN**, not PASS. No product release, Sprint 0 completion or production authorization.
- All unratified details remain `PROPOSED`; Architecture will explicitly review S0-09A results, implementation interfaces and residual trust before any promotion.

**Evidence:** [PR #14](https://github.com/alireza-anari/cac-project/pull/14) review discussion; [PR #11](https://github.com/alireza-anari/cac-project/pull/11) experimental source; [Architecture gate #9](https://github.com/alireza-anari/cac-project/issues/9); [Execution #13](https://github.com/alireza-anari/cac-project/issues/13).
