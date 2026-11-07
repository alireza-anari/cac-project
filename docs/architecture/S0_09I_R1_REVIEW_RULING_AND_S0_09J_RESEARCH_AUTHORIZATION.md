# CAC — S0-09I R1 Independent Delta Ruling and S0-09J Research Authorization

**Date:** 2026-11-07  
**Owner:** Astra Management / Security Architecture  
**Architecture issue:** [#33](https://github.com/alireza-anari/cac-project/issues/33), parent [#28](https://github.com/alireza-anari/cac-project/issues/28), [#23](https://github.com/alireza-anari/cac-project/issues/23)  
**Independent review:** [PR #35](https://github.com/alireza-anari/cac-project/pull/35), head `9134fcf3879f04f4f99fe448bbc782284ac3a572`, [R1 read-only delta report](https://github.com/alireza-anari/cac-project/blob/9134fcf3879f04f4f99fe448bbc782284ac3a572/docs/security/S0_09I_R1_SCOPE_AND_E_FEASIBILITY_DELTA_REVIEW.md), docs-only against main `724d7a418ed82d3464ec95e6f8c968a2a59df366`.  
**Research authorization:** [S0-09J Issue #36](https://github.com/alireza-anari/cac-project/issues/36) — **documentation-only feasibility comparison, no PoC**.  
**Disposition:** `R1_SCOPE_ACCEPTED_FOR_GOVERNED_RESEARCH / E_G1_G5_DESIGN_BLOCKED / MAJORITY_CATASTROPHE_UNSUPPORTED / DOCS_ONLY_S0_09J_AUTHORIZED / NOT_MERGED`.  
**Source:** `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`.

## Formal management vote

**ACCEPT** the independent scope verdict `R1_SCOPE_ACCEPTABLE_FOR_GOVERNED_RESEARCH` as an assessment that R1's requirements are sufficiently honest for a **separately governed research decision**. It is **not** a claim that E is feasible, that a terminal antirollback primitive exists, that R/E/PostgreSQL writes are atomic, or that recovery of an R majority is secure. PR #35 contains a **single added Markdown file** and reports no executed tests, code changes or CI. This review was read-only; it does not independently certify prior H infrastructure.

**Retain interim Option A.** Restoring a coherently responsive stale R majority (or jointly restoring R and all verifier policy) is **UNSUPPORTED**. A quarantine/deny guarantee depends on separately trusted still-current enforcement covering all old and live routes. When every enforcement root can rewind, `GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED`; neither a written policy nor an operator runbook can prove universal denial. Intact current-state restart is distinct from unverified older snapshot restore.

**Explicit, separate management authorization:** Issue #36 permits **only one bounded, documentation-only S0-09J feasibility study**, not coding or a physical/hardware investigation requiring deployment, secrets or account access. Unlike another round of generic R0/R1 rewriting, its deliverable must compare two *concrete failure-envelope candidate families* for E, or reject both as infeasible. The study does **not** choose a vendor, product, crypto algorithm, KMS/HSM, workflow or accepted recovery protocol. Any later implementation, active experiment, actual independent custody test or Production choice requires a **new independent review and management vote**.

## Findings accepted, never closed by language

| Finding / gate | Review disposition | Required research evidence |
|---|---|---|
| I-P0-01 / **G1** terminal E continuity | Requirements `DESIGN_SPECIFIED`; primitive/custody `DESIGN_BLOCKED / NOT_RUN` | Exact latest surviving fact, E own backup/restore/reset/rotation/rebootstrap and mandatory independent verifier/custody; no restorable shared root |
| I-P0-02 / **G2** complete pending obligations | DETECT_AND_DENY vs recovery distinguished; reconstruction `DESIGN_BLOCKED` | Complete OPEN/UNKNOWN bodies and absence/checkpoint proof; a digest can indicate stale R but cannot infer an empty pending set or local outcomes |
| I-P0-03 / **G3** atomic cross-root/local transitions | Cuts/rejection criteria specified, **not a protocol**; `DESIGN_BLOCKED` | Exact OPEN/first-use/revoke/local PG COMMIT/CLOSE ordering and ACK-loss conservative outcomes; no successor READY while any old authorized work may commit |
| I-P0-04 / **G4** current verifier/old-route control | Mandatory stop rule stated; actual independent enforcement `DESIGN_BLOCKED` | Authenticated bootstrap/policy floor, all SQL/issuer/RLS/private/old/pool/incumbent routes, administrative custody and old-signing-policy rejection |
| I-P0-05 / **G5** resource continuity across incarnations | No-laundering prohibition specified; realizability `DESIGN_BLOCKED` | Resource-bound predecessor obligations across root/namespace/actor/DB identities; hard fence, new key and human approval not equal to positive outcome |

**Retain I-P1-01..03:** real incident detection and verified quarantine receipts; PG operation/incarnation-specific outcome witness and privileged custody; qualitative cost/availability/failure domains. **Retain I-P2-01:** immutable provenance and no promotion of `DESIGN_SPECIFIED` to `SECURITY_PROVEN`.

### Critical interpretation rules from the independent reviewer

1. Recovering an ACK/status for an **already authoritatively CLOSED exact operation** is not an independently invented closure. Any durably **OPEN_UNKNOWN** effect without positive exact outcome remains **Lane3 P0 BLOCKED**. Neither an E status query, timeout, physical hard fence nor a renamed root permits release.
2. A legitimate `FIRST_USE_GRANTED` before `REVOKE_INTENT` may have in-flight effects after revoke, while the old durable hold prevents successor READY. An **unadmitted old route bypassing the current guard** is a different P0 failure. Blocking a new connection does not retroactively stop an incumbent transaction.
3. A signed fresh reply from a **coherently rewound** root need not be current. A standalone monotonic counter without a bound complete journal, or a backup-restorable witness with shared administrator and verifier, is not evidence of majority rollback safety.

## Distinct proposed research lanes — neither approved for implementation

- **E1:** independent authenticated current-head witness/service with a terminal nonrollbackable current sequence/head, key/manifest continuity, admissible transition validation, separately controlled restore and enforceable guard. Failure to identify an actual surviving fact and independent control = `NO_CREDIBLE_E_CANDIDATE`.
- **E2:** protected monotonic root plus separately complete authenticated operation journal, with proof of binding between counter/head, unresolved OPEN and policy, actual safe custody/reset/replace story and current guard. A bare HSM, signature, counter, WORM artifact or duplicate database is insufficient.

For each, research **G1–G5 and P1 operations** under a precisely described majority-root catastrophe/old-policy restore. Distinguish `DETECT_AND_DENY` from `RECONSTRUCT_AND_CONSERVATIVELY_AUTHORIZE`; even perfect reconstruction may reveal UNKNOWN and force indefinite safe downtime. Show why a purported independent administrative/control-plane boundary is or is not real. Prefer explicit `NO_VIABLE_E` over another assumed W/E oracle. No numbers for costs, RPO/RTO, throughput or latency without actual data.

## Experiment provenance and exclusions

- S0-09D C-only original rollback: actual **`FAIL_SECURITY`**, unchanged.
- S0-09H current non-restored five-voter majority-survival tests: bounded observed evidence only; previous **169 + 51 = 220 distinct DB/security methods across separate suites**, plus 2 artifact-only methods, **not E** or majority catastrophe security evidence.
- Real **root policy retirement** and literal old Raft snapshot/WAL import remain **`NOT_RUN`**, distinct from signer retirement and fresh learner replacement.
- Lane3 orphan OPEN clearing stays **`P0 BLOCKED / NOT_RUN`**. Real root catastrophe, simultaneous old verifier, admin/backup/key custody, physical cloning, fail-closed at every old path and cross-root safety remain **`SECURITY_UNPROVEN / NOT_RUN`**.
- No new executable code, SQL, workflow, tests, CI, KMS/HSM purchase, restore experiment, Production root, root recovery, original source reconstruction or merge.

## Next gate and governance

The **only newly authorized work** is [S0-09J #36](https://github.com/alireza-anari/cac-project/issues/36), producing `docs/architecture/S0_09J_EXTERNAL_CONTINUITY_FEASIBILITY_R0.md` in a docs-only **Draft PR targeting main**. The deliverable compares E1/E2 and a no-credible-E result, records G1–G5 plus P1/P2, and proposes only a *future* independent falsification plan. Require an adversarial **read-only review**, then a distinct management decision before any new experiment. S0-09J issue creation is authorization for **feasibility documentation only**.

Issues #33/#28/#23 and baseline Gate #9 remain OPEN; SOURCE-001 #1/GATE-SOURCE BLOCKED. All pre-existing Draft PRs including #35 OPEN/DRAFT/UNMERGED; no APR-033..036 change, canonical historical source, Sprint0, Production, real identity/onboarding, protocol, root/recovery security approval.

**Formal vote:** `S0_09I_R1_REVIEW_ACCEPTED_WITH_LIMITS / DOCUMENTATION_ONLY_FEASIBILITY_S0_09J_AUTHORIZED / E_NOT_PROVEN / NO_LANE2_OR_LANE3_EXECUTION`.
