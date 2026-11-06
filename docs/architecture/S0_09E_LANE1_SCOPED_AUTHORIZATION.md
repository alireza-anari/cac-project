# CAC — S0-09E R1 Management Ruling: Lane 1 Authorization Only

**Date:** 2026-11-06  
**Decision authority:** Astra Management / CAC Architecture  
**State:** `LANE1_SCOPED_EXPERIMENT_AUTHORIZED / W_ROOT_UNPROVEN / LANE2_BLOCKED / LANE3_BLOCKED / RECOVERY_PROTOCOL_NOT_RATIFIED`  
**Tracking:** [S0-09E architecture #23](https://github.com/alireza-anari/cac-project/issues/23) remains OPEN; [S0-09F execution #26](https://github.com/alireza-anari/cac-project/issues/26) is the **sole implementation authorization**.  
**Sources:** [R1 design refinement](S0_09E_TARGETED_DESIGN_REFINEMENT_R1.md) at `29709ad3cb15380653deb7b1c1c52e88725d2a92`, [independent R1 delta review](https://github.com/alireza-anari/cac-project/blob/d10ced56dcd7a267a18fd5620ccc8c16a1856604/docs/security/S0_09E_R1_DESIGN_DELTA_REVIEW.md), [Draft PR #25](https://github.com/alireza-anari/cac-project/pull/25) exactly `d10ced56dcd7a267a18fd5620ccc8c16a1856604`.  
**Execution parent:** [Draft S0-09D PR #22](https://github.com/alireza-anari/cac-project/pull/22) exact previously verified head `ca043e2751ea1dbcb7aed3c1ed3d171a9bb1f0e2`; verify live state before branch creation.

## Decision

**Accept** the R1 independent assessment that the four former P0 *specification gaps* and three P1/one P2 refinements are sufficiently defined/excluded **only for a narrow request to test integration under explicit W-oracle assumptions**. **Authorize that limited Lane 1 experiment in Issue #26**, not a full W anti-rollback implementation, production design, KMS root, physical HA or any real-world recovery process.

The four P0 *security proof obligations* remain open; satisfying a contract definition does not establish the underlying safety property. The former S0-09D test of actual PostgreSQL C anchor rollback **still FAILS_SECURITY**, because prior owner A regained fresh issuance and scoped RLS after epoch2→1. Legacy result must remain visibly RED and must not be relabeled GREEN from the new candidate.

## Scope-specific experiment and threat partition

### Lane 1 — AUTHORIZED, ASSUMPTION-BOUND

An **isolated disposable W-oracle integration harness** may assume that an external W already provides linearizable/monotonic current owner and epoch, independently held root/policy identity, fresh authenticated permits, and durable OPEN/exclusion history unaffected by the A/B/C restore scope. A fake oracle is a **test fixture**, not evidence of real W custody; a same-host PostgreSQL test is not independent anti-rollback infrastructure.

Only the explicitly admitted guard/verifier version and logical actor incarnation may authorize. A prior C-only or pre-W restored guard must be quarantined from **all** issuance and SQL/RLS paths. Physical same-SID clones, nonclonability, privileged-superuser compromise and real root recovery are excluded/unproved.

The W permission lifecycle must be falsifiable: durable atomic OPEN-before-permit; first-use fresh W check; serialized revocation barrier; durable hold until trustworthy known local COMMIT/ABORT outcome; unknown result maintains OPEN_UNKNOWN; successor cannot gain READY/live permits while old authorized work may still commit. Correct DENY on W outage must be distinguished from deliberate W-enforcement mutation RED; a late response and a reused PgBouncer backend cannot authorize stale generations.

**Authorized tests:** real C rollback against *non-rolled-back assumed W*, stale contexts/reused pool, delayed permits, outage/partition in fixture, clone/old-verifier **admission denial within stated scope**, in-flight commit vs takeover, lost acknowledgments and operation holds with crash cuts. Positive scoped controls plus expected actual fault denials and targeted mutation sensitivity; independent later read-only security review. All actual test evidence remains to be generated; current W result `NOT_RUN`.

### Lane 2 — BLOCKED / NOT_RUN

**No approval** to develop or attest a real anti-rollback W root/cluster/consensus or key-custody mechanism; no W snapshot rollback/own rebootstrap safety, same-identity physical clone/power loss/partitions, signer/root retirement or complete physical fencing claim. A successful Lane1 test proves only *conditional integration*, not this independent premise.

### Lane 3 — BLOCKED / NOT_RUN

**No safe orphan OPEN recovery or clearing**, even manual or timer initiated. Losing COMMIT ACK, a missing session or a signed operator approval cannot establish a prior transaction's outcome. An unknown/unresolved OPEN remains durable, blocks successor readiness and may cause indefinite safe downtime. A fixture reset between independent tests is never a recovery procedure.

## Evidence and acceptance rules

- Existing 94 inherited +20 C +15 D = **129 previously observed distinct GREEN** cases in separate workflows remain intact and are rechecked where applicable. They are not W-oracle tests.
- Preserve unchanged original `test_anchor_rollback_must_not_revive_previous_owner` and **legacy C-path SECURITY FAIL**. Create an independent, explicitly named W-enforced path; it must DENY old-owner issuance/RLS on restored C, and deliberately removing W enforcement must trigger the targeted **RED**. Do not invert assertions or allow C-only fallback.
- Actual nonowner PostgreSQL/PgBouncer fixtures, SQL/ACL changes limited to isolated experimental branch, full rollback/reapply and restoration evidence; SHA-pinned Push/PR merge CI, proof logs and independent security source review. New test count reported separately, no invented PASS or mislabeled expected security failure.
- Fail on unclear W continuity, stale root/guard admission, delayed permit, incomplete OPEN lifecycle, or orphan clearing. Strict `PASS / EXPECTED_MUTATION_RED / FAIL_SECURITY / BLOCKED / NOT_RUN` classification.
- Stacked **Draft** work branch `work/s0-09f-w-oracle-deny-only-poc` from PR #22, Draft PR targeting `work/s0-09d-fencing-proof-gaps`; no PR to main, no merging docs PR #24 or #25 to obtain them. Use their exact pinned SHA contents for design reference.
- All PRs #11/#16/#18/#20/#22/#24/#25 remain Draft, OPEN, unmerged; #23 remains OPEN and #26 records the experimental delivery.

## Governance unchanged

`SOURCE-001 / GATE-SOURCE = BLOCKED`, [Architecture baseline #9](https://github.com/alireza-anari/cac-project/issues/9) OPEN, `NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`. APR-033/034/035/036 unchanged. No canonical baseline promotion, production deploy, actual customer keys/identity, onboarding or Sprint 0 completion.

**The only permitted positive interpretation of Lane 1 SUCCESS:** `ASSUMED_W_DENY_ONLY_INTEGRATION_POC_PASS`, with real W-root/anti-rollback and orphan recovery still P0 UNPROVEN. This vote authorizes starting the experiment, **not** accepting its design/security outcome in advance.
