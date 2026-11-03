# CAC — S0-09A Architecture Review Decision

**Date:** 2026-11-03  
**Role:** Astra Management / CAC Architecture  
**Reviewed head:** `f351e26aa93ec87f17366dbaff85a87b171d36d2`  
**Reviewed PR:** [#16](https://github.com/alireza-anari/cac-project/pull/16), stacked on experimental [PR #11](https://github.com/alireza-anari/cac-project/pull/11)  
**Disposition:** `EXPERIMENT_ACCEPTED_WITH_LIMITS / PROTOCOL_PROPOSED / NEW_IMPLEMENTATION_EXPERIMENTAL / NOT_MERGED`  
**Architecture baseline gate:** [#9](https://github.com/alireza-anari/cac-project/issues/9) remains **OPEN**.  
**Historical provenance:** [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) remains **BLOCKED**.

## Executive decision

**ACCEPT the S0-09A adversarial synthetic PostgreSQL PoC as a completed, reproducible experiment.** This is **not** approval of a production-grade identity/security architecture, a v2 protocol contract, a canonical baseline, or a merge of either experimental PR into `main`.

S0-09A is isolated in `experimental/backend/context_poc/`, with newly proposed SQL scopes/roles/functions in disposable `poc` and `poc_private` schemas. Neither the existing Django model/migration nor the standalone onboarding code is integrated. The Work handoff is [context_poc/README.md](https://github.com/alireza-anari/cac-project/blob/f351e26aa93ec87f17366dbaff85a87b171d36d2/experimental/backend/context_poc/README.md); see the [full Architecture PR review](https://github.com/alireza-anari/cac-project/pull/16).

## Independent management evidence checked

- Actual final-head [push CI 41578052301](https://github.com/alireza-anari/cac-project/actions/runs/41578052301): SUCCESS, exact head `f351e26aa93ec87f17366dbaff85a87b171d36d2`.
- Actual final-head [PR synthetic-merge CI 41578057672](https://github.com/alireza-anari/cac-project/actions/runs/41578057672): SUCCESS, same PR head and synthetic merge SHA `f462cb09c31688aae587d934571629e47af82bfa`.
- Both workflows executed **43 inherited distinct tests before and after rollback/reapply** and **24 new distinct PoC PostgreSQL tests before and after PoC SQL rollback/reapply**. Each full green suite: zero FAIL/ERROR/SKIP, process exit 0. The 43 inherited include **39 real PostgreSQL cases + four configuration subprocess tests**; do not describe all 43 as SQL tests.
- Real `cac_runtime` nonowner ORM and schema/policy/role/ACL/function structural roundtrip PASS. PostgreSQL 17.11, Python 3.12.15, Django 5.2.18, psycopg 3.3.6.
- Three deliberate security weakening cases produced the **expected RED assertion failures**, controls were restored and the full tests were green. Separate historical CI RED at `58d0236966b91cd36014ebdd89b21ae3c253a424` exposed a real SQL NULL-operation-binding bypass. Fixed at `ba731e36bd3885cfe453ecfea2ce13530ecc0e7c` and passed at final head.
- Direct nonowner SQL/SET ROLE/function-EXECUTE denial, version/scope/action/target/body digest verification, signed malformed claims, cross-connection/login/transaction replay, independently committed first issuance, savepoint rollback attack, issuer concurrent scope race, timeout/deferred COMMIT, key rotation/revoke, principal/session/Store epoch, and actual `pg_blocking_pids` witnesses are covered. Real elapsed ledger retention test was 121 seconds and does **not** claim generalized disaster recovery.
- Final head changes fixed abnormal issuer connection close and a guard-lock cleanup path. CI review noted no previously reported deferred-COMMIT `ResourceWarning` in final green suite. Management did not execute an independent local PostgreSQL suite or obtain external security certification.

## Architecture boundary ruling

| Area | Accepted as proven *within the synthetic PoC* | Not approved / further required |
|---|---|---|
| Runtime trust boundary | The tested nonowner runtime cannot directly read keys/ledger, mint a token, revoke authority, disable FORCE RLS or escape Store scope through the checked attack paths. | No claim against compromised DB admin/guard/issuer, leaked valid session proof, real browser/IdP, business writes or every SQL injection payload. |
| Challenge and ledger | The tested separate DB role, signed challenge, issuer-connection COMMIT-before-return and first-issuance ledger prevent the checked same-outer-transaction scope switch and savepoint rollback bypass; failed commit does not authorize. | No final v2 format, HMAC canonicalization, key custody, isolated service process, precise retention/timing, physical recovery/failover, or distributed consistency contract ratified. |
| Session and epochs | Tested principal/session revocation invalidates context; Store-epoch mismatch demands new authenticated transaction, not in-place scope switching. | Real authentication, MFA/CSRF, revocation channel, grant model, exhaustive locks/deadlocks and retries remain separate. |
| RLS and pooling | FORCE RLS, composite Store FK, ACL and direct connection/commit/rollback reuse are demonstrated. | **Actual PgBouncer/transaction pooling and load/failover are NOT RUN.** No endorsement of a pooling contract. |
| Operations and contracts | No legacy product models, public HTTP endpoint, production credentials or onboarding integration modified. | CR/ADR decisions on signed envelope, API semantics, retention/privacy, audit/outbox, migration/upgrade and real provisioning remain open. |

### Mandatory residual architecture questions (not ratified)

1. Signed v2 field and canonical `jsonb::text` representation is PostgreSQL-version-specific; validate typed canonical bytes, duplicate-key behavior, interoperability and MAC comparison/timing before a public interface.
2. Separate HMAC challenge/context keys exist **inside** this synthetic PostgreSQL trust boundary. Production secret custody, compromise blast radius, rotation, emergency revocation and issuer process isolation remain undecided.
3. Candidate numbers (5-second issuance window, 60-second context TTL, 120-second ledger purge and 5-minute MFA freshness) are **test inputs, not product policy**. Analyze long transactions, lost-response replay and failover, exact expiry edges and revocation without relying on retry resurrection.
4. The simulated ledger is committed separately from the caller transaction, but no high-availability replication, point-in-time restore or PgBouncer proof exists. Real infrastructure must be verified separately; source code alone does not establish durability under production failure modes.
5. `SECURITY DEFINER`, owner role, `PUBLIC`, nonowner login and SQL role privileges were scoped to a new disposable schema. No product grant-write or invitation path has yet been authorized.

## Approval of next experimental slice

Authorize only [S0-09B #17](https://github.com/alireza-anari/cac-project/issues/17): independent *process* separation for issuer, actual pinned PgBouncer transaction-pool behavior, connection reset/cancellation, recovery-generation and bounded timing/lock adversarial tests, all with synthetic identities and real disposable PostgreSQL. Branch as a **stacked Draft PR on the S0-09A experimental branch**, not on `main`, preserving the 43+24 regression floor and full provenance.

Before that follow-up is reviewed, **do not integrate real IdP/MFA/CSRF, onboarding, production keys, public API, business mutations or product audit/outbox**. Those require separately approved contracts and acceptance tests.

## Governance and hard gates

- [Issue #15](https://github.com/alireza-anari/cac-project/issues/15) is completed **only as a synthetic adversarial PoC execution task**; its closure does not ratify the protocol.
- Draft [PR #16](https://github.com/alireza-anari/cac-project/pull/16) remains open/unmerged and targets the new-origin experimental branch. Draft [PR #11](https://github.com/alireza-anari/cac-project/pull/11) remains open/unmerged and unchanged.
- [Gate #9](https://github.com/alireza-anari/cac-project/issues/9) remains OPEN; `NEW_BASELINE_ACCEPTED` is **NOT GRANTED**.
- [Historical source #1](https://github.com/alireza-anari/cac-project/issues/1) remains BLOCKED. No inference of recovery of authentic v3.37/v3.38/v3.39 or compatibility with unknown historical migrations.
- `APR-033/034/035/036` remain governing and unchanged. No Sprint 0 completion, Production approval or release.

**Final ruling:** `S0-09A = EXPERIMENT_ACCEPTED_WITH_LIMITS`; `S0-09B = AUTHORIZED_FOR_SYNTHETIC_TESTING_ONLY`; `TRUSTED_CONTEXT_PROTOCOL = PROPOSED`.
