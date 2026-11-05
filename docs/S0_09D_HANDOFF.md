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

## Phase2 — CANDIDATE / execution pending

Four new tests compose unchanged C Gate/SQL with actual PgBouncer 1.22.0, package1.22.0-1build4. Runtime SQL and RLS go through a size-one transaction pool. Readiness and issuer/activation connections retain original direct online SQL to avoid a readiness query queuing behind the held single runtime backend. This is a test-only transport, not a new production broker or UID isolation proof.

Planned evidence: equal backend PID with different fullxids; intentionally persistent hostile session GUCs; commit/rollback reuse; actual pg_cancel_backend while PgSleep observed; lock-witnessed blocked takeover and stale-context denial on the reused backend afterward. No PASS claimed until actual logs. No SQL/check/TTL changes.

## Phase3 — NOT_RUN / pending

Bounded rollback/clone/invalid-identity authority, invalid response/read-only/channel faults, deterministic races and safe orphan recovery are not yet delivered. Physical PITR, same-identity clone, asymmetric network partition, multisite HA and externally witnessed orphan reconciliation are NOT_RUN. Never infer anti-rollback authority or safe orphan clearing from Phase1/2. Orphan reconciliation remains BLOCKED; timeout never revives authority.

## Restrictions and current risks

Local execution NOT_RUN: execution environment unavailable. Only actual Actions runs establish PostgreSQL results. Workflow edits are via authorized GitHub connector; no local restriction bypass attempted.

P0: trusted anchor rollback/clone and absent external recovery/anti-rollback custody contract; orphan reconciliation cannot safely clear ambiguity. P1: same-host clusters, finite schedules, targeted bootstrap predicates, production TLS/credentials/KMS/identity and performance outside scope. Protocol, v2 format, TTLs and key management remain unapproved.

SOURCE-001/GATE-SOURCE BLOCKED; Gate9 OPEN. PRs11/16/18/20 unchanged; PR22 Draft/unmerged. No production deployment, real secrets/IdP/MFA/onboarding, APR-033/034/035/036 change, historical source recovery or Sprint0 completion.
