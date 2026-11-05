# CAC — S0-09D Architecture Review Decision

**Decision date:** 2026-11-06  
**Authority:** Astra Management / CAC Architecture  
**Reviewed stacked Draft PR:** [#22](https://github.com/alireza-anari/cac-project/pull/22)  
**Final PR head:** `ca043e2751ea1dbcb7aed3c1ed3d171a9bb1f0e2`  
**Executable head:** `8b490bfe5a64ac62c0a8382e77ce6a45486b4f04`  
**Parent branch / SHA:** `work/s0-09c-recovery-fencing-poc` / `8bd81906f6edbf1732e22c46ca8925c7dec1a595`  
**Decision:** `S0-09D_EVIDENCE_ACCEPTED_WITH_LIMITS / ANCHOR_ROLLBACK_SECURITY_FAIL / RECOVERY_PROTOCOL_REJECTED_FOR_THIS_MODE / ARCHITECTURE_ACCEPTANCE_DEFERRED / NOT_MERGED`  
**Provenance:** `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`  
**Baseline gate:** [#9](https://github.com/alireza-anari/cac-project/issues/9) **OPEN**. **SOURCE-001 / GATE-SOURCE:** [#1](https://github.com/alireza-anari/cac-project/issues/1) **BLOCKED**.

## Executive architecture disposition

**ACCEPT the rigorously bounded S0-09D synthetic experiment and its honest negative evidence. REJECT anchor rollback as a safe authority-recovery mode in the candidate design. DO NOT ratify the recovery-fencing/trusted-context security protocol.**

The test reproduces a real **P0 unsafe authority revival**: after B takes over (epoch 2), a logical restore of the C anchor schema from an earlier epoch-1 snapshot at the *same C system identity* makes the previous owner A ready again and allows A to **issue a fresh context token and perform scoped RLS access**. B becomes unready. The original safety assertion remains RED; it was **not** removed, inverted, treated as GREEN or excused by a CI-success label.

This does not show an unprivileged runtime bypass when the originally stated “trusted, non-rollbackable C anchor” assumption holds. Instead it demonstrates that the product cannot safely treat a rollbackable C as its ultimate recovery authority. A PostgreSQL system identifier and WAL durability flags do **not** provide an independent monotonic anti-rollback root.

### Exact source and CI evidence

- [Technical handoff](https://github.com/alireza-anari/cac-project/blob/ca043e2751ea1dbcb7aed3c1ed3d171a9bb1f0e2/docs/S0_09D_HANDOFF.md), [independent read-only review](https://github.com/alireza-anari/cac-project/blob/ca043e2751ea1dbcb7aed3c1ed3d171a9bb1f0e2/docs/security/S0_09D_FINAL_READ_ONLY_REVIEW.md), [proposed CR-S0-09D-001](https://github.com/alireza-anari/cac-project/blob/ca043e2751ea1dbcb7aed3c1ed3d171a9bb1f0e2/docs/changes/CR-S0-09D-001-authority-recovery-boundary.md) and [18-run staged evidence manifest](https://github.com/alireza-anari/cac-project/blob/ca043e2751ea1dbcb7aed3c1ed3d171a9bb1f0e2/docs/evidence/S0_09D_CI.json) were reviewed.
- The exact PR head `ca043e2751ea1dbcb7aed3c1ed3d171a9bb1f0e2` differs from its executable proof SHA `8b490bfe5a64ac62c0a8382e77ce6a45486b4f04` by **one documentation-only commit** (handoff, proposed CR, manifest, independent review), confirmed by GitHub compare. No executable SQL/broker/worker/test weakening in the final documentation commit.
- [S0-09D final Push 42105526148](https://github.com/alireza-anari/cac-project/actions/runs/42105526148) and [PR synthetic-merge 42105536094](https://github.com/alireza-anari/cac-project/actions/runs/42105536094) are both SUCCESS, exact final PR head. **Both actual decoded job logs explicitly show**: `S009D SECURITY ROLLBACK WITNESS epoch2->1 old owner readiness True new owner readiness False`; `SECURITY FAIL/BLOCKED anchor rollback`; exact latest-state restoration; and subsequently 20 retained C tests GREEN. The SQL rollback test demands successful old-owner issuance and scoped RLS before its unchanged assertion fails; the test runner requires exactly that safety failure.
- [Full backend Push 42105526131](https://github.com/alireza-anari/cac-project/actions/runs/42105526131) and [full backend PR 42105535970](https://github.com/alireza-anari/cac-project/actions/runs/42105535970) are SUCCESS; the actual logs confirm 43 inherited foundation, 24 S0-09A, and 27 S0-09B distinct tests, each run twice around its schema/SQL rollback and reapply. Supplemental [C PR 42105536034](https://github.com/alireza-anari/cac-project/actions/runs/42105536034) and [B focused PR 42105535941](https://github.com/alireza-anari/cac-project/actions/runs/42105535941) are also SUCCESS.
- **129 distinct GREEN cases across separate workflows**: 94 inherited + 20 S0-09C + 3 independent mutation targets + 4 new combined pool cases + 8 bounded authority tests. This is **not** one 129-case monolithic suite; each applicable cohort and repeated run must be distinguished from distinct test cases. The separate *anchor rollback safety invariant is FAIL_SECURITY* and **is not included as GREEN**.
- PostgreSQL 17.11 in three separately initialized clusters on **one CI host**, and pinned PgBouncer 1.22.0 `1.22.0-1build4`. These are not independent physical/HA failure domains. Source/log review and prior separate read-only reviewer did not execute a new independent Management PostgreSQL run, and are not external security certification. GitHub artifact digests were reported by GitHub, not independently recomputed ZIP hashes.

## Accepted experimental observations (only within checked scope)

1. **Candidate sensitivity:** separately weaken monotonic compare-and-swap, online SQL guard and durable OPEN reservation protection in synthetic SQL; each targeted security assertion went RED for the intended reason, with zero errors/skips, and original function text, owner, ACL, SECURITY DEFINER and settings were restored before the identical GREEN target and C20 suite. The inherited SQL/Gate suites remain unchanged.
2. **Actual PgBouncer + C composition:** the unchanged C-fenced authorization/RLS was exercised through a one-backend transaction-mode pool, with same PostgreSQL backend PID, distinct full transaction IDs, prior positive scoped access, and stale token/ticket denied across commit, rollback, cancellation and held-gate takeover. Runtime authorization was pooled; issuer/readiness were directly connected and **not** covered by the combined pool claim.
3. **Bounded authority failures:** a logically copied anchor at a **different** PostgreSQL system identifier, a read-only anchor actor session, malformed attestation, a refused SQL-to-anchor channel, CAS contenders behind an observed row lock, committed receipt drop/retry and missing dblink extension were tested with actual PostgreSQL and restored to known-good fixture state.
4. **Orphan protection, not recovery:** an issuer crash leaves an independently committed OPEN intent; across C SIGKILL/restart, fresh guarded authorization and takeover remain denied. This is the correct conservative safety outcome, but **safe externally witnessed orphan reconciliation was neither designed to acceptance nor implemented**. An orphan may cause indefinite fail-closed unavailability. Test fixture teardown is not an operational recovery API.
5. **Failfast runner safety:** an earlier candidate's restoration-before-reset sequencing defect was fixed at executable head with failfast; no bypass introduced in the inherited security controls.

## Explicitly failed, blocked and not executed

| Classification | Condition |
|---|---|
| **P0 — FAIL_SECURITY / BLOCKED** | Same-C-identity logical anchor rollback `epoch 2 → epoch 1` revives prior owner A, new issuance and RLS. This recovery mode is REJECTED. |
| **P0 — BLOCKED** | Independent monotonic anchor anti-rollback identity/custody, externally governed fencing of stale primaries/signers, and an externally witnessed safe orphan OPEN recovery protocol are absent. No timer-only clearing or relaxed OPEN rule is allowed. |
| **NOT_RUN** | Physical PGDATA/PITR rollback, two simultaneously live same-identity physical anchor clones, standby promotion, asymmetric partitions, wire-level lost COMMIT acknowledgements, full missing-role/permission faults, multi-host HA/quorum and full pooler-crash/pooled-issuer concurrency. A logical clone with a different system identifier is not a same-identity physical-clone proof. |
| **P1 / limitation** | Single host; bounded deterministic schedules; targeted bootstrap checks; Production TLS, KMS/key custody, bearer theft, v2 canonical wire format, timing policy, IdP/MFA/CSRF/onboarding, performance and failure-domain planning all unratified. |
| **P2 / nonblocking** | Workflow path filters do not automatically trigger CI for design/plan-only `docs/superpowers` modifications. This is not an observed runtime bypass. |

## Architecture resolution and next governance step

The candidate PostgreSQL C anchor **may not be backed up/restored into operational authority without a new independently approved anti-rollback/fencing protocol**. This is not merely an operations runbook warning; the observed safety invariant fails on restored state.

The independent authority and recovery contracts must be decided **before another broad implementation attempt**. Open [S0-09E Architecture Issue #23](https://github.com/alireza-anari/cac-project/issues/23) as P0 **DESIGN-FIRST**, tasked with comparing anti-rollback root alternatives (separately governed high-watermark witness vs. new non-rollback identity/key epoch plus provable old-signer hard fencing), specifying authority epoch/identity activation and failure behavior, and safe externally witnessed orphan resolution. The issue is not yet permission to pick a vendor, KMS, HA/quorum technology or to write the next experimental PoC.

All existing experimental code remains unmerged. [Execution Issue #21](https://github.com/alireza-anari/cac-project/issues/21) may close only as a **completed bounded adversarial investigation and evidence delivery**; its failed P0 security criteria are **not resolved**, and are transferred as explicit architectural blockers to #23. No security/protocol acceptance is implied by the issue closure.

Keep [Draft PR #22](https://github.com/alireza-anari/cac-project/pull/22) and prior [#20](https://github.com/alireza-anari/cac-project/pull/20), [#18](https://github.com/alireza-anari/cac-project/pull/18), [#16](https://github.com/alireza-anari/cac-project/pull/16), [#11](https://github.com/alireza-anari/cac-project/pull/11) **open, Draft and unmerged**. `SOURCE-001 / GATE-SOURCE` **BLOCKED**; Architecture baseline #9 **OPEN**. `NEW_BASELINE_ACCEPTED` **NOT GRANTED**. No Production release, real identity/onboarding, recovery-feature enablement or Sprint 0 completion. APR-033/034/035/036 remain governing and unchanged.

**Final ruling:** `S0-09D_EXPERIMENT_EVIDENCE_ACCEPTED_WITH_LIMITS / ANCHOR_ROLLBACK_MODE_REJECTED / P0_SECURITY_GATE_BLOCKED / TRUSTED_CONTEXT_PROTOCOL_PROPOSED`.
