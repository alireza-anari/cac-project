# S0-09N — Fresh-Identity Learner Repair Qualification

**Date:** 2026-11-15  
**Priority:** P1 reliability mitigation qualification  
**Classification:** `NEW_IMPLEMENTATION_EXPERIMENTAL / CURRENT_NONRESTORED_QUORUM_ONLY / NO_PRODUCTION`  
**Execution:** [Issue #51](https://github.com/alireza-anari/cac-project/issues/51)  
**Parent diagnosis:** [S0-09M Issue #49](https://github.com/alireza-anari/cac-project/issues/49), [Draft PR #50](https://github.com/alireza-anari/cac-project/pull/50), exact parent head `f679274a4ff5ff32978d9c87362a5e4e1c8f548c`.  
**Physical foundation:** [S0-09L Draft PR #48](https://github.com/alireza-anari/cac-project/pull/48), exact head `ba5bc82170da4523b39b1512eb7d2de344255c3`.  
**Architecture authority:** [S0-09N Architecture Ruling R0](../architecture/S0_09N_ARCHITECTURE_RULING.md).

## 1. Executive result

The finite N sample cohort reproduced the M native fail-stop in all four Push observations and successfully completed a fresh-identity learner replacement in all four. The tested mitigation is **not same-ID recovery**: it quarantines the stale member's physical files, removes the old identity through the surviving current quorum, adds a new member as a learner with a fresh empty data directory and certificate, verifies current Root/journal catch-up, and explicitly promotes once.

The tested operation holds survived:
- A pre-granted OPEN remained OPEN and the complete Root/journal remained unchanged across member replacement. Only the actual PostgreSQL COMMIT ACK followed by authoritative CLOSE resolved it. After that known close, current policy-2 scoped SQL succeeded and policy-1 admission remained denied.
- A genuine UNKNOWN remained UNKNOWN and the complete Root/journal remained unchanged across replacement. Successor activation, policy adoption and inferred abort were denied. The path intentionally did not force policy-2 SQL while UNKNOWN remained unresolved.

**Bounded interpretation:** `N_FRESH_ID_LEARNER_REPAIR_BOUNDED_PASS` is supportable only for the tested single-host disposable lab envelope after the exact old-byte native panic. It is a candidate recovery workaround, not a fix for same-ID Raft replay, not a production runbook and not a release of any P0 security gate.

## 2. Frozen matrix and observed native outcomes

Two distinct cases × two repetitions × Push/PR trigger were authorized. The first Push sample cohort (run [43725822683](https://github.com/alireza-anari/cac-project/actions/runs/43725822683)) produced four successful N observations:

| Case | Repetitions | Stop mode | Native result |
|---|---:|---|---|
| `N_PROGRESS_OLD_CLEAN_OPEN` | 2/2 | Clean SIGTERM | `NATIVE_FAIL_STOP_EXIT2`; `tocommit(103) > lastIndex(72)` |
| `N_PROGRESS_OLD_KILL_UNKNOWN` | 2/2 | SIGSTOP / non-child SIGKILL | `NATIVE_FAIL_STOP_EXIT2`; `tocommit(99) > lastIndex(72)` |

Every sample confirmed the old member identity in the native panic, exact exit code 2, and the expected old-byte archive. The native failure was observed before the replacement path was invoked.

## 3. Fresh-identity replacement evidence

All four Push observations completed the existing quorum-governed remove → add-as-learner → catch-up → explicit-promote path:

- The failed old process was absent. The old data directory was moved into quarantine and its complete file inventory/hash manifest matched the pre-replacement inventory.
- The exact old member ID was removed from authoritative membership before the learner add. The new etcd member ID differed from the old ID.
- The new data directory did not exist before native bootstrap; the new member used a distinct certificate/key pair. No old WAL, snapshot or backend database bytes were copied into the new member.
- The new member was observed as a non-voting learner before promotion. Authenticated current Root plus ordered-journal catch-up completed before promotion.
- The server accepted one explicit promotion request. Final membership contained five voters and zero learners; the old ID was absent; the cluster ID and original r1/r2/r3 majority identities remained unchanged.
- The complete Root/revision/journal tuple was byte-for-byte equal before and after the membership repair in each sample.
- The recovery observer records every remove/add/promote request attempt, not just successful responses; any repeated or out-of-order membership request fails the frozen test. The tested path requires exactly one remove, one add and one promote request.

## 4. Operation-hold results

### 4.1 OPEN — clean old-member stop

Both repetitions began with a real pre-granted OPEN backed by a live PostgreSQL transaction and a protected row update. After native fail-stop and fresh-ID repair, the Root head/revision/ordered journal and OPEN count were unchanged; UNKNOWN remained zero. A successor was denied before close.

The actual local transaction then received COMMIT ACK and the authority recorded `CLOSED_COMMIT`. Only after that known close did the broker adopt current policy 2; a scoped policy-2 read returned the committed body, while policy-1 admission was denied.

### 4.2 UNKNOWN — forced old-member kill

Both repetitions created a genuine UNKNOWN after durable OPEN and a policy transition. After native fail-stop and fresh-ID repair, the Root head/revision/ordered journal remained unchanged; UNKNOWN count remained one. Successor activation, policy adoption and an inferred abort were all denied. The test intentionally did not force policy-2 SQL while the operation remained UNKNOWN.

## 5. Regression and CI accounting

The initial exact-head Push run [43725822683](https://github.com/alireza-anari/cac-project/actions/runs/43725822683) completed all four N sample jobs, and the separate H51, K17 and L7 regression cohorts passed. The combined sequential M4 regression attempt failed in its third case before the M native observation with `RuntimeError: Real etcd readiness blocked` during the fixture's initial `archive_current()`. This is a regression-harness isolation failure, not a product finding. The final workflow isolates each M case in its own disposable job; that isolated rerun is required before acceptance.

Final exact-head Push/PR CI receipts, safe artifact inventory, and Management's role-separated source/log review are recorded in the final delivery comment on [Issue #51](https://github.com/alireza-anari/cac-project/issues/51). The first combined M4 attempt is excluded from any PASS count.

## 6. Scope and limitations

- Pinned etcd 3.6.16, one-host disposable CI lab, five-voter etcd topology and three independent disposable PostgreSQL clusters.
- The generic etcd member-replacement and learner model supports the mechanics; it does not prove CAC's combined Root/journal/OPEN/UNKNOWN guarantees outside this tested fixture.
- No multi-host failure domain, network partition, arbitrary disk corruption, external key custody, restored-majority/old-verifier, whole-cluster catastrophe, live/torn WAL, or Production environment was tested.
- Same-ID replay remains `P1_OPEN_NOT_FIXED`. No etcd/Raft binary or source patch, same-ID retry, force-new-cluster, whole-cluster restore, security-guard relaxation, quorum reduction, UNKNOWN clearing, Merge or Production authorization is included.
- S0-09D remains `FAIL_SECURITY`; E G1–G5 remain P0 DESIGN_BLOCKED; Lane3 OPEN_UNKNOWN clearing remains BLOCKED; SOURCE-001/GATE-SOURCE and Gate #9 remain blocked/open. Issue #49 remains OPEN until Management accepts the bounded workaround and separately decides whether deployment-specific operational qualification is needed.

## 7. Final disposition

`N_FRESH_ID_LEARNER_REPAIR_BOUNDED_PASS` — subject to successful isolated M regression and exact-head PR verification. Issue #51 may close only as completed bounded experimental evidence after that verification. Issue #49 remains OPEN for the unresolved same-ID availability defect. PR #50 and the new N PR remain Draft/unmerged; no canonical source, Sprint0 or Production status follows.
