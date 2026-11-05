# S0-09D staged security proof handoff

Status: NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED. [Issue21](https://github.com/alireza-anari/cac-project/issues/21); [Draft PR22](https://github.com/alireza-anari/cac-project/pull/22), branch `work/s0-09d-fencing-proof-gaps`, stacked on `work/s0-09c-recovery-fencing-poc` at exact `8bd81906f6edbf1732e22c46ca8925c7dec1a595`. Handoff updated 2026-11-06 (Asia/Tehran); execution timestamps below are UTC on 2026-11-05.

**Result: candidate sensitivity and bounded pool composition proved; anchor rollback safety FAILED and remains BLOCKED.** There are 129 distinct GREEN cases across separate workflows (94 inherited +20 C +3 sensitivity targets +4 pooled cases +8 authority cases), plus a separate failing rollback safety assertion. A successful experiment CI means the intended unsafe observation and restoration were recorded, not that rollback is safe or the protocol accepted.

Final executable revision reviewed/tested: `8b490bfe5a64ac62c0a8382e77ce6a45486b4f04`. Each phase SHA is identified below. The subsequent documentation commit and its exact-head/PR-merge CI are identified in the final management receipt on PR22; earlier runs are not attributed to a later SHA.

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

## Phase3 — bounded experiment COMPLETE; rollback safety FAIL/BLOCKED

Stage SHA: `8b490bfe5a64ac62c0a8382e77ce6a45486b4f04`. Initial candidate09175ef4 was superseded by the reviewed failfast correction; do not use its superseded checks as final evidence.

| Scenario actually executed | Security result | Scope of evidence |
|---|---|---|
| Actual authenticated logical anchor clone on B, with a different PostgreSQL system identifier and endpoint | PASS | Actor can query the cloned active authority; Broker rejects its SID and A's SQL readiness denies when routed there; original routing restored and positive operation succeeds |
| C actor session made read-only by real role configuration | PASS | `transaction_read_only=on` observed; authority/readiness deny; exact role configuration restored. This is not a standby |
| Malformed authority response | PASS | Actual attest function returns malformed bytes; readiness/use deny; definition/owner/ACL/settings restored and positive operation succeeds |
| SQL-to-anchor channel refused while Broker-to-anchor remains healthy | PASS | Bad SQL-channel port causes denial although direct status is active; connection configuration restored. This is not a network partition |
| Two real CAS contenders blocked behind an administrator-held row lock | PASS | Both waiting PIDs and blocking chain observed; release yields exactly one epoch2 winner, both unready during reservation, loser denied after winner activation |
| Actual issuer process exit, orphan OPEN, then C SIGKILL/restart and fresh coordinator | PASS for denial; recovery BLOCKED | Durable orphan remains; new authorization and takeover deny; no timeout clearing or recovery API implemented |
| Committed reserve receipt deliberately discarded, then disconnect/retry | PASS | Same UUID returns epoch2 once, one activation row, positive operation after retry. This is application receipt loss, not wire-level COMMIT-ACK loss |
| Real missing dblink extension, then reapply | PASS | Readiness/use deny; extension function definitions/owners/ACL compared after reinstallation; positive operation returns. Not an exhaustive comparison of every extension object |
| Actual logical rollback of C anchor schema, unchanged physical C identity, epoch2 to earlier epoch1 | **FAIL_SECURITY / BLOCKED** | Old A becomes ready and successfully issues a new context and performs scoped RLS access; B becomes unready. Original fail-closed assertion remains RED. Latest C snapshot is restored before C20 GREEN |

The rollback experiment uses actual private `pg_dump`/`pg_restore` against the independently initialized C cluster; it does not fake an attestation or change a security assertion. It demonstrates that the current protocol relies on the authority **not itself being rolled back**. It is not evidence of an unprivileged runtime exploit under the non-rollbacked-anchor model. It also does not establish two simultaneously live physical anchor clones.

Push log42063170761 records rollback old-A readiness=True/new-B=False at16:22:42Z, latest-state restoration at16:22:42Z, then retained C20 GREEN at16:23:09Z. PR log42063182389 independently records the same sequence at16:24:23Z and16:25:01Z. Successful issuance/RLS is required by source before the failing assertion. The runner demands exactly one intended safety failure and zero errors/skips; infrastructure/restore failures cannot satisfy this receipt.

Restoration compares private instance/state/activation/operation data, sequence state, function definitions/owners/ACL/SECURITY DEFINER/settings, and table/sequence owner/ACL/RLS flags. These are the compared fields, not exhaustive equivalence of every PostgreSQL property. The authority GREEN runner uses failfast so a fault-restoration failure stops before the next fixture reset. Dump bytes and private snapshot values are not evidence artifacts.

| Phase3 CI | Exact-head push | PR synthetic merge |
|---|---|---|
| D proof | [42063170761](https://github.com/alireza-anari/cac-project/actions/runs/42063170761) SUCCESS | [42063182389](https://github.com/alireza-anari/cac-project/actions/runs/42063182389) SUCCESS |
| Full retained94 | [42063170143](https://github.com/alireza-anari/cac-project/actions/runs/42063170143) SUCCESS | [42063182278](https://github.com/alireza-anari/cac-project/actions/runs/42063182278) SUCCESS |

Additional C PR [42063181989](https://github.com/alireza-anari/cac-project/actions/runs/42063181989) and B focused [42063182367](https://github.com/alireza-anari/cac-project/actions/runs/42063182367) SUCCESS. PR checkout is merge `8ba3fc9` of8b490bfe into8bd81906; push tests exact stage SHA. Full94 logs show43/43,24/24,27/27 around roundtrip. C20, all three sensitivity RED/restoration/GREEN receipts and all four pooled cases rerun at this revision. Repeated execution never adds distinct cases.

## Environment, rollback and reproducibility

PostgreSQL17.11 (`17.11-1.pgdg12+2`), official image `postgres@sha256:839fbb5a4942a7758dd93e18b42ea5649807491a0545b5eeeb8f0b8bb11857a5`; PgBouncer1.22.0 (`1.22.0-1build4`); Python3.12.15 and locked/hashes-checked requirements. C logs fsync, synchronous_commit and full_page_writes ON. Restart observations and these settings are not a storage power-loss guarantee.

| Cluster | Phase3 push system ID | Phase3 PR system ID |
|---|---|---|
| A primary | 7704722924099149862 | 7704723074995531814 |
| B independent restore/temporary clone host | 7704722926159843364 | 7704723077760106534 |
| C external anchor | 7704722929602183206 | 7704723080856195110 |

They are separately initialized clusters on one CI host, not separate physical failure domains. App schemas are restored to B; the authority rollback experiment separately restores the anchor schema on C. The original C app migration down/up retains its bounded function/ACL/owner, column/constraint/policy comparison; full94 workflows retain their existing rollback checks. Inherited SQL, Gate, 94 tests and C20 test files are byte-for-byte unchanged by D. Full94 workflow changes only route D branch/document paths to existing checks.

Use `.github/workflows/recovery-proof.yml` on the exact stage or final SHA: bootstrap the disposable three services, execute `python -m recovery_fencing.parent_red`, `python -m recovery_fencing.run`, then `python -m recovery_proof.run`. The latter runs completed phases sequentially. The historical artifact filename `phase1.log` contains all three D phase receipts. Full94 uses `.github/workflows/experimental-backend.yml`. Do not execute bootstrap/fault modules against any other database.

All eighteen successful phase runs and their artifact IDs/digests/expiry are in [the CI manifest](evidence/S0_09D_CI.json). Archive digests are GitHub metadata, not independently rehashed ZIPs. Raw uploaded evidence is accessible through the run artifacts; retain before their recorded expiry for long-term audit. Credential scans cover the uploaded evidence files and known fixture material, not arbitrary job-log content or unknown secrets.

## NOT_RUN and blocked recovery matrix

| Mode | Status / reason |
|---|---|
| Physical PGDATA backup/PITR or standby promotion | NOT_RUN — harness exercises logical restores, no physical recovery fixture or custody contract |
| Two live physical anchor clones with the same SID/material | NOT_RUN — different-cluster logical clone and same-C logical rollback are the executed cases; physical-clone indistinguishability is a design inference, not an execution result |
| Asymmetric network partition/firewall packet loss | NOT_RUN — only real channel refusal by bad port, container stop/crash and role read-only behavior tested |
| Wire-level lost COMMIT acknowledgment | NOT_RUN — committed application receipt was discarded; no transport fault injected |
| Complete missing-role/permission/extension fault matrix | NOT_RUN — targeted config/ACL floor, missing dblink and read-only actor tested; not every installation fault |
| Pooler/backend crash, pooled issuer/readiness and arbitrary multiuser pool composition | NOT_RUN in D — runtime pool composition bounded to tested known-outcome paths; inherited B tests remain separate evidence |
| Multihost/multisite HA, quorum, storage power loss and exhaustive schedules | NOT_RUN — one host, finite deterministic and process/container fault cases |
| Externally witnessed orphan reconciliation | NOT_RUN / BLOCKED — no safe clearing protocol proved or implemented; no timeout revival |
| Production TLS/KMS, credential lifecycle, real IdP/MFA/onboarding and performance/RPO/RTO | NOT_RUN / outside approved scope |

## Restrictions and current risks

Local PostgreSQL/PgBouncer execution NOT_RUN. The command environment was unavailable during implementation; authorized GitHub connector changes and disposable Actions supplied the database evidence. On the resumed2026-11-06 handoff, local command execution became available: Python AST/inventory checks and Git diff/link checks ran in an isolated checkout. No earlier environment restriction was bypassed and no database result is inferred from local syntax checks.

P0: trusted anchor rollback/clone and absent external recovery/anti-rollback custody contract; orphan reconciliation cannot safely clear ambiguity. P1: same-host clusters, finite schedules, targeted bootstrap predicates, production TLS/credentials/KMS/identity and performance outside scope. Protocol, v2 format, TTLs and key management remain unapproved.

SOURCE-001/GATE-SOURCE BLOCKED; Gate9 OPEN. PRs11/16/18/20 unchanged; PR22 Draft/unmerged. No production deployment, real secrets/IdP/MFA/onboarding, APR-033/034/035/036 change, historical source recovery or Sprint0 completion.

## Independent review and proposed architecture vote

[Final independent read-only review](security/S0_09D_FINAL_READ_ONLY_REVIEW.md) examined source and actual D/full94 logs at8b490bfe. No remaining blocking harness defect; P2 restoration/reset ordering addressed by failfast. The observed rollback safety failure and absent safe orphan reconciliation remain P0 architectural blockers. A low design/plan-only CI path-filter limitation is retained and disclosed. Review is not an external certification or independently rerun database experiment.

Proposed vote: **accept the bounded sensitivity/pool/fault evidence; reject the demonstrated rollback recovery mode and defer protocol acceptance** pending a separately reviewed anti-rollback/fencing/key-custody contract and externally witnessed orphan recovery proof. [CR-S0-09D-001](changes/CR-S0-09D-001-authority-recovery-boundary.md) compares candidate authority boundaries without approving an implementation. Preserve the safety assertion RED until a real control makes it GREEN; never reinterpret successful CI as restored security.
