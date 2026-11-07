# CAC — S0-09I R0: Root-Majority Catastrophe, Recovery Boundary and Independent Continuity

**Date:** 2026-11-07
**Authority:** Astra Management / Security Architecture
**Issue:** [S0-09I #33](https://github.com/alireza-anari/cac-project/issues/33)
**Parents:** [Architecture #28](https://github.com/alireza-anari/cac-project/issues/28), [#23](https://github.com/alireza-anari/cac-project/issues/23)
**Prior bounded evidence:** [S0-09H ruling](S0_09H_ARCHITECTURE_RULING.md); [Draft PR #32](https://github.com/alireza-anari/cac-project/pull/32) at b32416c799160f0e5957506d58254a693cbc231f
**Decision:** DESIGN_CANDIDATE_R0 / ROOT_MAJORITY_RESTORE_UNSUPPORTED / EXTERNAL_CONTINUITY_RESEARCH_ONLY / P0_SECURITY_UNPROVEN / NO_POC_AUTHORIZED
**Origin:** CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED

## 1. Management position and exact safety claim

**Interim support policy: prohibit automatic resurrection of authority from a rolled-back or catastrophically lost majority R.** Ordinary snapshot-based etcd recovery is not an approved CAC authorization recovery protocol. Any restoration with unverified current authority history, signer/verifier policy or unresolved operation history must remain QUARANTINED / NOT_READY **where a surviving independently trustworthy guard can enforce denial**.

This is an **operational restriction, not a demonstrated universal fail-closed mechanism**. A still-responsive majority restored coherently to an earlier epoch may produce a newly signed but stale authorization decision. If *all* quorum, trust roots, mandatory verifiers and old SQL/issuer entry points are jointly restored, CAC has no surviving newer fact from which to detect that rollback. In that threat model, saying “the service fails closed” would be unjustified. The only safe planning stance is **UNSUPPORTED / P0 SECURITY_BLOCKED** until a genuinely independently retained fact and mandatory enforcement are proven.

No Production / canonical source / root security acceptance or executable experiment is authorized by this document.

## 2. Evidence accepted and remaining gaps

The S0-09H test observed five real etcd v3.6.16 voters, actual PostgreSQL 17.11 and PgBouncer 1.22.0 on **one CI host**. With an admitted up-to-date, non-restored three-of-five R majority and trusted test controller/PG observer, a logical rollback of W plus fresh minority nonvoting learner replacement did not revive previous owner A. Complete root/OPEN replay, guarded SQL/RLS, first-use/revoke sequencing, real local transaction/reply faults and no unsafe orphan release were exercised. Evidence: 51 distinct new H DB/security test methods, five targeted original-assertion RED and restored GREEN probes, two artifact-scanner methods, and 169 retained prior cases in **separate suites**. The old S0-09D C-only rollback remains **FAIL_SECURITY**; it is not repaired by a conditional H-path pass.

**NOT_RUN / NOT_PROVEN:** responsive rollback of three or more R voters; full W/R root disaster; jointly restored obsolete verifier, signer policy and old SQL; nonclonable physical actors; independent production admin/backup/key custody; root **policy retirement** (signer retirement differs); **literal old Raft snapshot/WAL import** (fresh learner replacement differs); complete Raft ACK crash matrix, physical PITR/multi-host partitions, and Lane3 orphan OPEN reconciliation. None can inherit a PASS from the earlier 220 distinct security/DB case inventory.

## 3. Indistinguishability and root-of-trust requirement

History H1: epoch 1/A is genuinely the most recent authorized state. History H2: epoch 2/B and durable OPEN were once committed, but a quorum, root signing credentials and mandatory verifier policy were restored to epoch 1. If every observable trusted input is restored, the two histories can be indistinguishable. Signatures prove the credential that signed an answer; they do not prove no newer committed epoch existed.

A second restorable database, old but valid signer, internal hash chain, revision bump, cluster ID or ordinary WORM audit trail does **not** independently prove the most recent authorized head. A responsive rewound quorum is materially different from an unavailable quorum. A verifier that checks only current responsiveness can accept the former.

A recoverable majority-rollback mode requires a separate **non-rewindable latest-head continuity fact** and an authenticated current enforcement root that survive *the exact rollback scope being claimed*. If both those roots can be rolled back under the same administrator, the failure has merely moved one layer higher.

## 4. Architecture choices — explicit recommendation

| Choice | Security premise | Availability / complexity | R0 verdict |
|---|---|---|---|
| **A. Unsupported majority restore; independent quarantine where enforceable** | Preserve the already-proven bounded non-restored 3/5 majority scope, refuse to authorize when current history cannot be verified | Can cause **indefinite downtime**; requires independent old-endpoint/guard isolation to be meaningful | **SELECT AS INTERIM POLICY**; not a universal fail-closed proof |
| **B. Independent continuity root E** | Separate trust/custody root attests a fresh, nonrollbackable **latest complete authority head** and current signer/verifier policy, beyond majority R snapshots | More independent infrastructure, online gate, key policy, failure domains and cross-root atomicity; unpriced/untested | **Keep as design research candidate**, no code/vendor approval |
| **C. Protected monotonic hardware or external witness plus complete log** | A protected non-resettable sequence and cryptographically bound full pending journal could underpin E | A bare counter, HSM signature or sealed key does not preserve OPEN or repair a rolled-back verifier; replacement and key custody unknown | **Alternative B primitive**, NOT selected/proven |
| **D. Immutable audit store / revision-bump snapshot** | Useful for evidence preservation, cache invalidation and incident review | Does not by itself provide a fresh, online, linearizable authorization head | **Reject as standalone root** |

**Recommended path:** A now, B/C only after an adversarial independent architecture review and a concrete physical/operator custody design. No hardware, KMS, consensus product, cloud service, algorithm or root TTL is selected. Do not assert any numeric performance, quorum availability, RPO/RTO, expense or recovery time without measurements.

## 5. External E minimum contracts, if studied later

A qualifying E must independently preserve and freshly authenticate at least: root/namespace incarnation; latest committed authorization sequence, epoch, owner/actor incarnation; membership and approved signer/verifier/guard policy; complete head/journal commitment including **all unresolved OPEN/UNKNOWN**, idempotency and revocation tombstones; prior/head digest; and current endpoint and permitted-actor admission state. A high-watermark counter or root signature **without complete operation history** is not enough to know that no stale transaction can still commit.

**E-PRECONDITIONS, all DESIGN_UNPROVEN:**
1. E survives each precisely specified R/W/PG restore scope, with **separately governed backup, access, key and verifier-policy custody**. E's own rollback/rebootstrap and former key revival must have a tested story; no infinite chain of unproved roots.
2. The **current verifier/guard is mandatory on every admitted live and restored path**: issuer, direct SQL/RLS, PgBouncer backend reuse, old C-only guards and privileged administrative admission. A verifier cannot self-attest a downgraded image. A copied public key alone is not physical actor identity; SQL superuser/root compromise remains excluded unless independently constrained.
3. Every new permit requires an authenticated fresh E decision AND a matching fully replayed R state and unresolved-operation head. Older signed messages, lost E, policy mismatch, missing OPEN or incomplete journal => DENY/NOT_READY.
4. Multi-root durability must be spelled out. Proposed **conservative staging**: serialize candidate owner/OPEN/revoke at R, durably bind that exact full head at E, and release any new permit only after E acknowledgment and a fresh dual-head match. **This is a research sketch, not a proven atomic protocol.** If an R/E acknowledgment is lost, or E and R disagree, block rather than permit two active epochs. A design must also prevent old-permit continuation from creating an unnoticed unsafe window before E catches up.
5. First-use vs revoke remains total-ordered and holds survive until trustworthy, transaction-specific **local durable COMMIT/ABORT outcome** plus authorized CLOSE; no successor READY while an older transaction could still commit.
6. Restoring old R voting history, obsolete root/verifier policy, or W snapshot must never silently re-genesis E or erase OPEN. Root replacement requires an independently approved continuity and hard-fence procedure, not an operator signature that guesses the missing history.

A later candidate should produce a formalized state machine and indistinguishable-history counterexamples before any experimental authorization. E implementation and real majority-restoration tests are **NOT AUTHORIZED HERE**.

## 6. Trust and custody matrix

| Authority | Can restore/change | Threat if shared with root and guard | Requirement |
|---|---|---|---|
| R voter/backup operator | WAL, snapshots, membership, root election | Responsive stale voting majority and erased OPEN/policy | Bounded minority learner path only; majority restore UNSUPPORTED unless E proves a later head |
| W/application/PG operator | local schemas, issuer, pool, data backups | old executable issuer/SQL path and copied actor secret | Independent admitted version/actor policy and old-route hard disable |
| Verifier and signer-policy custodian | trusted root set, minimum build/policy, keys | A restored old verifier can trust an old signer/root again | Separately retained latest admission policy; proved key retirement |
| Cloud/root/control-plane administrator | hosts, networking, secrets and backups | Joint rollback of R, E and admission controls | Define common-control-plane exclusion; physical/admin independence NOT_RUN |
| Incident operator | quarantine/authorization to investigate | May incorrectly infer expired OPEN or safe new genesis | Cannot clear OPEN or authorize successor from signature/timeout alone |
| PostgreSQL superuser/trusted outcome observer | RLS bypass and local transaction evidence | Forged outcome or unauthorized data path | Explicitly outside H proof; design independent operational restrictions |

**Missing deployment evidence:** organizational/admin graph, key/enrollment lifecycle, multi-host/isolation boundaries, backup authorities, network route inventory, old-verifier kill/quarantine control and current independent guard enforcement. Same-host containers/processes do not prove these boundaries.

## 7. Recovery safety matrix and runbook

| Scenario | Interim support | Authoritative action |
|---|---|---|
| W logically restored, current admitted 3/5 R majority intact | H bounded observed | Current-head read, exact OPEN replay, restore quarantine and fresh admission |
| Up to two minority R replacements as fresh nonvoting learners | H bounded observed | Retain committed majority and catch up before any admitted vote |
| Literal old Raft WAL/snapshot import | NOT_RUN | Do not resume voting from copied prior identity; require separately scoped proof |
| Current quorum unavailable but independent guard still valid | DENY policy, experimental partial evidence | Block new permits; no heuristic reboot/re-genesis |
| Responsive rewound majority with old signer/policy | P0 UNSUPPORTED | Do not certify restored cluster or return to service without independent latest-head witness |
| Majority plus obsolete verifier/root jointly restored | P0 UNSUPPORTED; denial not guaranteed | Treat as security incident; physical/network isolation only under separately established controls |
| Unknown durable local outcome, lost COMMIT/ABORT ACK | BLOCKED | Persist OPEN_UNKNOWN and deny successor; never infer abort from missing session |
| Hard-fenced old actor with UNKNOWN effects | Lane3 BLOCKED | Hard fence alone does not close UNKNOWN |
| Root policy retirement and restored earlier policy | NOT_RUN | Require future independent verifier/retirement test and explicit authorization |
| Real physical clone or root-key/custody catastrophe | NOT_RUN | No Production recovery claim |

**Proposed incident states (design only):** CURRENT_VERIFIED -> ROOT_SUSPECT -> ISOLATION_REQUESTED -> VERIFIED_QUARANTINED (only where effective independent guard is established) -> EVIDENCE_GATHERING -> either REVIEWED_CURRENT_HEAD or BLOCKED_INDEFINITELY. No automatic transition from SUSPECT to new READY based on snapshots, endpoint liveness or elapsed time.

Operators must preserve signed evidence from genuinely independent sources, audit all old issuer/SQL/pool routes, compare exact committed membership/policy and unresolved holds. If physical isolation or admission cannot be shown, mark **GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED**, not “securely stopped.” An incident review can request new root enrollment, but this R0 does not authorize it and cannot release UNKNOWN operations.

## 8. Test/acceptance obligations and provenance

**Future proposed work only; no new test is authorized or executed by R0:**
- Verify actual **policy retirement** independent of signer retirement; reject obsolete policy on old direct SQL/issuer/pooled entry points after supported restore.
- Test literal stale Raft snapshot/WAL import or protocol-correct rejection while a non-restored admitted majority survives; fresh learner replacement is not a substitute.
- Challenge R ACK/voter crash cuts, journal compaction and idempotency tombstone retention, physical same-ID clones and one-way multi-host partitions.
- Study an actually independent current-head witness E, its own rollback and key-policy recovery, common admin/backup threat and **atomic R/E/Open transitions**. An assumed oracle or synthetic “rollback detected” switch does not add genuine real-root evidence.
- Keep healthy positive scope before every negative/fault assertion; controlled weakening must produce **reason-specific RED**, with byte-identical fixture restoration and identical probe GREEN. If safety invariants fail under supported conditions, preserve the failing assertion, stop scope expansion and report P0 FAIL_SECURITY.
- Do not recast S0-09D legacy C anchor rollback as GREEN. Maintain the 169 inherited +51 H = **220 distinct previous security/DB tests across separate workflows** and two artifact-only methods; never claim one monolithic suite.

**Claim register:**
- H W/minority restore under intact current quorum/guard: BOUNDED_OBSERVED_PASS.
- Root majority rollback detection: P0 SECURITY_UNPROVEN/NOT_RUN.
- Guaranteed denial after joint root+verifier rollback: NOT_ESTABLISHED.
- External E own rollback/custody/atomic bridge: DESIGN_OPTION / NOT_RUN.
- Actual root policy retirement and literal old Raft WAL import: NOT_RUN.
- Lane3 OPEN_UNKNOWN clearing: P0 BLOCKED / NOT_RUN.
- S0-09D original C-only restore: FAIL_SECURITY.
- Production/canonical source/full protocol: NOT AUTHORIZED.

## 9. Mandatory independent review and gate

**Next permitted activity:** independent **READ-ONLY R0 architecture/security review** under [Issue #33](https://github.com/alireza-anari/cac-project/issues/33), no code, CI experiment or Merge. Deliver a docs-only Draft PR on main with report **docs/security/S0_09I_R0_ROOT_CATASTROPHE_READ_ONLY_REVIEW.md**, exact SHA and Issue #33 receipt. Reviewer must challenge the unsupported-fail-closed wording, E terminal primitive and its own restore, required full OPEN journal, atomic cross-R/E authorization, key/verifier retirement, old-endpoint exclusion, admin custody, incident recovery availability and specific H NOT_RUN items.

Required reviewer vote: **R0_SCOPE_ACCEPTABLE_FOR_FURTHER_DESIGN**, **TARGETED_DESIGN_REFINEMENT_REQUIRED**, or **ROOT_CATASTROPHE_RECOVERY_DESIGN_REJECTED**. All design findings distinguish DESIGN_SPECIFIED from SECURITY_PROVEN and NOT_RUN. The review cannot itself authorize implementation, complete Lane2 or Lane3, ratify Production or close architecture gates.

**Governance:** Issues #33/#28/#23 and baseline [#9](https://github.com/alireza-anari/cac-project/issues/9) remain OPEN, SOURCE-001 [#1](https://github.com/alireza-anari/cac-project/issues/1) and GATE-SOURCE remain BLOCKED. Experimental and docs Draft PRs #11/#16/#18/#20/#22/#24/#25/#27/#29/#30/#32 remain UNMERGED. No APR-033/034/035/036 change, Sprint0 completion, identity/onboarding integration, historic source recovery, Production or security protocol ratification.

## 10. Official technical background (not CAC security proof)

- [etcd v3.6 disaster recovery](https://etcd.io/docs/v3.6/op-guide/recovery/) — lost quorum, snapshot restore and revision bumps, including new logical cluster membership. Those tools do **not** independently certify CAC's latest authority epoch.
- [etcd v3.6 compaction and maintenance](https://etcd.io/docs/v3.6/op-guide/maintenance/) — MVCC revision retention and compaction; no inference that CAC's outstanding OPEN/effect evidence is recoverable without its own committed journal.
- [NIST key-management guidance](https://csrc.nist.gov/Projects/Key-Management/Key-Management-Guidelines) — key life-cycle and custody principles, not an approval of any root implementation.
