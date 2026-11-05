# S0-09D staged security proof handoff

Status: NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED. Issue21; Draft PR22 stacked on C. This is a live staged record, not protocol acceptance.

## Phase1 — COMPLETE at 65006f4b6d7a94751f077c865094c9acf3d2d6fd

[Verified management checkpoint](https://github.com/alireza-anari/cac-project/pull/22#issuecomment-6662649292). Exact parent 8bd81906f6edbf1732e22c46ca8925c7dec1a595. Three new distinct probes, 114 unchanged cases in separate workflows: 117 distinct total at Phase1.

| Control | Actual RED | Restoration / GREEN |
|---|---|---|
| CAS | Removing expected-epoch predicate permits stale expected0 reservation after epoch1; FenceDenied not raised | Exact function catalog restored; same target GREEN |
| SQL Fence | Removing check_guard online attestation permits raw challenge without live ticket; InsufficientPrivilege not raised | Exact catalog restored; valid gated challenge and no-ticket denial GREEN |
| OPEN | Removing reserve OPEN predicate permits reservation despite actual crashed issuer/orphan; FenceDenied not raised | Exact catalog restored; same target GREEN |

Each RED requires exactly one intended assertion failure, zero errors/skips; function definition, owner, ACL, SECURITY DEFINER and settings equality checked in finally before fixture reset. Three baseline/final probes and C20 post-mutation suite pass. Whole-cluster/job SIGKILL cannot promise Python finally execution; all authority/data are disposable service fixtures and job teardown destroys them. No mutation is committed to inherited SQL.

| CI | Push exact head | PR merge |
|---|---|---|
| D proof | [42058440127](https://github.com/alireza-anari/cac-project/actions/runs/42058440127) PASS | [42058448878](https://github.com/alireza-anari/cac-project/actions/runs/42058448878) PASS |
| Full retained94 | [42058439858](https://github.com/alireza-anari/cac-project/actions/runs/42058439858) PASS | [42058448933](https://github.com/alireza-anari/cac-project/actions/runs/42058448933) PASS |

Additional C PR42058448915 and B focused42058448866 PASS. PR checkout merge943de6b; parent/head recorded by workflow artifacts. Full94 logs show 43/43,24/24,27/27 around roundtrip. Repeats do not add distinct cases. D runs retained C20 before/after migration and after mutations.

[Independent read-only Phase1 review](security/S0_09D_PHASE1_READ_ONLY_REVIEW.md): no blocking source finding, one low documentation-path trigger gap; no independent DB rerun.

## Phase2 — COMPLETE at 5a5ddda96a6a034bd6396735fde292f3b9ee8e53

Four new tests compose unchanged C Gate/SQL with actual PgBouncer 1.22.0, package1.22.0-1build4. Runtime SQL and RLS go through a size-one transaction pool. Readiness and issuer/activation connections retain original direct online SQL to avoid a readiness query queuing behind the held single runtime backend. This is a test-only transport, not a new production broker or UID isolation proof.

[Verified Phase2 checkpoint](https://github.com/alireza-anari/cac-project/pull/22#issuecomment-6662962158). D push42060774098 and PR42060783634 PASS; full94 push42060774149 and PR42060783711 PASS; additional C PR42060783731 and B focused42060783918 PASS. PR checkout18f5973; push exact head.

Four new cases PASS. Push PID/fullxid witnesses: commit197 /1973->1978->1980; cancel219 /1989->1994->1996; rollback249 /2005->2010->2012; held takeover167 /1958->1963. Same PID, changed fullxid, stale context/ticket denied, known outcomes leave zero OPEN. Actual PgSleep observed and pg_cancel_backend succeeds; diagnostic explicitly says user request, not statement timeout. Hostile session context deliberately persists through pool release but cannot authorize the new transaction. Positive scoped RLS controls precede denial.

Independent Phase2 source review found no blocking defect; its nonblocking cancellation ambiguity was addressed by the diagnostic assertion in5a5ddda9 and verified in CI. Review did not itself execute databases. 121 distinct GREEN cases across separate workflows at this stage (114 floor +3 Phase1 +4 pool), not a combined run under C wrappers. No SQL/check/TTL changes.

## Phase3 — CANDIDATE / actual execution pending

Eight new bounded denial/retry/race targets are prepared: actual authenticated logical anchor clone at another endpoint/cluster ID; read-only actor sessions; malformed signed response; SQL channel refusal while broker channel remains healthy; lock-witnessed two-contender CAS; crashed issuer orphan across anchor restart; discarded reserve receipt/disconnect retry; missing dblink extension and exact function/owner/ACL reapply.

A separate unchanged safety assertion tests logical rollback of C's actual anchor schema from epoch2 to its earlier epoch1 dump, with same physical C identity. The hypothesis is previous-owner revival: if observed, it is SECURITY FAIL/BLOCKED, not a passing recovery mode. The runner requires the intended assertion RED and exact restoration of the latest C state/data/sequence/functions/ACL/RLS flags before proceeding. Expected unsafe observations are reported separately from GREEN cases.

Physical PITR, same-identity physical clone with two live anchors, asymmetric network partition/firewall loss, actual standby promotion, wire-level lost COMMIT acknowledgment, complete missing-role matrix, multihost HA and externally witnessed orphan reconciliation remain NOT_RUN. Logical restore is not physical restore. Read-only role session is not standby. Discarding an application receipt is not injected wire packet loss. Bad per-channel port is not a network partition. Never infer anti-rollback authority or safe clearing from this experiment. Orphan reconciliation remains BLOCKED; no clearing API or timeout revival is introduced.

## Restrictions and current risks

Local execution NOT_RUN: execution environment unavailable. Only actual Actions runs establish PostgreSQL results. Workflow edits are via authorized GitHub connector; no local restriction bypass attempted.

P0: trusted anchor rollback/clone and absent external recovery/anti-rollback custody contract; orphan reconciliation cannot safely clear ambiguity. P1: same-host clusters, finite schedules, targeted bootstrap predicates, production TLS/credentials/KMS/identity and performance outside scope. Protocol, v2 format, TTLs and key management remain unapproved.

SOURCE-001/GATE-SOURCE BLOCKED; Gate9 OPEN. PRs11/16/18/20 unchanged; PR22 Draft/unmerged. No production deployment, real secrets/IdP/MFA/onboarding, APR-033/034/035/036 change, historical source recovery or Sprint0 completion.
