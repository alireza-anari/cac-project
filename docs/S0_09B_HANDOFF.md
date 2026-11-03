# S0-09B architecture handoff

**NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED**. Issue #17,
[stacked Draft PR #18](https://github.com/alireza-anari/cac-project/pull/18),
base `work/s0-09a-trusted-context-poc` at
`f351e26aa93ec87f17366dbaff85a87b171d36d2`. Do not merge.

Source identity: CAC-NEW-ORIGIN-S0-07. No historical source recovered.
SOURCE-001 / GATE-SOURCE BLOCKED; architecture #9 OPEN.
PR #11 and PR #16 were reverified Draft/open/unmerged before branching.
No production identity, MFA provider, public API, onboarding, business mutation,
customer data, deployment or production secret is involved.

## Delivered scope

Local issuer process with kernel-checked peer identity, role-only credential
file/environment and independent DB COMMIT-before-return. Actual runtime UID
uses real PgBouncer transaction pooling. Actual database restart and logical
schema/data restore are exercised separately from controlled clock fault
injections, real elapsed expiry and contention/cancellation/deadlock schedules.

See [reproduction and test matrix](../experimental/backend/pool_recovery/README.md),
[residual P0/P1 risks](../experimental/backend/pool_recovery/RISKS.md), and
[proposed CR/ADR decisions](changes/CR-S0-09B-001-recovery-pool-contract.md).

## Reproduction and failure history

[Initial push 41581543249](https://github.com/alireza-anari/cac-project/actions/runs/41581543249)
on `f22dd2556fa24cd087bd790b0d8faf98cff74d46` failed at child process startup.
It preserved and passed all inherited 43 tests and all 24 S0-09A cases,
each before/after their rollback/reapply. The new fixed-clock challenge,
expiry, MFA, cleanup and encoding tests passed on PostgreSQL; process/pool/
recovery tests did not execute successfully. This failed run is not evidence of
process isolation or pool safety. No SQL checks were relaxed in response.

Actual package install passed: PostgreSQL **17.11 (Debian 17.11-1.pgdg12+2)**,
PgBouncer **1.22.0**, exact Ubuntu package **1.22.0-1build4**.
Inherited locked Python/Django/psycopg versions unchanged.

Local environment had no PostgreSQL/Docker and denied Unix socket creation;
local AST/request-validator checks only are not database evidence. CI is the
execution authority. Startup diagnostics redact all known fixture credentials.

## Migration and contract diff

Inherited Django migrations, models, SQL functions, policies, grants and all
67 tests remain unchanged in git. Added runner temporarily mutates only the
explicitly disposable database and restores exact function definitions, then
requires structural down/up equality. No persistent schema or public API diff.
v2 bytes and 5s/60s/120s/300s numbers are test inputs, not ratified contracts.

## Independent review and reproduced defect

Independent read-only static review of 42ba141 identified no critical privilege
bypass, but reported the truncated-EOF CPU loop and unverified process startup.
CI diagnostics proved private runner-home traversal denial; root-owned copied
entrypoints and a root-prebound listening socket fixed the process setup without
making the socket directory writable to runtime.

[Focused RED 41582586448](https://github.com/alireza-anari/cac-project/actions/runs/41582586448)
on `6a688850e4c2595e1b538eafbccef496e862f95f` ran **26 cases: 25 passed,
1 assertion failure, 0 errors**. It reproduced the EOF receiver defect; the
receiver is fixed to reject empty recv immediately. This is actual test-first
RED evidence, not an import/startup failure relabeled as a security regression.

The reviewer noted that clone token denial is also PID/xid-confounded; the
separate live-runtime generation test isolates generation invalidation. Restore
now logs/probes the original five-second window explicitly and fails if it is
missed; no TTL was extended. General service admission/DoS stays a residual P1.
The independent review was static; fixes are validated by execution, with no
claim of external security certification or independent database execution.

## Administrator-boundary regression

[Focused green 41582991340](https://github.com/alireza-anari/cac-project/actions/runs/41582991340)
on `914a46d078928c7b252caa7da5a0f0313c2dc6bd` executed all 26 cases successfully,
including the EOF regression; known-credential artifact scan passed. It is
superseded by the expanded 27-case final matrix.

Self-review then added the runtime adversary's known public bootstrap password.
[Focused RED 41583393073](https://github.com/alireza-anari/cac-project/actions/runs/41583393073)
on `6d0ef24f2d4be28c2158f6a09369c566a94fccbb` executed 27 cases: 26 passed and
one assertion failed because a runtime process could use the public disposable
administrator credential to query guard keys. No key bytes were emitted.

The fix randomizes the disposable postgres password **before adversarial UIDs
start**, keeps it only in the existing private all-role configuration, and
requires the same old-password/key-access attack to fail. This also prevents
claiming that source-file ACL isolation alone establishes a credential boundary.
The separate processes still receive only their individual random role password.

## Final acceptance receipt and concrete findings

The authoritative **final head/base SHA, exact Push and PR run IDs, synthetic
merge SHA, artifact links and execution outcome** are recorded in the
[Draft PR #18 receipt](https://github.com/alireza-anari/cac-project/pull/18).
A SHA cannot name its own tree; use that maintained receipt and the per-run
`tested-sha.txt` / `pr-head-sha.txt` evidence to bind these documents to execution.

The full workflow requires this matrix, zero failures/errors/skips, and exit 0:

| Suite | Distinct cases | Verification |
|---|---:|---|
| Retained foundation | 43 = 39 PostgreSQL + 4 configuration subprocess | before/after foundation zero/down/up; ORM and schema/ACL equality |
| Retained S0-09A | 24 PostgreSQL | before/after PoC down/up; original sensitivity controls |
| Added S0-09B | 27 = 8 process + 9 pool/locks + 3 recovery + 7 timing/encoding | before/after another PoC structural down/up; transaction/MFA/window mutation assertion RED then restoration |

**94 distinct cases total**; repeats are not new tests. Added cases combine
actual PostgreSQL, Linux process and infrastructure evidence; do not describe
all 94 as independent SQL tests. A supplemental focused workflow executes only
the 27 added cases once for faster feedback; it does not replace the full floor.

Observed findings within the measured scope:

- Root-owned read-only entrypoints, private role files, scrubbed child env and
  kernel peer credentials separate the unprivileged runtime/issuer processes.
  Public bootstrap authority must first be removed, as the regression proves.
- Transaction pooling reuses a backend PID across different xids. Deliberately
  persistent session context is denied by transaction binding; four simultaneous
  Store transactions are isolated in the measured schedule.
- Backend cancellation, aborted SQL, injected deadlock, rollback and savepoint
  paths retain fail-closed authorization. Issuer COMMIT failure returns no token.
- Controlled PostgreSQL restart preserves committed ledger rows but kills the
  old transaction. Logical restore preserves signing authority until explicit
  generation fencing; no automated fencing/HA/PITR protocol is delivered.
- Exact clock-fixture edge predicates and separate elapsed expiry/MFA checks
  have distinct evidence. No timing SLA or product TTL approval follows.
- Python MAC calculation over exact PostgreSQL bytes works for the examples;
  naive Python JSON serialization differs for at least one typed vector.
  Canonical v2 bytes and constant-time MAC validation remain open P0 questions.

These findings are conditional on the exact run receipt; they grant no
production readiness, source-baseline acceptance or permission to integrate
identity/onboarding. Proposed decisions and all unsupported scenarios remain
in CR-S0-09B-001 and the residual risk matrix. General admission/DoS remains P1;
physical recovery, external key custody, valid bearer-proof theft, split-brain
fencing and the protocol remain P0 integration gates.


## Fresh-observer regression

At `d27c479a`, full PR CI
[41583867122](https://github.com/alireza-anari/cac-project/actions/runs/41583867122)
passed the complete 94-case before/after matrix, all sensitivity and scans.
Full Push [41583861223](https://github.com/alireza-anari/cac-project/actions/runs/41583861223)
passed the first 27-case run, all three assertion RED mutations and structural
roundtrip, but the second run failed its issuance/revoke lock witness. It is
not reported as green or hidden by rerunning unchanged code.

The observer had queried pg_stat_activity inside one transaction: PostgreSQL
retains that activity snapshot until transaction end. Observer connections now
use autocommit so every poll obtains a fresh snapshot. The race test deliberately
primes an empty view before starting issuers and requires an actual
`pg_blocking_pids` witness containing the particular revoker PID. No clock,
issuer lock timeout, security predicate or negative assertion is relaxed.
See [PostgreSQL 17 statistics snapshot semantics](https://www.postgresql.org/docs/17/monitoring-stats.html#MONITORING-STATS-VIEWS).
The final exact-head receipt in PR #18 supersedes both of these candidate runs.
