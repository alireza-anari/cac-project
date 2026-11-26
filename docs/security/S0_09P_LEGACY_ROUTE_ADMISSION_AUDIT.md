# S0-09P — executable legacy-route admission audit

Authority: [Issue #55](https://github.com/alireza-anari/cac-project/issues/55).
Exact K base: `9e768a4d1f6c97c429c36475237e132b8e3e7fc2`.
Branch: `work/s0-09p-legacy-route-audit`, stacked on K PR #46's
`work/s0-09k-policy-retirement-experiment`, not on the M/N/O lane.

`NEW_IMPLEMENTATION_EXPERIMENTAL / ORIGINAL_NONRESTORED_CURRENT_3_OF_5_R_MAJORITY_ONLY / TRUSTED_MANDATORY_CURRENT_GUARD / NO_PRODUCTION`.

This document freezes source provenance and the finite execution plan before
sampling. It does not assert an observed PASS. Final actual case receipts,
immutable SHA, CI/artifact links and independent reviews belong in Issue #55.
Keeping that evidence ledger there avoids extra pushes and outcome-driven
repetitions of the six frozen observations.

## 1. Exact-source route provenance

All links below identify the immutable K source, before any P diagnostic.

| Real route | Exact source and enforcement | Inventory status / coverage limit |
|---|---|---|
| Original Unix issuer | [pool_recovery/issuer.py:28](https://github.com/alireza-anari/cac-project/blob/9e768a4d1f6c97c429c36475237e132b8e3e7fc2/experimental/backend/pool_recovery/issuer.py#L28): `serve`  to  `handle`, SO_PEERCRED and request validation  to  real `cac_ctx_issuer` login  to  `poc.issue`  to  commit-before-response | AVAILABLE/EXECUTABLE. Has no policy field or Root ticket. Already fenced by K's mandatory guard even at policy1. Its denial alone does not prove retirement newly disabled an otherwise functional K legacy client. |
| Current coordinator issuer/runtime | [h_quorum/broker.py:59](https://github.com/alireza-anari/cac-project/blob/9e768a4d1f6c97c429c36475237e132b8e3e7fc2/experimental/backend/h_quorum/broker.py#L59) and `Gate` at64: exact SID/PID/fullxid, action/body digest, durable Root ADMIT/first_use, transaction-local ticket/intent, SQL final guard, local ACK then authoritative close | AVAILABLE/EXECUTABLE. Separate explicit new policy1 ADMIT negative after real policy2 cut; current-generation signed SQL positive. |
| Protected direct PostgreSQL | [context_poc/sql/001_up.sql:16](https://github.com/alireza-anari/cac-project/blob/9e768a4d1f6c97c429c36475237e132b8e3e7fc2/experimental/backend/context_poc/sql/001_up.sql#L16): `poc.records`, owner `cac_ctx_owner`, ENABLE/FORCE RLS. [h_quorum/sql/guard.sql:82](https://github.com/alireza-anari/cac-project/blob/9e768a4d1f6c97c429c36475237e132b8e3e7fc2/experimental/backend/h_quorum/sql/guard.sql#L82) replaces read policy with `h_guard.scope` and guarded write policy | AVAILABLE/EXECUTABLE via actual runtime/issuer logins and listener5432. Other application relations or hypothetical web/API entrypoints are NOT_RUN, not assumed protected. |
| Public legacy SQL helpers | `poc.verify`, `poc.read_scope`, `poc.authorize`; original functions remain in the same K database, routed through the current wrappers | AVAILABLE/EXECUTABLE subpaths of direct-SQL case. Actual stale execution required, not an inferred ACL denial. |
| Internal old SQL functions | [guard.sql:53–62](https://github.com/alireza-anari/cac-project/blob/9e768a4d1f6c97c429c36475237e132b8e3e7fc2/experimental/backend/h_quorum/sql/guard.sql#L53) relocates/revokes `issue_c`, `verify_c`, legacy checker and unfenced private helpers | PRESENT/ACL-RESTRICTED. Execute `h_guard.issue_c` as actual issuer; inventory other private function privileges. Not permission to simulate an old guard owner. |
| Real transaction pool | [recovery_proof/pool_lab.py:36](https://github.com/alireza-anari/cac-project/blob/9e768a4d1f6c97c429c36475237e132b8e3e7fc2/experimental/backend/recovery_proof/pool_lab.py#L36): PgBouncer port6544, transaction mode, size1, runtime login. `server_reset_query_always=0` at41 | AVAILABLE/EXECUTABLE. Persistent session values are intentionally possible. Prove old authorization cannot leak; do not claim DISCARD ALL runs after every transaction. |
| Separate policy-v1-only SQL login | K's role definitions encode policy in Root/config/binding, not a fabricated role called “legacy runtime” | NOT_APPLICABLE as a separate invented route. Existing real roles are inventoried and named. |
| Privileged ownership/maintenance | `postgres`, NOLOGIN `cac_ctx_owner`/`cac_ctx_guard`, `cac_ctx_identity`, `cac_fence_activator`, anchor/statistics roles | Live flags, memberships, SECURITY DEFINER owners/search_path and private execution ACLs inventoried. Runtime/issuer execution tested; arbitrary DBA/owner/identity administration is OUT_OF_SCOPE/NOT_RUN. No privileged role or grants are added. |
| Coherent old guard/verifier or R-majority restoration | No independent trust/custody proof in this authorization | NOT_RUN / missing independent primitive. Current guard remains mandatory on every claimed tested protected path. No global fail-closed claim. |

`h_guard.require` at [guard.sql:29](https://github.com/alireza-anari/cac-project/blob/9e768a4d1f6c97c429c36475237e132b8e3e7fc2/experimental/backend/h_quorum/sql/guard.sql#L29)
measures the live catalog, uses the authenticated checker and signed online
Root answer/reverification, binds role/SID/PID/fullxid/nonce/intent/ticket and
policy. [policy.py:8](https://github.com/alireza-anari/cac-project/blob/9e768a4d1f6c97c429c36475237e132b8e3e7fc2/experimental/backend/h_quorum/policy.py#L8)
allows only exact previously granted historical OPEN continuation.
`retirement.retire_policy` changes real policy1 to 2 through Root CAS/journal;
`adopt_policy` at31 refuses retired unresolved operations and validates current
catalog/ACL before trusted configuration adoption. Neither signer rotation,
session death nor elapsed time is a substitute for that transition.

## 2. Fixed executable plan

Only new `h_quorum/p_audit.py`, `p_issuer_worker.py`, `p_tests.py`, `p_run.py`,
`p_evidence.py` and `p_evidence_tests.py`,
one scoped workflow and this document are proposed. All inherited implementation,
H/K tests, SQL/guards/consensus, M/N/O, Preview, main and canonical APRs remain
byte-for-byte unchanged. Three distinct integration methods, one original
observation per case per final-head Push and PR: six total. No skipped method,
outcome-driven rerun or fourth case. H51 and K17 regressions run separately;
other inherited applicable workflows retain their original cohorts.
Two local snapshot-serializer unit methods are not extra route observations.

| Frozen case | Actual measured negative | Positive and state interpretation |
|---|---|---|
| `P_STALE_ISSUER_POLICY_AFTER_RETIREMENT` | Start actual original Unix issuer with issuer-only config. After real retirement and adoption, create a fresh current runtime challenge with no ledger entry; old socket request reaches original SQL and must return denial/42501 through `h_guard.require`, ledger remains0. Explicit new policy1 Root ADMIT separately denied. | On that same fresh challenge, current original issuer Gate must issue successfully, ledger becomes1 and scoped data succeeds. Earlier policy1 granted OPEN is separately allowed to continue, and closes only after real COMMIT ACK/CLOSE. Never conflate a historical token reissue with the fresh negative. |
| `P_DIRECT_SQL_OLD_PRINCIPAL` | Real non-superuser runtime connects directly; unexpired signed old context and old ticket/intent under new fullxid cannot authorize SELECT. Execute actual public old SQL helpers and issuer's private old-function call; distinguish guard denial from private ACL denial. | Current real P1 to S1 and P2 to S3 signed scopes succeed; other store/tenant SELECT returns zero rows and cross-tenant UPDATE affects zero. Live owner/RLS/role/grant facts are recorded. No arbitrary privileged execution claim. |
| `P_POOL_REUSED_BACKEND_OLD_CONTEXT` | Real size1 pool: persist all three actual session settings, retain the same backend PID with a new fullxid after retirement, require unexpired old token; raw inherited-state SQL and explicit old SET LOCAL replay both denied by current guard. | Fresh current P1 and P2 transactions on that same backend see only their store. Historical pregrant has real COMMIT ACK and authoritative CLOSE; successor reservation is denied while OPEN and before CLOSE. A later actual SQL error yields inherited genuine UNKNOWN; inferred abort and successor remain denied. No forced abort or orphan reconciliation. |

### Original issuer observation seam

The worker calls the unchanged `pool_recovery.issuer.serve`. A Python thread
trace at its exact original `c.execute('SELECT poc.issue...')` source line
reads that original connection's real user/PID/fullxid/system ID and challenge
age; the original SQL statement, parser, SO_PEERCRED and response still execute.
The trace never supplies a ticket, changes a role, wraps a DB call or replaces
an RPC/guard result. Original SQL exception is observed with safe allowlisted
function names and42501; raw args, proofs, context and stderr are never printed.
The worker starts before the fresh five-second challenge. Its source hash,
call line and live challenge PID/fullxid/age must be witnessed. Missing traces,
expired challenge or an unreproduced path are INCONCLUSIVE, not PASS.
This same-runner-UID process does not prove independent OS/key/operator custody.

### Quorum and evidence

Each P job has independent disposable five-process pinned etcd3.6.16 and three
PostgreSQL containers. Original r4/r5 stop without membership changes, leaving
only original nonrestored r1/r2/r3. Their IDs/PIDs/data directories, membership,
authenticated local full Root/state revision and complete ordered journal are
checked before/after cases. Intended retirement/admission/close transitions
are recorded; denied actions compare full Root/journal equal, not just counts.
Full tuples are read/compared in memory. Safe logs preserve full state field
coverage and every decoded ordered journal row with its original key/revision/
version/lease metadata, raw value digest and exact original full-tuple digest.
Only bearer/credential-named fields are replaced by SHA256+byte-length markers;
an explicit path manifest accounts for every replacement, including nested
journal state. These are complete credential-redacted observations, not raw
bearer snapshots. No field/row is silently omitted. Snapshot unit checks
verify redaction and preservation before any real-route observation.

Live role flags/memberships/SET ROLE eligibility, function owners/SECURITY
DEFINER/search_path, real ENABLE/FORCE RLS policies, SQLSTATE/function path,
actual backend/session IDs, tuple retention, positive scopes and negative
effects accompany receipts. Invariant violations are
`P_SUPPORTED_SECURITY_FAIL`, retain the failing assertion and stop/escalate.
Unmeasured/ambiguous routes remain NOT_RUN/INCONCLUSIVE. Existing credential
scanner and artifact allowlist stay unchanged; no WAL/db archives, TLS keys,
generated secrets or raw protected child stderr are uploaded. Local Windows
has no active Docker/WSL lab; local missing-implementation RED/syntax checks
are not native route observations. Real execution is only in disposable CI.

## 3. Explicit unproven coverage and handoff

Even all three bounded cases passing cannot establish complete G4 coverage,
independent E, root survival under catastrophe, cross-login pool switching,
all public/application relations, restored old guards, DBA/owner bypass,
independent hosts/certificates/operator custody or Production readiness.
An absent hypothetical route is not a tested denial. Inventory-only privileges
are not dynamic path coverage. Issue #55 records actual outcomes and exclusions.

Stale direct/pool replay negatives combine a CLOSED old ticket, a new transaction
identity and the current policy/guard; they do not isolate retirement as the sole
denial cause. The separate explicit new policy1 ADMIT negative measures that
generation boundary. Current P1/P2 positives use read-scoped signed contexts;
their zero-row cross-tenant UPDATE checks are denial controls, not proof of a
healthy own-store write grant. Historical probe writes are observed separately.

Original S0-09D C-only rollback `FAIL_SECURITY`; I/J E G1–G5 `DESIGN_BLOCKED`;
Lane3 orphan OPEN_UNKNOWN resolution `BLOCKED`; coherent R-majority+old verifier
rollback `UNSUPPORTED / GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED`; independent-host/
cert/operator custody `NOT_PROVEN`; SOURCE-001/GATE-SOURCE `BLOCKED`; Gate #9
and #23/#28/#33 OPEN; #49 P1 OPEN all remain unchanged. New PR stays Draft,
unmerged. No canonical source baseline, Production, recovery runbook, identity
integration or Sprint0 approval. Independent source/log review and a separate
final CI reconciliation precede delivery for Management decision.
