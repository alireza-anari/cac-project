# S0-09O - interrupted fresh-ID learner repair

Execution authority: [Issue #53](https://github.com/alireza-anari/cac-project/issues/53).
Exact immutable N base: `ecce43e73a9418ed64538d3f142dc28a7e371ba1`.
Branch: `work/s0-09o-interrupted-learner-repair`, stacked on
`work/s0-09n-fresh-identity-repair-qualification` (Draft PR #52).

Classification: `NEW_IMPLEMENTATION_EXPERIMENTAL / CURRENT_NONRESTORED_3_OF_5_R_QUORUM_ONLY / NO_PRODUCTION`.

## Execution plan and frozen acceptance

1. Add three new O test methods, a one-observation runner, a child repair
   controller, and a supervisor. The existing N native-panic precondition
   helpers are imported unchanged. No inherited source/test/assertion is edited.
2. Execute one isolated observation per case per Push and PR trigger: six O
   observations total. No outcome-driven rerun or matrix growth. Each job has
   its own pinned five-process etcd 3.6.16 and three PostgreSQL containers.
3. Review exact-head source and all six O logs, unchanged regression cohorts,
   allowlisted credential scans and artifact metadata. Record the actual
   result, tested SHA, CI links and independent read-only review in Issue #53.

The local Windows session lacks a Docker engine, WSL access and direct GitHub
DNS. It is not an executed lab. The executable fixture is the existing pinned
GitHub Actions pattern, instantiated independently for every job. Dependency
and fixture startup failures must be reported, never converted to a PASS.

| Frozen case | Actual cut implemented | Required observed result |
|---|---|---|
| `O_REMOVE_ACK_THEN_STOP_OPEN` | Child exits 70 after real remove ACK and membership witness, before add | Old ID absent, four current voters, OPEN and successor exclusion retained |
| `O_LEARNER_ADDED_THEN_STOP_UNKNOWN` | Child exits 71 at pre-spawn boundary after add ACK, new certificate and empty new directory; learner process never starts | Exact authoritative learner nonvoting, no catch-up/promote/duplicate add, UNKNOWN held |
| `O_PROMOTE_ACK_LOSS_UNKNOWN` | Transport shim receives real promotion reply, discards it before returning to `q.promote`, then child exits 72 | Parent resolves actual voter state by authoritative membership; no second add/promote, UNKNOWN held |

The third case models **controller-visible response loss**. It is not a
network partition or an etcd response fabrication. The stale local learner
flag demonstrates that the controller did not consume the successful reply.
Only current-quorum membership resolves committed-but-reply-lost status.
Genuinely unresolved membership must remain inconclusive; there is no blind retry.

## Measurements and assertions

- Every sample must first reproduce the exact native archived-old-byte panic,
  exit2, matching member ID and `tocommit > lastIndex`. File hash inventories
  are preserved. The old failed process is reaped before replacement.
- The child is a distinct PID, ends with the designated exit code, and is
  reaped by the supervisor. Exactly one cut and exact ordered membership
  requests are required. The O-only low-level `_request` wrapper forbids any
  duplicate wire POST, including endpoint/auth retries hidden inside inherited
  `Etcd.call`. Two local transport-budget tests are separate unit methods,
  not native consensus observations or additional matrix samples.
- Full application Root, its state revision, and complete ordered journal are
  compared directly in the supervisor and hashed in per-step child witnesses.
  Quorum cluster/member IDs and original r1/r2/r3 PIDs survive. Old data remain
  hash-verified in quarantine. No old ID, data path or certificate is reused.
- Parent reconciliation uses fresh config and linearizable membership reads
  after controller death, before any possible continuation. This experiment
  does not resume repair. No automatic promote, abort, rollback or timeout
  interpretation is permitted.
- Trusted catalog/ACL/FORCE-RLS checks, old issuer/readiness and SQL admission
  denials are checked before and after interruption. Successor stays denied.
  OPEN closes only after the real transaction COMMIT ACK and authoritative
  `CLOSED_COMMIT`; only then is current policy2 scoped SQL checked. Genuine
  UNKNOWN blocks adoption/inferred abort/successor and policy2 is not forced.
- Safe artifact names and scanner are inherited unchanged. Native files,
  private configs, TLS keys, credentials and raw child stderr are not uploaded.

## Evidence and verdict discipline

This document freezes the implementation and acceptance before sampling.
**It does not assert an observed PASS.** The final delivery comment in
Issue #53 is the evidence ledger for actual outcomes and exact-final-head
Push/PR/job/artifact URLs, preserving one immutable code head for six samples.
The O workflow executes H51/K17/L7, four isolated M methods, and the two
unchanged N methods as separate regression jobs per trigger. These are
regressions, not new O methods. Repeated scanner methods are not new tests.
Any inherited workflow failure must also be disclosed.

Allowed aggregate verdicts: `O_INTERRUPTED_REPAIR_BOUNDED_PASS`,
`O_INTERRUPTED_REPAIR_INCONCLUSIVE`, `O_ENV_BLOCKED_NOT_RUN`, or
`O_SUPPORTED_SECURITY_FAIL`. Any supported security invariant violation
requires P0 escalation/STOP, not a flaky P1 classification.

## Unproven and unreleased

The finite single-host fixture cannot establish independent-host failure
domains, external certificate/operator custody, arbitrary/torn disk recovery,
responsive restored-majority/old-verifier protection, or a production runbook.
This does not fix native old-byte same-ID restart: #49 stays OPEN/NOT FIXED.
S0-09D original `FAIL_SECURITY`; E G1-G5 `DESIGN_BLOCKED`; Lane3 orphan UNKNOWN
resolution `BLOCKED`; responsive restored-majority/old-verifier `NOT_PROVEN`;
SOURCE-001/GATE-SOURCE `BLOCKED`; Gate #9 OPEN all remain unchanged.
All PRs remain Draft/unmerged. No Production, Preview, canonical source
baseline, accepted recovery runbook, Sprint0 sign-off, or security-gate release.
