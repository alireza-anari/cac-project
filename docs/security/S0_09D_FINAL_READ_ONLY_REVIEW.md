# S0-09D final independent read-only security review

Review completed 2026-11-06 (Asia/Tehran). Repository `alireza-anari/cac-project`; base `8bd81906f6edbf1732e22c46ca8925c7dec1a595`, executable head **`8b490bfe5a64ac62c0a8382e77ce6a45486b4f04`**. Subsequent handoff edits are documentation only and are identified in the final PR22 delivery receipt.

A separate reviewer read the design/plan/handoff, all new recovery_proof source/tests, workflow routing and relevant inherited SQL/Gate/tests. The reviewer independently read decoded D and full94 CI logs and status metadata through supported GitHub connector tools. No source writes or independent database execution. This is not third-party certification. A temporary reviewer usage limit interrupted the first pass; the same review resumed and completed after continuation. Generic GitHub fetch cannot read redirected job logs; the supported decoded-log reader was used.

**No remaining blocking defect found in the bounded proof harness. Protocol acceptance remains BLOCKED by observed anchor rollback behavior and unproved safe recovery.**

| Severity / status | Finding and disposition |
|---|---|
| P0 — observed trust blocker | `experimental/backend/recovery_proof/authority_red.py:29`: actual restore of earlier C schema at the same C identity revives A after B takeover. Both D logs show A ready=True/B=False; source requires successful new issuance and scoped RLS before the original safety assertion fails. SECURITY FAIL/BLOCKED, not a passing recovery mode |
| P2 — addressed | `experimental/backend/recovery_proof/run.py:56`: initial runner could enter a later fixture reset after an authority restoration failure. Reviewed `failfast=True` delta from09175ef4 stops this progression. Inherited controls untouched |
| Low — retained | `recovery-proof.yml:5,7` and `experimental-backend.yml:4,7` under `.github/workflows` omit design/plan-only paths in `docs/superpowers`. Those changes alone do not trigger fresh CI. No runtime bypass; final handoff/review/CR paths are included |

The review verified actual CAS/SQL/OPEN mutations, one intended assertion RED with zero errors/skips, exact catalog restoration and identical target GREEN. Mutation drift cannot count as RED. Healthy live OPEN permits same-owner nested work; orphan OPEN blocks new use/takeover. No clearing or timeout revival was introduced.

Pool tests use actual transaction-mode PgBouncer with equal PID/distinct fullxid, valid issuance/RLS before denial and persistent hostile session state. Cancellation requires PostgreSQL's user-request diagnostic. Runtime authorization/RLS is pooled; readiness and issuer remain direct. The evidence does not establish every production pool configuration or crash schedule.

Clone helpers use synthetic roles/database and remove them, including the additional shared function grant. Dump/snapshot material remains private; diagnostics avoid exposing private comparison values. Latest-state rollback cleanup compares instance/state/activation/operation data, sequence state, function definitions/owners/ACL/SECURITY DEFINER/settings and table/sequence owner/ACL/RLS flags before C20 proceeds. These fields do not constitute exhaustive catalog equivalence. Inherited recovery SQL, Gate and all114 floor tests are unchanged; full94 workflow changes are routing only.

## Independently inspected execution evidence

| Workflow | Exact-head push | PR merge |
|---|---|---|
| D proof | [42063170761](https://github.com/alireza-anari/cac-project/actions/runs/42063170761) SUCCESS | [42063182389](https://github.com/alireza-anari/cac-project/actions/runs/42063182389) SUCCESS |
| Full94 | [42063170143](https://github.com/alireza-anari/cac-project/actions/runs/42063170143) SUCCESS | [42063182278](https://github.com/alireza-anari/cac-project/actions/runs/42063182278) SUCCESS |

C PR42063181989 and B focused PR42063182367 also SUCCESS. Push identifies8b490bfe; PR identifies merge8ba3fc9 of that head into8bd81906. Both D logs contain8 authority GREEN, separately classified rollback SECURITY RED, latest-state restoration and C20 GREEN afterward. Both full94 logs contain43+24+27 before/after roundtrip. Known-fixture scans of artifact evidence pass; this does not certify all job-log content.

## Residuals and recommendation

Anti-rollback custody and safe orphan reconciliation remain P0 blockers. Same-host topology, finite schedules, targeted bootstrap predicates, production TLS/credential/KMS/identity isolation and performance are P1 limits. Physical PITR, two same-identity physical clones, asymmetric partitions, standby promotion, wire-level lost COMMIT ACK, complete missing-role matrix, multihost HA and externally witnessed orphan clearing are NOT_RUN.

Retain Draft experimental evidence; record the failed recovery invariant explicitly. SOURCE-001/GATE-SOURCE BLOCKED, Gate9 OPEN. No production approval, merge, safe-recovery claim or protocol ratification follows from CI SUCCESS. See [handoff](../S0_09D_HANDOFF.md) for the complete matrix and proposed management disposition.
