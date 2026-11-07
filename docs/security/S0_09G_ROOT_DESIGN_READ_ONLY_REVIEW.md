# S0-09G R0 — independent root security architecture review

**Date:** 2026-11-06 (Asia/Tehran). **Reviewer role:** Astra Security Architecture Reviewer / Work. **Audience:** Astra Management. **Tracking:** [Issue28](https://github.com/alireza-anari/cac-project/issues/28), parent [Issue23](https://github.com/alireza-anari/cac-project/issues/23).

**Verdict: TARGETED_DESIGN_REFINEMENT_REQUIRED.** R0 is a useful, candid statement of requirements and impossibility boundaries. It does not yet specify a concrete root-continuity mechanism or sufficiently precise enforcement/transition contract for requesting a **real bounded Lane2 PoC**. This is not ROOT_DESIGN_REJECTED: separating W from an independently surviving continuity fact is a sound direction. It is not READY_TO_REQUEST_BOUNDED_LANE2_POC: replacing the missing primitive with another assumed oracle would repeat Lane1, not discharge Lane2.

**Review only; no execution authorization.** `NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`. Original S0-09D rollback remains **FAIL_SECURITY**. All real R experiments in this review are **NOT_RUN**. Lane3/orphan clearing remains **BLOCKED**. SOURCE-001/GATE-SOURCE remain **BLOCKED**; Gate9, Issue23 and Issue28 remain **OPEN**. No Production, protocol, APR or Sprint0 approval.

## 1. Scope, provenance and evidence boundary

Reviewed the [R0 candidate at exact management main](https://github.com/alireza-anari/cac-project/blob/2444293bf288ed27d7cf698bbb19f7ce65b4fe8c/docs/architecture/S0_09G_REAL_W_ROOT_DESIGN_CANDIDATE_R0.md):

| Identifier | Verified value / meaning |
|---|---|
| Live main at initial review | `2444293bf288ed27d7cf698bbb19f7ce65b4fe8c` |
| Last commit modifying R0 | `f6eb045f90b01a27aa663579318c2d76ffb91066` (later main commit records provenance) |
| R0 Git blob | `702b4fd8f33920ec5e9c40684ff547853604df42` |
| R0 content SHA256 | `6ca7ce3b38a457642bfd4c0a563ab8e20eaab2abfde2c053340c5594f6e7ac59` |
| Remote/local content | Raw GitHub content compared byte-for-byte with the main checkout |
| Prior conditional execution | Draft27 head `2bebe0022956809b3842a015d215e6332c5a8b0f`, still Draft/open/unmerged |

Read Issue28 and its management R0 handoff, Issue23, management R1 and D/F rulings at the pinned main, and the accepted [R1 independent delta review](https://github.com/alireza-anari/cac-project/blob/d10ced56dcd7a267a18fd5620ccc8c16a1856604/docs/security/S0_09E_R1_DESIGN_DELTA_REVIEW.md). R0 section/invariant references below refer to this exact blob. Official technical references were consulted read-only; their scope is stated in section10.

This review is independent of **R0 authorship**. Prior CAC review/implementation participation does not make it an external certification, independent infrastructure operation, hardware evaluation or formal proof. No code, SQL, migration, workflow, existing test, architecture proposal, APR or prior PR is changed. Only this new review report is added in a separate branch/ Draft PR against current main. No D/F test is repeated, no dependency installation/deployment is performed, and no product or vendor is selected.

The management D/F rulings supply provenance: 129 inherited +40 conditional F methods form a **169 distinct inventory across separate suites**, not one invocation and not real R evidence. Their runtime results are cited as prior observations, not independently rerun here. A workflow that successfully detects the legacy D assertion failure does not make rollback safe.

## 2. What R0 gets right, and what remains unestablished

R0 section1 correctly distinguishes signature validity from current authority. In history H1, A/e1 is still current. In H2, B/e2 was committed, then W, signer and verifier policy are restored to e1. If every fact consulted by the verifier is identical, a new nonce and a newly generated signature do not distinguish those histories. An old key can sign a new nonce over old state. This reasoning supports an independent continuity/enforcement boundary, not the existence of that boundary.

R0 sections2–4 also correctly require more than a scalar epoch: root/policy continuity, the authenticated current head, complete unresolved-work evidence and admitted actors/guards. It explicitly refuses an ordinary extra database, generic quorum label, WORM audit log or hardware label as a complete solution. G-INV-07 and the runbook reject timeout/manual orphan clearing. These requirements should be retained.

**Answer to the central question:** R could prevent W rollback **conditionally**, if its current head and enforcement policy survive the supported W restore, cannot fork into independently accepted roots, and bind the full operation state. R0 currently names those desired properties rather than the actual mechanism that supplies them. Thus it has not yet escaped the W-to-R displacement problem. It is candid about that gap; the finding is missing design evidence, not an allegation of a demonstrated implementation vulnerability.

### Surviving-fact analysis

| Disaster / restore envelope | Fact that must remain outside it | Permissible result under this candidate |
|---|---|---|
| All W members/data lost; R remains independently current | Authenticated R head with owner/epoch/policy and unresolved-work commitment; complete replay evidence outside lost W if recovery is claimed | Rebuild only from verified complete state; otherwise quarantine. Knowing the epoch alone does not permit resumption |
| W restored to e1; current R records e2 | Protected R identity/policy and enforced verifier admission | Reject e1, including fresh old-signer answers; deny if current proof unavailable |
| R service members restored/recreated from an old snapshot | A non-restored freshness/state-binding primitive and enforcement root, or a strictly defined surviving authoritative failure domain | R0 has not supplied this. No claim that a new cluster ID or numeric revision bump recovers lost authority/OPEN history |
| W and old verifier/trust store restored together | Mandatory admission/fencing path outside that joint restore, covering direct SQL/issuer/pool endpoints | An obsolete verifier cannot certify itself as current. A new verifier denying elsewhere is insufficient |
| R payload/journal lost but protected counter survives | Authenticated binding of that counter/head to exact state; complete pending-operation data for any availability recovery | Mismatch/missing history means deny. Raising the counter again does not reconstruct forgotten OPEN |
| Every independent current-head/policy witness is lost or jointly rewindable | None survives | No authoritative automatic recovery can be inferred. Global quarantine requires an enforcement boundary that also survived; otherwise even the deny claim is unestablished |

Independence must cover restore permissions, backup catalog, signing/boot policy, identity enrollment, root replacement and control-plane administrators, not just a different process, region or database. Excluding an attacker who controls every root is reasonable as an explicit boundary; it does not establish that routine permitted restore/replacement procedures actually leave an independent fact intact.

## 3. Comparison of R0's two principal options

These are capability comparisons of the alternatives **already in R0**, not a technology selection or a new architecture. No numeric price, latency, endurance or recovery-time claim is supported yet.

| Dimension | A — independent linearizable R plus nonrollback head primitive | B — protected monotonic/sealed root plus ordered state service |
|---|---|---|
| Security potential | A single order for owner/policy/OPEN/CLOSE can protect W against its own rollback if R's continuity survives | A genuinely protected state-binding primitive can prevent accepting older service state if all authorization decisions are gated by it |
| Missing security fact | An ordinary consensus database can itself be restored. A still needs the named nonrollback primitive and independent verifier/bootstrap protection | Non-exportability alone prevents neither signing stale state nor restored-verifier trust. A counter alone lacks owner/OPEN/state meaning |
| Infrastructure independence | Separate administration, backup/restore authority, membership/bootstrap policy, signer custody and current-head verification must be demonstrated | Device/anchor administration, reset/replacement, firmware/policy and any shared parent account must be outside the supported rollback envelope |
| Complexity | Membership/reconfiguration, current reads, journal replay, signer retirement, fail-closed client behavior and catastrophe policy | Atomic counter/digest/state binding, ordered journal, crash gaps, device replacement, policy enrollment and current-head verification; these obligations do not disappear |
| Cost drivers | Independent operators/domains, durable operation history, network/quorum latency, key lifecycle, monitoring and DR exercises | Root operations/capacity, device-specific limits and assurance, custody, replacement inventory, independent journal plus service operation |
| Critical-path availability | R unavailable or freshness uncertain means no new permission; membership loss may stop service. A healthy W cache cannot override it | Unavailable/lost/uncertain protected root must stop new permission even if the state service is healthy; replication/replacement must not silently create a second root |
| Loss of all W | Potential replay from R's independently retained complete evidence; a head-only R requires separate payload survival or indefinite freeze | Counter/root may preserve a rejection boundary; useful recovery additionally needs authenticated full state outside W |
| Loss/restore of all R state | Not solved by consensus or a new logical-cluster ID. Requires an independently surviving primitive or explicitly unsupported recovery | Only the specified primitive's actual survival/replacement guarantees count; losing it without a trusted continuity witness means freeze |
| PoC feasibility | W-restore integration can be tested, but calling it Lane2 requires evidence that A's own root failure envelope is real, not assumed | Can test actual supported primitive behavior and binding/crash cases once a concrete capability is independently specified; an emulator proves integration only |

**A and B are not necessarily disjoint.** B could supply the missing primitive in A. Conversely, an externally anchored B can simply become another A-like service with the same root question. R0's preference for A is therefore a provisional review preference, not a demonstrated security/cost winner.

R0 puts OPEN and CLOSE as well as epoch transitions into R's order. Cost evaluation cannot assume a root touched only on rare takeover. Each successfully closed operation entails at least the two logical durable transitions OPEN and CLOSE; batching can amortize physical work but must preserve the before-permit/after-outcome constraints. Online issuer/SQL/RLS checks add availability and latency dependencies. Actual throughput, durability latency, storage/retention, failure recovery and operating cost remain **NOT_RUN** / unmeasured.

Option C remains audit supplementation: preserving object versions is different from selecting a fresh authoritative live head. Option D is a required fallback, not recovery; it protects the full system only if old endpoints cannot bypass the surviving deny/admission boundary.

## 4. P0 findings — targeted refinement before a Lane2 request

### G-P0-01 — No concrete terminal continuity primitive or catastrophe envelope

**Status: DESIGN_BLOCKED.** References: R0 sections1–3, G-INV-01, section7 gate.

R0 requires an irreversible latest head but does not identify its actual capability, protected state, authorized mutators, rollback/reset behavior or survival budget. A's nonrollback primitive and B's hardware/external anchor remain placeholders. After all root service members and their backups are restored, nothing described currently explains how a verifier learns that a newer head ever existed. Ordinary linearizability within one history is insufficient to establish history continuity across root reconstruction.

**Required refinement:** one concrete, technology-neutral capability contract or a separately evidenced implementation candidate: what survives which faults, what cannot be reset by the permitted restore actor, how reset/replacement is detected, who authenticates its current state, and when all-member/root loss is permanently unsupported. A bounded crash-fault service with surviving authoritative state may be a legitimate scoped candidate; do not extend it to destruction/restoration of that surviving state. No vendor purchase or universal indestructibility promise is requested. If the only root is another jointly restorable database, that instantiation is rejected, even though R0's broader direction is retained.

### G-P0-02 — Bootstrap, signer retirement and old-verifier exclusion lack an enforceable endpoint contract

**Status: DESIGN_BLOCKED.** References: response contract, G-INV-02/06, runbook steps2–3/6.

Co-versioning policy fields is necessary but does not say who prevents a restored verifier from trusting an old root and using old credentials. Root identity cannot be authenticated solely by the root's own restored metadata/key. A fresh signature by a retired signer and a restored accepting trust store still satisfy the H1/H2 ambiguity. A new guard's READY refusal does not constrain an old direct SQL/issuer/pool endpoint that never consults R.

**Required refinement:** trusted initial admission and re-enrollment inputs held outside the joint restore; root/namespace/incarnation binding; atomic activation/retirement policy; independent current minimum verifier policy; precise all-entry-point quarantine and evidence of completion before reopening. Name which operator/control plane can reset root identity, keys, trust policy and actor admission, including common administrators. Root rotation must not silently create an accepted genesis. Physical same-ID clones must stay excluded unless actual independent identity or enforced exclusion is available.

Retirement must distinguish **new authorization** from verification of historical journal evidence. Retained old public keys may be needed for an authenticated historical replay; that must not make an old key eligible to mint current authority. The candidate needs this explicit use/policy distinction, not just a list of retired key epochs.

### G-P0-03 — Atomic protected head, full OPEN state and replay-completeness interface is still an obligation, not a contract

**Status: DESIGN_BLOCKED.** References: R state tuple, G-INV-03/05, section5 atomicity obligation.

The state tuple and demand for complete replay are directionally correct. The document does not yet specify the durable linearization/acknowledgment rule tying the protected primitive to owner/policy state, OPEN membership and the replay payload. For B, advancing a counter without the durable matching operation state can destroy recoverability; keeping an old payload while accepting a higher unbound counter can forget an OPEN. A can have an analogous protected-head/journal commit gap. A head digest with inaccessible payload can safely force indefinite denial, but is not proof of successful state recovery.

**Required refinement:** define the authoritative transition/receipt and conservative crash states for protected head versus journal versus W; exact expected-head/CAS and idempotent lookup semantics; how a complete unresolved set is verified against the authoritative head; and what survives journal loss/compaction. State which missing pieces cause quarantine with no permit. No particular hash algorithm, serialization or storage schema need be ratified to describe these semantics. Never issue permission from W's updated cache while R's commit or continuity is uncertain.

Concrete attack history for the future proof: A's OPEN is durably acknowledged; restore W without it; present a newer scalar epoch/counter but omit that unresolved operation; attempt B activation. A currently anchored, complete state must exclude B, or missing evidence must freeze the namespace. Recreating an empty list at a new sequence is not recovery.

### G-P0-04 — First-use freshness and revocation have an unresolved linearization/physical-time distinction

**Status: DESIGN_BLOCKED.** References: response validation, G-INV-03/04, section5 current status/first-use obligation and delayed-response cut.

A possible schedule is: R validates a live operation at q; a nonce-bound reply is delayed; REVOKE_INTENT commits; the reply arrives and the local statement starts. A fresh nonce and even a correct linearizable read do not alone place physical local execution inside the remote read. Another final remote check merely moves the interval. The held OPEN can still prevent successor READY, which is a different and valuable invariant.

**Required refinement:** define FIRST_USE as an ordered R authorization transition or specify an independently enforced fence/commit boundary if the intended promise is that *physical* local first use cannot occur after revoke acknowledgment. Specify whether a first use ordered before revocation is in-flight despite late delivery, and how a replay into a new local transaction is denied. Do not weaken the no-old-COMMIT-after-successor-READY hold invariant, and do not silently claim instantaneous revocation of all previously admitted work. This is a request to disambiguate the acceptance predicate, not a new protocol proposal or a demonstrated exploit.

### G-P0-05 — Hard-fence alternative can be read as an unauthorized orphan-release path

**Status: DESIGN_BLOCKED.** References: section5 takeover outline, G-INV-07, runbook resume rule; compare accepted R1 E-P0-04.

The takeover outline allows an alternative of separately proven hard fencing where other wording requires all holds known resolved. G-INV-07 says FENCED_UNRESOLVED remains a deny state, and the candidate excludes Lane3. A fence may establish that a particular old endpoint cannot execute another COMMIT; it does not by itself establish whether an earlier COMMIT/effect already happened, cover a different clone/prepared participant, or reconcile that effect. PostgreSQL prepared transactions illustrate why session disappearance is insufficient [T3].

**Required refinement:** in this Lane2 slice, explicitly bar successor authorization while an operation is OPEN_UNKNOWN/FENCED_UNRESOLVED. State that fencing alone does not clear the operation or substitute for outcome/effect evidence. If an exception is desired, it belongs to a separately reviewed/authorized Lane3 contract with positive outcome/effect evidence and durably recorded resolution. No timeout, manual signature, root epoch bump or fresh bootstrap may act as that exception.

## 5. P1/P2 findings and residual risks

| ID | Priority / status | Finding and required disposition |
|---|---|---|
| G-P1-01 | P1 / DESIGN_BLOCKED | Failure-domain/custody matrix and lifecycle cost are not decision-ready. Specify supported simultaneous failures/restores, shared administrative parents, membership/reconfiguration/reset rights, independent backup/journal survival, replacement ceremony, irrecoverable loss and service/operating cost drivers. Geographic/process separation alone is insufficient |
| G-P1-02 | P1 / REQUIRES_EXPERIMENTAL_PROOF | Quarantine/runbook enforcement and complete-replay denial need evidence at direct issuer, SQL/RLS and existing/reused pooled endpoints, not only READY. Draining/credential revocation must be observed as complete; fencing and prepared/in-flight effects remain distinct. R unreachable blocks new authorization but cannot retroactively revoke data already returned |
| G-P1-03 | P1 / REQUIRES_EXPERIMENTAL_PROOF | The future proof plan needs reason-specific acceptance controls: actual healthy current-root authorization before each relevant fault; eligible contenders; no missing ticket/invalid argument masking the root check; intended assertion RED rather than setup errors; exact restoration. A simulated root or forced loss flag cannot prove physical root continuity |
| G-P2-01 | P2 / PROPOSED | Normalize the claim/status ledger and evidence vocabulary. R0's A preference is not product approval; draft fields, counters, key formats and any TTL remain unratified. Record exact primitive/firmware/policy/evidence versions and distinguish a capability assumption, design contract, laboratory observation and operational assurance |

These findings do not require redesigning or repeating D/F. They require tightening the proposed R boundary and its falsifiable proof obligations. Availability losses, possible permanent freezes, operational independence and unproved physical enforcement remain material risks even if a later PoC passes.

## 6. Claim-by-claim disposition

Each claim below has one primary review status. A requirement recorded as PROPOSED is not an implementation PASS; experiment scenarios are separately NOT_RUN.

| R0 claim / component | Review status | Reason / dependency |
|---|---|---|
| Section1 independent surviving continuity/enforcement fact is necessary | PROPOSED | Sound threat-model direction, not a constructed root or formal proof |
| G-INV-01 non-revivable epoch under R's own restore | DESIGN_BLOCKED | Actual surviving primitive/failure envelope absent; G-P0-01 |
| G-INV-02 current signer/root/verifier policy cannot be rolled back together | DESIGN_BLOCKED | Bootstrap, retirement and endpoint enforcement not concrete; G-P0-02 |
| G-INV-03 declared OPEN-before-permit and ADMIT/revoke order | PROPOSED | Appropriate requirement retained; no real R implementation evidence |
| Protected OPEN/head/journal commit and completeness mechanism | DESIGN_BLOCKED | G-P0-03, including total W-history loss |
| Fresh first-use semantics across delayed response/revoke | DESIGN_BLOCKED | G-P0-04; nonce freshness is not physical-time fencing |
| G-INV-04 local durable outcome followed by hold closure, no successor while old commit possible | REQUIRES_EXPERIMENTAL_PROOF | Intended safety property retained; cannot infer real R durability from F; resolve G-P0-03/04/05 before scoping proof |
| G-INV-05 reconstruct W only from exact current complete root state, otherwise deny | REQUIRES_EXPERIMENTAL_PROOF | Appropriate fail-closed requirement; completeness mechanism blocked separately |
| G-INV-06 ordinary SID/copied credentials do not establish physical clone safety | PROPOSED | Honest exclusion; actual physical admission/fence is not supplied |
| G-INV-07 UNKNOWN/fenced-unresolved nonrelease | PROPOSED | Preserve as absolute Lane2 boundary; reconcile section5 alternative via G-P0-05 |
| Option A is ready as a real root to implement | DESIGN_BLOCKED | A capability placeholder, not evidence of irreversible recovery |
| Option B offers a possible protected root capability | PROPOSED | Platform-specific capability and state binding must be established; no HSM/KMS choice |
| Option C WORM/audit alone is sufficient for current authorization | DESIGN_BLOCKED | R0 correctly rejects this inference; version retention is not a latest-head/admission protocol |
| Option D guarantees global denial after root loss | REQUIRES_EXPERIMENTAL_PROOF | Depends on surviving mandatory guard/fence; cannot assume obsolete endpoints cooperate |
| Real R rollback/clone/rebootstrap, all-root-member loss and independent custody have been demonstrated | NOT_RUN | No such execution occurs in this review; 169 prior observations are not R proof |

## 7. Adversarial histories and future proof boundary

All executions below are **NOT_RUN** for a real R. This is a review of R0's proof plan, not authorization or a new test implementation.

| History to distinguish | Required acceptance observation / reason a superficial GREEN is insufficient | Execution status |
|---|---|---|
| W e1 snapshot presented after acknowledged R e2 | Current R rejects old A new issuance/RLS; current-root positive first, enforcement-removed mutation must fail the same denial assertion | NOT_RUN |
| All W members lost; old/partial/missing OPEN journal restored | Independently surviving R rejects mismatched/incomplete state; complete current replay if claimed, otherwise quarantine with no successor | NOT_RUN |
| Own R snapshot rollback, namespace recreation, all-member recovery | Actual surviving primitive detects/rejects the older state or admission refuses it. A guessed revision bump/new identity and a mock counter are not proof | NOT_RUN |
| Restored retired signer + restored verifier trust/policy + W | Independently current bootstrap/admission blocks every supported old endpoint before permission; fresh old-key signatures must not suffice | NOT_RUN |
| R majority/minority, two independently restored signer groups, one-way loss | Only a currently admitted authoritative head may authorize; minority/unknown continuity denies. Reconfiguration and cloned-root genesis must not create two accepted roots | NOT_RUN |
| Delayed signed first-use response crosses REVOKE_INTENT | Evaluate the explicitly chosen ordered-first-use contract; preserve hold/no-successor invariant. Do not call nonce-only replay rejection instantaneous revocation | NOT_RUN |
| Physical same-SID/credential clone, old guard or simultaneous W/verifier restore | Actual independent admission/exclusion at direct SQL, issuer and pool; otherwise mark unsupported. Do not substitute a new logical ID for nonclonability | NOT_RUN |
| Protected primitive advances before journal durability, or journal writes before protected commit | No permit until the defined authoritative commit; mismatched/uncertain state stays excluded, not filled with an empty OPEN set | NOT_RUN |
| OPEN commit/ACK lost; client/guard/W crash before first use | Same-key/digest lookup under current R, original outcome or denial; no extra guessed activation and no unrecorded permit | NOT_RUN |
| Last guard then local COMMIT; COMMIT durable but ACK lost | Original hold survives until positive bound outcome; no successor READY while old work may still commit; no post-hoc check substituted for hold | NOT_RUN |
| Pre-ABORT crash, lost ABORT ACK, R CLOSE executed/ACK lost | Separate actual cuts and message loss; uncertain local outcome remains blocked. If authenticated lookup proves an already committed exact CLOSE, idempotent observation is not a new orphan-clearing operation | NOT_RUN |
| Old actor hard-fenced while outcome/effects unknown | FENCED_UNRESOLVED remains non-authorizing; neither reservation nor an operator signature clears it | NOT_RUN |
| R outage / stale reads / stale policy / old W warm cache | Known-valid issuer/RLS/pool operations stop receiving new authorization, with no offline/C-only fallback; distinguish already returned reads and tracked in-flight work | NOT_RUN |

### What a later bounded PoC could and could not establish

After targeted refinement and **separate explicit Management authorization**, a bounded PoC can falsify transition/response binding, OPEN/revoke ordering, idempotent ACK recovery, missing-replay rejection, W snapshot rejection, protected-root integration, old-verifier quarantine and named crash schedules. It must use the actual capability for every claim labeled real-root proof and maintain reason-specific mutation sensitivity/restoration. Record the actual restore envelope, primitive version, custody topology and unsupported losses; preserve the original D FAIL_SECURITY and the distinct inherited inventory.

A model/emulator can test adapter logic and failure handling, but its monotonicity/root authenticity remain assumptions. Testing two containers/accounts is not evidence that no shared control authority can reset both. Actual physical root reset/replacement resistance, custody separation, firmware/policy trust, noncloneable actor identity and catastrophe survival require independently supported infrastructure/device capabilities and operational evidence beyond a simulated CI fixture. Even actual hardware availability alone does not establish the state-binding or verifier contract. No benchmark, purchased device or generic compliance citation is a substitute for that evidence.

Root loss with no surviving witness may be an explicitly unsupported recovery mode with indefinite denial. That is a defensible safety boundary only if the surviving enforcement path can enforce it; it must not be reported as successful epoch/OPEN recovery. Lane3 reconciliation remains outside any proposed Lane2 proof.

## 8. Minimum targeted refinement for a later authorization request

This is a closure checklist for R0's existing obligations, not a replacement design or permission to implement:

1. **Close G-P0-01:** specify one real root capability and exact supported loss/restore budget; identify the final surviving fact and its protected reader/administrator. State explicitly where all-root loss means unsupported indefinite freeze.
2. **Close G-P0-02:** describe trusted genesis/enrollment, root/key retirement and replacement, current verifier policy, physical/logical actor scope and unavoidable all-endpoint admission. Provide a restore/custody diagram or matrix that shows what cannot be rolled back together.
3. **Close G-P0-03:** define protected commit/ACK/head+OPEN completeness, missing payload behavior, idempotent status/close and journal retention/replay crash states. Root and W coordination can conservatively block; it cannot silently invent a resolved history.
4. **Close G-P0-04:** state an unambiguous first-use/revoke linearization predicate and its relation to physical local execution and successor READY. Match future test assertions to the actual promised invariant.
5. **Close G-P0-05:** remove the Lane2 hard-fence-only interpretation; keep every unknown/fenced-unresolved operation non-authorizing until a separately approved Lane3 resolution exists.
6. **Bound G-P1-01/03:** compare actual independence, operating/capacity/replacement cost drivers and available evidence for A/B, then define the smallest hypothesis, actual primitive, healthy positives, targeted REDs, named real crash/restore cuts, failure/stop criteria and explicit NOT_RUN modes for the Management request.

Contract closure would make a later request reviewable. It would **not** prove security or authorize execution. Findings marked REQUIRES_EXPERIMENTAL_PROOF still need real evidence after authorization; no proposed R1 refinement, root code, device experiment or deployment is created by this report.

## 9. Change scope, verification and governance

Verification for this documentation review consists of live GitHub main/document/issue/PR checks, immutable source/blob/content hashes, source/reference reading, and a diff/whitespace check requiring this report to be the only change relative to the selected main. No security tests or runtime experiments are run or claimed PASS; no D/F CI is re-dispatched. Any automatically scheduled repository checks would verify their own scope, not real R security.

At review start, prior PR11/16/18/20/22/24/25/27 were open/Draft/unmerged; their heads were recorded and are not modified by this review. No PR is merged, and no architecture/source gate is closed. The separate review PR targets main and is not stacked onto the experimental implementation branches. The review commit SHA/PR and final main/protected-PR recheck are delivered in Issue28, avoiding a self-referential SHA inside its own report.

**Astra Management vote: TARGETED_DESIGN_REFINEMENT_REQUIRED.** Retain the independent-root direction, but do not request/authorize a real Lane2 implementation on R0 as written. Resolve the five P0 contract gaps and bound the custody/cost/proof envelope first. A concrete instantiation that merely renames a restorable W as R should be rejected; the entire independent-root approach need not be discarded. The 169 prior case observations do not change this vote. S0-09D rollback remains FAIL_SECURITY; Lane3 and SOURCE-001/GATE-SOURCE BLOCKED; Gate9/Issue23/Issue28 OPEN; no Production, protocol, APR or Sprint0 acceptance.

## 10. Sources and exact scope of reliance

Repository sources are authoritative for CAC's proposed contract and recorded prior decisions, not proof that a physical root exists. Public technical documents below were retrieved on 2026-11-06; use of a named technology as a counterexample/reference is **not selection or approval**.

- **[R0]** [Pinned management R0](https://github.com/alireza-anari/cac-project/blob/2444293bf288ed27d7cf698bbb19f7ce65b4fe8c/docs/architecture/S0_09G_REAL_W_ROOT_DESIGN_CANDIDATE_R0.md), especially sections1–7 and G-INV-01..07. Hashes in section1.
- **[R1]** [Management R1 at reviewed main](https://github.com/alireza-anari/cac-project/blob/2444293bf288ed27d7cf698bbb19f7ce65b4fe8c/docs/architecture/S0_09E_TARGETED_DESIGN_REFINEMENT_R1.md), especially E-P0-01..04; [accepted independent R1 review](https://github.com/alireza-anari/cac-project/blob/d10ced56dcd7a267a18fd5620ccc8c16a1856604/docs/security/S0_09E_R1_DESIGN_DELTA_REVIEW.md). Lane1 scoping acceptance did not accept a real root.
- **[D/F]** [D ruling](https://github.com/alireza-anari/cac-project/blob/2444293bf288ed27d7cf698bbb19f7ce65b4fe8c/docs/architecture/S0_09D_ARCHITECTURE_RULING.md), [F ruling](https://github.com/alireza-anari/cac-project/blob/2444293bf288ed27d7cf698bbb19f7ce65b4fe8c/docs/architecture/S0_09F_ARCHITECTURE_RULING.md), [F exact-head receipt](https://github.com/alireza-anari/cac-project/issues/26#issuecomment-6682584952). Prior bounded evidence only; no rerun or real-root inference.
- **[T1]** [etcd v3.6 disaster recovery](https://etcd.io/docs/v3.6/op-guide/recovery/), Revision Difference / Restoring from snapshot / Restoring with revision bump: older snapshot restoration can lower revisions, and restore replaces cluster/member identifiers. Reviewer inference: revision bump/new identity alone does not restore missing CAC owner/policy/OPEN history or supply an independently surviving witness.
- **[T2]** [etcd API guarantees](https://etcd.io/docs/v3.6/learning/api_guarantees/), Strict serializability / Linearizability / Operation completed: current reads and uncertain timeout outcomes have defined consistency semantics; explicitly weaker serializable read mode and watch behavior cannot be treated as a universal current-head proof. These are examples of interface obligations, not proof about unspecified R or consensus safety under all-member restore.
- **[T3]** [PostgreSQL17 PREPARE TRANSACTION](https://www.postgresql.org/docs/17/sql-prepare-transaction.html), Description/Notes: prepared transaction state is persisted separately from the initiating session and can be completed later; zero max_prepared_transactions disables preparation. This supports the need to account for prepared work or prohibit it, not an implemented R fence.
- **[T4]** [AWS Object Lock guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html), object-version retention: locking a version does not prevent creating new versions/delete markers. Reviewer inference: WORM alone does not choose the authoritative latest owner/OPEN head. No storage-product choice is made.
- **[T5]** [NIST SP800-57 Part1 Rev5](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57pt1r5.pdf), section7 (key states) and section8.1.5.1 (asymmetric-key/trust-anchor distribution): key-state transitions/revocation and authentic trust-anchor distribution require explicit management. It does not establish monotonic counters, this root's irreversibility or an anti-rollback implementation certification.

The counterexamples, option comparison, required refinements and verdict are this reviewer's design analysis. They are not reported as executed attacks, vendor assurances, new architecture decisions or experimentally proved R properties.
