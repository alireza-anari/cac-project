# CAC — S0-09I R1 | Root-Catastrophe Scope Ruling and E Feasibility Gates

**Date:** 2026-11-07  
**Authority:** Astra Management / CAC Security Architecture  
**Architecture issue:** [#33](https://github.com/alireza-anari/cac-project/issues/33); parent [#28](https://github.com/alireza-anari/cac-project/issues/28) / [#23](https://github.com/alireza-anari/cac-project/issues/23)  
**R0:** [Root-majority catastrophe design](S0_09I_ROOT_MAJORITY_CATASTROPHE_DESIGN_R0.md), baseline management main `e3f72ea9a1e355a574c52b12c3ae4fed6464ab01`  
**Independent review:** [S0-09I R0 read-only review in Draft PR #34](https://github.com/alireza-anari/cac-project/blob/5e903c26f43ea1cba52770ecedc6925b8257b9f5/docs/security/S0_09I_R0_ROOT_CATASTROPHE_READ_ONLY_REVIEW.md); exact head `5e903c26f43ea1cba52770ecedc6925b8257b9f5`  
**Disposition:** `R0_SCOPE_ACCEPTED_FOR_FURTHER_DESIGN / OPTION_A_UNSUPPORTED_CATASTROPHE_RESTORE_INTERIM / E_P0_FEASIBILITY_GATED / NO_POC_OR_PRODUCTION_AUTHORIZATION`  
**Origin:** `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`.

## 1. Formal architectural position

Astra Management **accepts the independent review's narrow vote**: R0's **unsupported majority-restore policy** is a defensible scope statement for the experimental architecture. It does not establish that a responsive rewound majority will be detected, that old SQL/issuer paths are all disabled, or that globally fail-closed behavior is available when the majority **and all verifier roots** are jointly restored.

**Interim choice A stays in effect:** do not declare restored R-majority snapshots safe; do not automatically re-genesis, re-admit retired policies, clear UNKNOWN or promote a successor after unverifiable catastrophe. If an independent mandatory current trust/control plane is actually still enforceable, it **must quarantine and deny**. If this plane is absent or potentially jointly restored, record `GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED / SECURITY_INCIDENT`, not `SAFELY_RECOVERED`. A procedural prohibition is **not** a runtime protection proof.

**Research candidate B/E stays open, but is not approved or selected.** The following refinements define *requirements and rejection criteria* for future feasibility design. They do **not close** the five review P0 findings and do not invent a terminal root primitive or a working three-system atomic commit protocol. No implementation, PoC, restore experiment, vendor/hardware/KMS choice or Production deployment is authorized.

## 2. Acceptance threshold for E — terminal independent root (I-P0-01)

To advance beyond research, a future E proposal MUST name:
- The precise **irreversible/monotonic fact** and what constitutes latest current authority: namespace and protected-resource identity, root incarnation, committed state-transition index, actor/owner generation, admitted signer/verifier policy and a complete unresolved-operation commitment (or a demonstrably equivalent current authenticated state). A key signature alone is not a highest-head fact.
- The **physical and administrative mechanism** making this fact survive the **specific** R-majority/W/verifier restore scope being supported. Enumerate reset/reimage/backup, firmware and credential restore, quorum loss, privilege escalation, custody/owner rotation, E replacement/rebootstrap, network split and cross-account access. A “quorum”, “hardware-backed” or “append-only” label is insufficient.
- The **root-of-trust termination**: which key, installation manifest, policy and current verifier enforce E, which actors may change them, and what happens if those are also destroyed or restored. There need not be protection from every adversary, but the supported boundary must not silently assume an independent root that does not exist.
- Exactly what E can do when its own current history or signer policy is lost: **deny/not-ready**, potentially indefinitely. No silent new genesis, lower epoch or automatic key reset into old authority.

Compare at least **two implementable but unapproved** continuity families in a later feasibility memo: independently governed current-head service with separately protected high-watermark, versus a credible protected monotonic state/receipt service plus durably complete ordered log. Document each failure-domain and replacement/custody limits; no provider or numeric SLA selection now.

**Hard rejection:** E and all mandatory verifiers are snapshot-restorable by the same controller as R, or E can freshly attest an arbitrary caller-provided higher sequence without checking legal prior state, unresolved obligations and key policy. This is merely relocated rollback vulnerability.

## 3. Completeness vs detection — durable OPEN/UNKNOWN (I-P0-02)

A current cryptographic commitment can establish **inconsistency**, but cannot restore missing transaction facts. Two distinct capabilities must be reported:

- `DETECT_AND_DENY`: a surviving E authenticated head proves a restored R view is stale/incomplete. Missing OPEN bodies, checkpoint suffix, prior authorized actor/transaction mapping or tombstones means permanent **NOT_READY**, even if stale rollback was detected.
- `RECONSTRUCT_AND_CONSERVATIVELY_AUTHORIZE`: the exact authoritative **complete pending OPEN/UNKNOWN set** and policy/head/actor state can be independently reconstructed and authenticated to a current E committed index; only then may normal rules consider a new owner. This is **NOT PROVEN** and requires a future design for recoverable bodies, predecessor/ancestry proof, journal retention, checkpoints, tombstones and completeness witnesses.

The E commitment must bind **every protected resource**, root/namespace/physical actor incarnation, operation ID and digest, idempotency key, local PostgreSQL incarnation/transaction binding, state OPEN/UNKNOWN/positively CLOSED, signer/verifier policy and revocation barriers. Same-epoch new operations can change safety, so `epoch` alone is insufficient. Compaction/retention may not erase live UNKNOWN, its outcome obligations or the proof of absence of other pending work. Unverifiable gaps are **not** empty sets.

E cannot independently infer a PostgreSQL COMMIT, aborted prepared transaction or external effect from a log root. The local outcome witness remains a separately trusted dependency and Lane3 clearing is still forbidden.

## 4. Cross-R/E/PostgreSQL safety contract (I-P0-03)

Do **not** treat two linearizable reads or “R then E” staging as a proven atomic transaction across R, E and PostgreSQL. Any later protocol proposal MUST give a single unambiguous authorization/permission linearization rule and a falsifiable state-transition model that covers:

1. **OPEN-before-first-permit:** the precise operation, resource, actor, epoch and transaction binding must be durably included in **both** current decision evidence and complete E-continuity before a permit can become usable. If R or E ACK is lost, the caller queries original idempotency key+digest using a current independently authenticated decision; no guessed success, altered retry or second epoch.
2. **Grant vs revoke:** define a serialized `FIRST_USE_GRANTED` / `REVOKE_INTENT` order including delayed signed replies and a first-use check bound to the exact currently admitted PostgreSQL transaction. A grant preceding revoke can permit old in-flight work, **but successor READY must be excluded until that work is positively resolved and CLOSED**. A grant following revoke is denied. Merely comparing R/E heads at one instant does not revoke previously granted work.
3. **CLOSE and local outcome:** never remove a hold merely on client disconnect, missing session, TTL, fence, E/R leader restart or operator approval. Require exact, durably known PG COMMIT or ABORT/effect evidence matched to operation+incarnation and then a correctly ordered E/R close. Lost local outcome/CLOSE ACK => hold persists as OPEN_UNKNOWN unless status is positively established.
4. **Divergence/crash cuts:** R OPEN committed but E unacknowledged, E OPEN committed but response lost, old permit delayed past revoke, E ahead of R, R ahead of E, E head stale after failover, PG commit observed but E CLOSE unknown, incomplete checkpoint replay and new-root admission with old obligations. In every ambiguous window, fail to **authorize NEW** work and never declare successor READY while a prior authorized old transaction might still commit.

A future proposal must prove or explicitly falsify these cases with a model and reason-specific adversarial schedules **before** asking permission to implement. No 2PC, lease, wall-clock timeout, signed-only receipt or transport/crypto format is selected in this R1. Deadlock/indefinite denial is acceptable under the scoped *safety-only* design; it must not be mislabeled as availability success.

## 5. Mandatory current guard and old-route exclusion (I-P0-04)

E can protect **only** paths that cannot bypass it. For any supported restore, require an independently held approved *installation and policy floor* that cannot be rolled back with W/R/PG:

- explicit current root/namespace, E and R root identities, signer-key and verifier-policy minimum epochs, admitted guard build/function hashes, approved SQL roles/RLS/ACLs, current actor incarnation and independent manifest enrollment. Restored pre-E / C-only code, obsolete SQL SECURITY DEFINER routines and signer keys are **not** automatically trusted.
- exhaustive route inventory: direct issuer, application/transaction context, SQL guard/RLS, private functions and direct DB roles, PgBouncer **existing** server/client backends, existing active/prepared transactions, alternate listeners/admin paths, old/clone actors and re-enrollment/rebootstrap. `NOLOGIN` and deny of new connections do **not** prove old in-flight work cancelled.
- evidence that the **mandatory trusted enforcement plane survives** the claimed R/E restore and can quarantine every old route, not only a new verifier service or UI status flag. A stale verifier cannot self-certify its current build or lower the policy floor from an older database image.
- explicitly exclude or independently constrain PostgreSQL superuser, common cloud/admin/root controller and PG outcome observer compromise. Do not claim these are already protected by the H same-host CI tests.

**Stop condition:** if any old credential, loaded verifier, SQL/issuer path or incumbent pooled transaction can act on a protected resource without E/current admission, catastrophic restoration is UNSUPPORTED and universal deny cannot be claimed. Mark `DESIGN_BLOCKED / GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED`.

## 6. Resource continuity on root re-enrollment (I-P0-05)

**A new root ID, namespace, key, actor, database incarnation, cluster ID or manifest is not a fresh set of authorization obligations for an unchanged protected resource.** Candidate re-enrollment must carry a resource-bound predecessor link and all unresolved OPEN/UNKNOWN from prior incarnations. No switch to a different namespace can launder an old effect, authorize successor B while prior A may still commit, or erase idempotency/tombstones.

For current R0, **root re-genesis or identity replacement cannot return a protected resource to READY after unverified catastrophe**. Human recovery approval, hardware replacement receipt and physical hard fence alone are not positive evidence of every old local transaction outcome or external effect. New resource provisioning can be studied only when its isolation from all old protected resources and external effects is independently demonstrated. Lane3 orphan release is **not** part of this design, and no exception is introduced here.

## 7. Remaining P1 and P2 obligations / qualitative feasibility

| ID | Requirement before an implementation request | Present disposition |
|---|---|---|
| I-P1-01 | Incident-trigger proof: distinguish silent responsive rewind, unavailable majority and intact restart; audited old-route coverage, evidence for independently verified isolation; do not elevate `ISOLATION_REQUESTED` to `VERIFIED_QUARANTINED` without actual independent proof | SECURITY_UNPROVEN / NOT_RUN |
| I-P1-02 | Transaction outcome and actor custody: precise PG database/incarnation/transaction/effect receipt, observer/operator superuser/restore powers, missing ACK and prepared-tx state; PG observer rollback may invalidate closure evidence | SECURITY_UNPROVEN / NOT_RUN beyond H |
| I-P1-03 | A vs B/C operational economics: account/backup/failure-domain diagram, root enrollment and physical replacement ceremonies, sustained E request rate and journal/hold growth, exit from outage; no guessed numeric RPO/RTO, availability, latency or cost | NOT_RUN / unpriced |
| I-P2-01 | Version status with exact provenance, no shorthand `UNSUPPORTED_FAIL_CLOSED` without conditional enforcement qualifier. Historical D rollback actual FAIL_SECURITY; H's 169 inherited+51 new=220 distinct DB/security cases across **separate** workflows +2 artifact methods and five mutation controls; no E experiments | Documentation refinement only |

### Required feasibility gate matrix (the five P0 findings are NOT CLOSED)

| Gate | Exact proof or design deliverable needed before requesting a real E PoC | Current |
|---|---|---|
| G1 Terminal E continuity | Named primitive, immutable latest-head and its **own** reset/restore/custody/verification threat matrix | DESIGN_BLOCKED |
| G2 Journal availability | Complete pending OPEN/UNKNOWN and idempotency/retirement replay, or detection-only indefinite exclusion | DESIGN_BLOCKED |
| G3 Atomic transitions | Explicit R/E/PG ordered state machine with counterexample traces and lost-ACK safety; no successor overlap | DESIGN_BLOCKED |
| G4 Trusted verifier | Mandatory all-route, old-connection and restored-policy isolation with independently protected admission | DESIGN_BLOCKED |
| G5 Root/resource reincarnation | Resource continuity, no old-work laundering, old-root signer/actor retirement and no unknown clearing | DESIGN_BLOCKED |

**No gate can be converted to PASS merely by reviewing this R1.** This document clarifies a future *testable contract*; implementation security and real physical independence remain NOT_RUN. Reviewer may recommend whether an E option is **worth detailed feasibility design**, not authorize it.

## 8. Immediate project direction

1. **Approve the restricted Option A scope as the current experimental support policy**: no majority/root-catastrophe restore; do not claim global fail-closed without independently evidenced guard and old-route coverage. Record indefinite downtime and security-incident possibility clearly.
2. **Keep Option B/E and protected-root Option C in FEASIBILITY_ONLY**, not in the committed Product architecture or implementation backlog. An additional mock/oracle does not improve on S0-09F. First demand a concrete custody/failure-domain architecture, complete operation history availability and cross-R/E proof obligations.
3. **Next permitted work:** one **focused independent read-only design review** of this R1, specifically challenging whether it faithfully addresses I-P0-01..05 and whether Option A's limits are honest. Separately, a feasibility design may be proposed in Issue #33 after an explicit Management vote; not by default.
4. Do **not** dispatch policy-retirement or literal stale Raft snapshot/WAL tests just because H's missing evidence is listed here. Both remain NOT_RUN and would need a separate authorized test task.

**Independent delta review output if commissioned:** `docs/security/S0_09I_R1_SCOPE_AND_E_FEASIBILITY_DELTA_REVIEW.md` in a **docs-only Draft PR targeting main**. Review verdicts should be `R1_SCOPE_ACCEPTABLE_FOR_GOVERNED_RESEARCH`, `TARGETED_DESIGN_REFINEMENT_REQUIRED`, or `UNSUPPORTED_SCOPE_INSUFFICIENT`, and must not imply real E proof or execution authorization.

## 9. Nonnegotiable governance

[Architecture #33](https://github.com/alireza-anari/cac-project/issues/33), parents [#28](https://github.com/alireza-anari/cac-project/issues/28)/[#23](https://github.com/alireza-anari/cac-project/issues/23), [baseline Gate #9](https://github.com/alireza-anari/cac-project/issues/9) remain **OPEN**; [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) / GATE-SOURCE **BLOCKED**. Every prior Draft PR, including [#34](https://github.com/alireza-anari/cac-project/pull/34), stays **OPEN/DRAFT/UNMERGED**. The original S0-09D C-only anchor rollback remains **FAIL_SECURITY**, real E/root-majority catastrophe **SECURITY_UNPROVEN / NOT_RUN**, actual root policy retirement and literal old Raft snapshot/WAL import **NOT_RUN**, Lane3 orphan `OPEN_UNKNOWN` clearing **BLOCKED / NOT_RUN**. No Production, accepted recovery protocol, Sprint0, canonical historical source baseline, APR-033..036, IdP/MFA/onboarding, vendor/KMS/physical failure-domain/security certificate or Merge authorized.

**Formal vote:** `R0_SCOPE_ACCEPTED_FOR_FURTHER_DESIGN / CATASTROPHIC_MAJORITY_RESTORE_UNSUPPORTED / CONDITIONAL_QUARANTINE_ONLY / E_FEASIBILITY_DESIGN_GATED`.
