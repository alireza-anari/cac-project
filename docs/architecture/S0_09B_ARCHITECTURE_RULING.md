# S0-09B Architecture Review Decision

**Date:** 2026-11-03  
**Role:** Astra Management / CAC Architecture  
**Reviewed PR:** [#18](https://github.com/alireza-anari/cac-project/pull/18)  
**Reviewed head:** `75be54d0f18d6391014ca4e5d91466d62a6cf72c`  
**Base branch/head:** `work/s0-09a-trusted-context-poc` / `f351e26aa93ec87f17366dbaff85a87b171d36d2`  
**Synthetic merge:** `be0e564e2390f8824506809858ad8782260ffb59` (parents are exactly the base and reviewed head)  
**Disposition:** `EXPERIMENT_ACCEPTED_WITH_LIMITS / PROTOCOL_PROPOSED / NEW_IMPLEMENTATION_EXPERIMENTAL / NOT_MERGED`  
**Architecture Gate:** [#9](https://github.com/alireza-anari/cac-project/issues/9) remains **OPEN**.  
**Historical provenance:** [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) remains **BLOCKED**.

## Executive decision

**Accept S0-09B as a completed synthetic process-isolation / PgBouncer transaction-pool / bounded recovery experiment. Do not ratify the trusted-context protocol, recovery contract, key custody, production timing policy, canonical v2 wire format or merge.**

The exact final PR head is eight commits ahead of the S0-09A parent, changes 19 files (1,433 additions / 3 deletions), and is correctly stacked as Draft on the S0-09A experimental branch. PR #18 is open, Draft and unmerged. PRs #16 and #11 remain open, Draft and unmerged at their previously approved heads.

The implementation is isolated under `experimental/backend/pool_recovery/`. No inherited Django model, migration, product SQL, public endpoint, onboarding flow, business mutation, real identity, customer data or production secret was integrated.

## Management evidence checked

### Exact-head CI
- Full Push [41584962736](https://github.com/alireza-anari/cac-project/actions/runs/41584962736): SUCCESS, head `75be54d0f18d6391014ca4e5d91466d62a6cf72c`.
- Full PR synthetic-merge [41584967557](https://github.com/alireza-anari/cac-project/actions/runs/41584967557): SUCCESS, PR head `75be54d0f18d6391014ca4e5d91466d62a6cf72c`; synthetic merge `be0e564e2390f8824506809858ad8782260ffb59`, with exact parent and head SHAs.
- Supplemental focused Push [41584962878](https://github.com/alireza-anari/cac-project/actions/runs/41584962878) and PR [41584967696](https://github.com/alireza-anari/cac-project/actions/runs/41584967696): both SUCCESS on the same exact head. These 27-case focused runs supplement, not replace, the full 94-case runs.
- Both full runs have one completed `postgres-security` job and every step succeeded, including the full retained floor, PgBouncer install, S0-09B run, credential scan and evidence upload. Management inspected the decoded job logs and test summaries.
- The two full runs each execute **94 distinct cases** before and after rollback/reapply: 43 inherited foundation cases (39 PostgreSQL + 4 configuration subprocess), 24 inherited S0-09A PostgreSQL cases, and 27 new S0-09B cases (8 process, 9 pool/lock, 3 recovery, 7 timing/encoding). Each green suite is zero failure/error/skip and exit 0. Repeated executions are not additional distinct cases.
- Three deliberate security-predicate weakening mutations produced expected assertion RED; exact SQL was restored. A separate deliberately stale `pg_stat_activity` observer produced its expected assertion RED. The full suites then passed. Earlier startup, EOF, public-bootstrap credential and cached-observer failures are retained transparently in the handoff; they were not relabeled as green.
- Versions observed in CI: PostgreSQL 17.11, PgBouncer 1.22.0 (Ubuntu package `1.22.0-1build4`), Python 3.12.15, Django 5.2.18, psycopg 3.3.6.
- Full-run evidence artifacts are present and unexpired: Push artifact [13206929600](https://github.com/alireza-anari/cac-project/actions/runs/41584962736/artifacts/13206929600), PR artifact [13207029521](https://github.com/alireza-anari/cac-project/actions/runs/41584967557/artifacts/13207029521). PR metadata records SHA-256 verification and tested SHA receipts.
- Management reviewed source, workflow and CI logs; did **not** perform a separate local PostgreSQL/PgBouncer rerun or obtain an external security certification. Earlier independent review was static and at a prior candidate SHA, not a final independent security audit of this exact head.

## Evidence accepted within the experiment boundary

### 1. Issuer / runtime process separation
Three distinct unprivileged Linux UIDs are used for issuer (62001), runtime (62002) and PgBouncer (62003). The lab uses individual mode-0600 role credential files, scrubbed child environments, root-owned read-only entrypoints, a root-prebound Unix socket and Linux `SO_PEERCRED` peer checks. Issuer uses only the `cac_ctx_issuer` database login and commits/closes its independent DB transaction before returning a token. Runtime uses only its own DB login and the actual PgBouncer TCP endpoint.

The test reproduced and corrected a real bypass caused by the known public disposable bootstrap administrator password; the fixture admin password is now randomized before adversarial processes start. EOF truncation is explicitly rejected. Malformed, duplicate, oversized and wrong-scope RPC requests fail closed; issuer outage and deferred COMMIT failure do not fall back or return an uncommitted token.

**Bound:** this proves a narrow same-host Linux UID/file/proc/socket boundary under the CI threat model. It does not protect against host root/ptrace compromise, same-UID runtime compromise, valid bearer-proof theft, a compromised DB administrator, production service orchestration or general admission/DoS. A per-UID local socket is not a production identity proof.

### 2. Actual PgBouncer transaction pooling
Actual pinned PgBouncer 1.22.0 runs in transaction mode with one- and four-backend pools. The tests witness `session_user`, `current_user`, backend PID and transaction ID; demonstrate backend PID reuse with a different transaction ID; deliberately leak session-level context; and exercise rollback, savepoint, SQL error, backend cancellation, deadlock, lock timeout, four simultaneous Store scopes, and concurrent revocation/issuance schedules.

**Bound:** only this pinned package, local CI topology, SCRAM login, default READ COMMITTED and bounded schedules were tested. This is not a deployment-version recommendation or proof for prepared statements, protocol-level CancelRequest forwarding, session/statement pooling, multi-host/TLS, network partition, rolling upgrades, high isolation levels or general load.

### 3. Timing and encoding probes
Exact database predicate boundaries are tested using controlled replacement of the target SQL function clock, with exact original definitions restored. Separate elapsed tests use the real clock for token expiry and MFA becoming stale after issuance. Typed PostgreSQL/Python encoding examples show that naive Python JSON serialization differs for at least one vector; Python verifies the MAC over exact PostgreSQL bytes for the examples.

**Bound:** test values 5s / 60s / 120s / 300s are not product policy. No latency/revocation SLA, canonical cross-language wire format, duplicate/numeric interoperability standard, or constant-time SQL MAC comparison has been approved.

### 4. Restart and logical restore
A controlled Docker PostgreSQL restart preserves committed ledger rows and kills the old transaction. A logical schema/data restore into another disposable database on the same PostgreSQL cluster was also executed.

**Critical observed failure:** restoring keys, generation and ledger together preserved the Issuer's ability to return the same old ledger response while the original challenge remained valid. A manually applied generation change rejected old authority, but **the experiment delivers no automatic durable external generation fence, recovery coordinator, startup/readiness gate or split-brain prevention**. Clone-token rejection also depends on PID/xid binding; the handoff correctly distinguishes this from the separately tested live-transaction generation check.

This is a real P0 integration blocker, not a passing recovery design. The same-cluster logical clone retained cluster roles and is not a fresh-cluster bootstrap proof. No physical PITR, replica promotion, crash-at-WAL-commit, HA failover, RPO/RTO or split-brain recovery was demonstrated.

## Mandatory unresolved P0 gates

1. **Restore fencing:** a monotonic generation authority outside the database backup/restore failure domain; atomic single-authority activation; fencing before readiness; stale-primary and restored-candidate mutual exclusion; fail-closed behavior when the anchor is unavailable, stale or partitioned. Startup-only checking is insufficient unless a bounded lease protocol is formally specified and proven.
2. **Key custody:** keys currently remain inside the PostgreSQL guard boundary. External custody, backup confidentiality, rotation, revocation, compromise blast radius and separation from DB admin/issuer remain open.
3. **Bearer proof theft:** a valid stolen proof can request its own authorized scope. Real session identity, proof delivery and theft response are not addressed by UID separation.
4. **Signed protocol:** PostgreSQL `jsonb::text` bytes are server-specific; canonical typed bytes, cross-language vectors, versioning, duplicate/numeric semantics and constant-time MAC verification remain unapproved.
5. **Disaster recovery:** no physical PITR, replica promotion, independent HA authority or split-brain protocol has been proven.

## Residual P1 risks

- Verifier SHARE locks can delay revocation while a transaction remains active; already returned reads cannot be retroactively undone.
- No general admission/rate-limit/DoS bound for issuer threads or runtime service; the socket timeout is not a complete deployment admission policy.
- Only bounded local concurrency and READ COMMITTED are exercised.
- PgBouncer 1.22.0 is a fixed experimental target, not a recommended production package.
- Protocol-level cancellation, packet loss, lost response/idempotency, pool exhaustion, network partition, TLS and prepared statement compatibility are incomplete.
- Exact frozen-clock edges do not establish microsecond scheduling or production clock authority.

## Governance

- [Issue #17](https://github.com/alireza-anari/cac-project/issues/17) is completed and may be closed **only as a synthetic experiment/handoff**; closure does not ratify the protocol.
- [PR #18](https://github.com/alireza-anari/cac-project/pull/18) remains open, Draft, stacked and unmerged. Do not merge or promote it.
- [PR #16](https://github.com/alireza-anari/cac-project/pull/16) and [PR #11](https://github.com/alireza-anari/cac-project/pull/11) remain unchanged, Draft and unmerged.
- [S0-09C Issue #19](https://github.com/alireza-anari/cac-project/issues/19) is authorized for **synthetic recovery generation fencing and split-brain proof only**, stacked on PR #18. It must prove that restored and stale instances cannot both authorize and that loss of the independent anchor fails closed.
- Architecture [Gate #9](https://github.com/alireza-anari/cac-project/issues/9) remains **OPEN**; no `NEW_BASELINE_ACCEPTED`.
- Historical [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) and `GATE-SOURCE` remain **BLOCKED**. No historical v3.37/v3.38/v3.39 recovery is inferred.
- `APR-033/034/035/036` remain unchanged. No Sprint 0 completion, Production approval or product integration.

**Final ruling:** `S0-09B = EXPERIMENT_ACCEPTED_WITH_LIMITS`; `S0-09C = AUTHORIZED_FOR_SYNTHETIC_RECOVERY_FENCING_ONLY`; `TRUSTED_CONTEXT_PROTOCOL = PROPOSED`.
