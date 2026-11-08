# CAC — S0-09K Architecture Ruling R0

**Date:** 2026-11-08  
**Authority:** Astra Management / Security Architecture  
**Execution:** [S0-09K Issue #45](https://github.com/alireza-anari/cac-project/issues/45)  
**Technical evidence:** [Draft PR #46](https://github.com/alireza-anari/cac-project/pull/46) exact head `9e768a4d1f6c97c429c36475237e132b8e3e7fc2`, target `work/s0-09h-quorum-survival-poc` at H head `b32416c799160f0e5957506d58254a693cbc231f`. **OPEN / DRAFT / UNMERGED**.  
**Handoff:** [S0-09K technical proof and source-review report](https://github.com/alireza-anari/cac-project/blob/9e768a4d1f6c97c429c36475237e132b8e3e7fc2/docs/security/S0_09K_POLICY_RETIREMENT_EXPERIMENT_HANDOFF.md); [final immutable issue receipt](https://github.com/alireza-anari/cac-project/issues/45#issuecomment-6717790281).  
**Vote:** `ACCEPT_BOUNDED_S0_09K_REAL_POLICY_RETIREMENT_UNDER_NONRESTORED_Q / P0_ROOT_CATASTROPHE_UNPROVEN / LANE3_BLOCKED / NO_MERGE_OR_PRODUCTION`.  
**Classification:** `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`.

## 1. What was independently inspected

Management fetched exact PR head/base metadata, full new S0-09K handoff, the **11 changed paths** (one CI workflow, one security report, K test/run/sensitivity and related H-quorum modules), the actual `retirement.py`, `authority.py`, `policy.py`, `test_policy_retirement.py` and sensitivity source. Existing H / SQL / inherited backend / Preview and APR files were **not changed by the PR**.

The 17 distinct test methods are K00–K16 and implement real etcd five-process Root policy-generation 1→2 under a current **non-restored 3/5 R majority**. Authoritative control-only CAS commits the policy/profile, cut sequence, idempotent request receipt and full ordered Root state+journal; signing generation stays **1**. The proof distinguishes retirement from merely rotated signing keys or fixed policy mismatch checks.

A current trusted verifier/issuer/guard and real PostgreSQL/PgBouncer paths deny **new** retired-policy work, including a valid old signed transcript, direct old readiness, issuer and reused-pool paths. Positive policy2 authorized SQL/RLS is observed. An **already granted pre-cut** operation may reach actual known COMMIT or ABORT; it keeps unresolved successor exclusion until an authoritative CLOSE. A real UNKNOWN remains unresolved and never releases a successor by timeout, session loss, cancellation, member repair, or signature alone.

The source shows profile-generation labels and private controller adoption under trusted R/catalog/current-role checks; this is **not a general semantic policy migration**. Fresh K genesis is not proof that an existing **pre-K namespace** can be upgraded. Tests and observer/controller share one disposable CI host and trusted administrative plane.

## 2. Actual final-head CI and independent assessment

GitHub Actions verified **all eight final-head runs** `completed/success` on exact `9e768a4d1f6c97c429c36475237e132b8e3e7fc2`:

| Workflow | Final run | Evidence scope |
|---|---|---|
| K Push | [42449479460](https://github.com/alireza-anari/cac-project/actions/runs/42449479460) | Real H51, K17, authority mutation/recovery |
| K PR | [42449481947](https://github.com/alireza-anari/cac-project/actions/runs/42449481947) | Real H51, K17, mutation; actual proof/sensitivity job logs checked |
| H PR | [42449481940](https://github.com/alireza-anari/cac-project/actions/runs/42449481940) | Existing H51 and five inherited H mutation probes |
| Backend | [42449482021](https://github.com/alireza-anari/cac-project/actions/runs/42449482021) | 94 original distinct DB/security tests |
| C | [42449481926](https://github.com/alireza-anari/cac-project/actions/runs/42449481926) | 20 distinct C tests |
| D | [42449481922](https://github.com/alireza-anari/cac-project/actions/runs/42449481922) | 15 D tests, including intentional **historical security-failure reproduction** |
| F | [42449481890](https://github.com/alireza-anari/cac-project/actions/runs/42449481890) | 40 distinct F tests, assumed-W scope |
| Focused B | [42449481949](https://github.com/alireza-anari/cac-project/actions/runs/42449481949) | Supplemental repeated coverage, not distinct additional methods |

The measured inventory is **17 K + 51 H + 169 inherited = 237 distinct case methods across separate completed workflows**. Repeated methods, artifact scanners, mutation probes and extra focused-B are not included as newly distinct tests. Review of final K logs shows actual **`Ran 17 tests ... OK`** in both proof and sensitivity jobs, and checked logs contain retirement/current-policy guarded outcomes and persisted UNKNOWN. Other six runs were verified on the final SHA; Management did **not** independently execute the test suite or exhaustively inspect every log or artifact byte.

The reason-specific sensitivity removes the *control-role check only*, preserves an actual unauthorized policy2 CAS commit, fails the **original K02** assertion with `Policy retirement accepted a non-control role`, restores identical source bytes (recorded SHA-256 `c619aa3043e1342d97c50b814e14c95b98a586688442cb43b27c0668d4d29652`) and reruns the original assertion GREEN followed by K17 GREEN. Mutant test failure is **expected RED**, not a production exploit. Role-separated read-only source/selected-log reviewer found no P0/P1 within the bounded review; corrected an issuer-negative P2 discrimination issue before implementation commit. This is not external/custody certification.

**Critical negative evidence remains negative:** inspected final D job log reproduced `AssertionError: True is not false : Rolled-back anchor revived previous-owner authority`, followed by `S009D SECURITY FAIL/BLOCKED`. A green workflow harness that successfully *detects* that known attack is **not** a passing safety property; S0-09D remains **`FAIL_SECURITY`**.

## 3. Exact supported conclusion and exclusions

**Accepted only:** `K_POLICY_RETIREMENT_REAL_Q_SURVIVAL_EVIDENCE_PASS` for current genuine R majority, trusted current mandatory guard, real PG/PgBouncer and test-only controller/privileged roles. Committed policy-generation change and related guards have new real conditional evidence.

**Not accepted / still unresolved:**

- Responsive coherently rolled-back **R majority**, joint obsolete verifier+root restore, root re-genesis, same-ID physical clones, real independent admin/backup/key custody: **`UNSUPPORTED / SECURITY_UNPROVEN / NOT_RUN`**, `GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED` if no independently current mandatory guard survives.
- [E G1–G5 root-continuity blockers](https://github.com/alireza-anari/cac-project/issues/33): **P0 DESIGN_BLOCKED**, E1/E2 currently not qualified; S0-09J study closed as documentation only.
- True orphan `OPEN_UNKNOWN/FENCED_UNRESOLVED` Lane3 resolution: **P0 BLOCKED**, may require indefinite safe downtime.
- Literal old etcd **Raft snapshot/WAL physical import/restart**: **NOT_RUN** in H and K. Fresh learner replacement or logical W rollback does not substitute.
- Pre-K existing namespace upgrade/migration, general semantic policy migration/generation3, arbitrary compound crash cuts, common-administrator compromised guard: **NOT_DEMONSTRATED / NOT_RUN**.
- Historical S0-09D C-only rollback: **FAIL_SECURITY**, unchanged.
- [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1)/GATE-SOURCE BLOCKED; canonical architecture [Gate #9](https://github.com/alireza-anari/cac-project/issues/9) OPEN, security parents [#33](https://github.com/alireza-anari/cac-project/issues/33)/[#28](https://github.com/alireza-anari/cac-project/issues/28)/[#23](https://github.com/alireza-anari/cac-project/issues/23) OPEN. No accepted historical v3.37–39 source, full protocol, Production deployment, Sprint0 or IdP/onboarding acceptance.
- Product [Preview V0 Draft PR #44](https://github.com/alireza-anari/cac-project/pull/44) remains independent local/demo new-origin code, unmerged; no impact or new owner UX approval from K.

## 4. Disposition and next bounded research

[S0-09K Issue #45](https://github.com/alireza-anari/cac-project/issues/45) is **eligible for CLOSED only as bounded experimentally delivered evidence**, never as resolved catastrophe/root/Lane3/Production protection. Keep PR #46 DRAFT and UNMERGED as a traceable stacked experiment.

**Next separately authorized executable slice:** [S0-09L Issue #47](https://github.com/alireza-anari/cac-project/issues/47), real *physical minority-member etcd Raft WAL/snapshot* rollback/reintroduction under surviving, nonrestored current 3/5 original R voters, with current SQL/guard denial and healthy success controls. **No replay surrogate:** if authentic bytes cannot safely be imported, report `L_PHYSICAL_IMPORT_NOT_RUN` rather than treating a fresh learner/app journal as proof. Work must not alter surviving original current majority, run a clone concurrently with same member identity, claim restored-majority protection or discard true UNKNOWN. New Draft PR stacked on exact K head; independent source/log review and measured CI required.

**Formal vote:** `ACCEPT_BOUNDED_S0_09K_EVIDENCE_ONLY / S0_09L_PHYSICAL_MINOR_REPLAY_AUTHORIZED / SOURCE_AND_SECURITY_GATES_UNCHANGED / NO_MERGE_OR_PRODUCTION`.
