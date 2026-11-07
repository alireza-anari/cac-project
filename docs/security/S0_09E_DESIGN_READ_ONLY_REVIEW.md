# S0-09E — Independent architecture security review

**Date:** 2026-11-06 (Asia/Tehran). **Reviewer role:** Astra Security Architecture Reviewer / Work. **Audience:** Astra Management. **Tracking:** [Issue23](https://github.com/alireza-anari/cac-project/issues/23).

**Disposition: TARGETED_DESIGN_REFINEMENT_REQUIRED / NOT_READY_FOR_IMPLEMENTATION_POC_AUTHORIZATION / P0_BLOCKED.** Retain A as a candidate for discussion; do not restart the design or select a technology. In its present form, the proposal states necessary safety properties but does not yet supply the root-continuity and transaction/recovery contracts needed to treat a limited anti-rollback PoC as a security proof. Explicit Management decision remains required before any implementation.

## 1. Exact scope and provenance

Reviewed management document: [S0_09E_ANTI_ROLLBACK_DESIGN_PROPOSAL.md](https://github.com/alireza-anari/cac-project/blob/ff67a06d9beb66e59ce53a00f6a07f3eb5ba4591/docs/architecture/S0_09E_ANTI_ROLLBACK_DESIGN_PROPOSAL.md), at commit **`ff67a06d9beb66e59ce53a00f6a07f3eb5ba4591`**, verified as live main before review. That commit updates project status; the proposal's last modifying commit is **`0ae1dff92bf7b115e6f099c7d2231126164ff82c`**.

- Git blob SHA: **`5c24e2034f539d3a6f6c59903c78ae17abcb01bd`**, verified in the remote Git tree and with local `git hash-object`.
- File-content SHA-256: **`8e251c998b2c45d3feeb58b5ef107384baadecc871844f0ff6559d631ebfbe24`**. The blob ID and file-content digest are different identifiers, not interchangeable.
- All line references below refer to this pinned 110-line proposal, not a later main revision.
- Also read: Issue23 and its two management comments; [S0-09D ruling](https://github.com/alireza-anari/cac-project/blob/ff67a06d9beb66e59ce53a00f6a07f3eb5ba4591/docs/architecture/S0_09D_ARCHITECTURE_RULING.md); pinned D handoff/review and earlier evidence context.

This is a critical review of the management-authored design, not a replacement design, executable implementation, formal verification or third-party certification. The reviewer previously participated in D implementation/evidence delivery; independence here is from authorship of the E proposal, not organizational separation from CAC. No W implementation, database experiment or new security test was executed in this review. Existing D results are not W evidence. This change adds only this report; the management proposal, executable code, SQL, tests, workflows and APRs remain unchanged.

## 2. Answers to the requested review questions

| Question | Assessment | Claim status |
|---|---|---|
| Is W actually non-rollback, rather than a renamed C? | Not established. Separate administration and linearizable access are necessary assumptions, but neither specifies how W's committed history, identity and key policy survive its own restore/rebootstrap. The document correctly admits this dependency | **BLOCKED**, E-P0-01 |
| Can W stop old-owner revival after complete C restore? | Conditionally yes if W history survives, every authorization path still enforces W and restored verification policy cannot accept retired roots/actors. These are not yet demonstrated or fully scoped | **PROPOSED; requires proof**, blocked dependencies E-P0-01/02 |
| Is W approval to local COMMIT race-free? | No executable claim can be made. The proposal requires holds but does not define their atomic admission, durable lifetime, close point or commit-versus-takeover ordering | **BLOCKED**, E-P0-03 |
| Are identity, keys and W responses rollback-resistant? | Nonce binding helps with recorded-response replay, not an active old signer or restored verifier trust policy. Physical clones with copied credentials need a credible actor/incarnation boundary | **BLOCKED**, E-P0-02; encoding contract **PROPOSED**, E-P1-01 |
| Are outage, split-brain and ambiguity always fail-closed? | Required policy is sound. It has not been shown for W minority/stale signers, delayed permits, ambiguous durable writes, existing holds or root recovery | **PROPOSED; requires proof**, E-P0-01/03, E-P1-03 |
| Can orphan OPEN recovery be proved? | Safety by remaining blocked is viable. Safe progress is conditional on trustworthy fencing and outcome/effect evidence. No general clearing algorithm follows from current prerequisites | Clearing **BLOCKED**; deny-only policy **PROPOSED**, E-P0-04 |
| Which assumptions require independent infrastructure/keys/operations? | W history and namespace continuity, signing/verifying policy custody, actor/guard incarnation, actual fence execution, trusted outcome witnesses and recovery authorization. None may be silently restored from the snapshots it must reject | **BLOCKED pending explicit trust contract**, section6 |
| What needs ADR amendment or an experiment? | Root/restore contract, enforcement/actor contract, operation lifecycle and recovery evidence, followed by separately authorized fault experiments | **PROPOSED revisions; experiments NOT_RUN**, sections7–8 |

## 3. Findings — P0

### E-P0-01 — W anti-rollback continuity remains an axiom

**References:** proposal sections2/6, lines20,24,28–31,81. **Status:** BLOCKED; prerequisite for INV-01/06/07 and any claim about W restore safety.

The preferred direction moves authority out of C, which addresses the observed C-only root mistake only if W's own historical commitment cannot be replayed. The proposal does not specify the persistent fact outside all permitted W rollback sets that distinguishes a valid latest W from an old restored W. Linearizability within a live authority incarnation does not itself define continuity after restoring/reinitializing the whole authority. Separate operators or signing credentials that survive C restore do not alone bind the signer to the latest W state.

**Conditional analytical counterexample, not an executed W exploit:** W commits epoch2; its state is restored to epoch1 while an accepted signing identity can still sign. Old A requests a fresh nonce-bound response. A valid new signature over the stale state is possible unless signing/admission is constrained by a non-replayable continuity fact. No historical packet replay is needed. The same issue applies to namespace deletion/recreation, total quorum rebootstrap, an old signer and a fresh client with no high-watermark memory.

**Required refinement:** identify W's trust root, durable commitment/linearization point, namespace/incarnation continuity, which restore actions are allowed, which actor can perform them, which independent state they cannot roll back, and the verifier's response when continuity cannot be established. Distinguish fault tolerance of live members from full-authority disaster recovery and anti-equivocation. State whether rolling back W data alone, credentials alone, or both is in scope. If every relevant state/key/policy can be restored together, either exclude that mode explicitly and remain blocked during recovery, or provide a separate root argument. Merely renaming C, retaining a valid TLS identity or declaring a quorum is insufficient.

This is a missing root contract acknowledged by the draft, not a claim that any particular W technology has been implemented incorrectly.

### E-P0-02 — Restored enforcement policy and cloned actor identity are unresolved

**References:** sections2–4, lines29,35–36,40,49,56,60. **Status:** BLOCKED for restore/clone invariants; conditional end-to-end enforcement remains PROPOSED.

W can govern only requests that reach and obey it. The proposal requires a SQL guard or independent verifier, but does not delimit which guard code, grants, trust anchors, supported backup versions and actor credentials may be restored. A legitimate pre-W or obsolete-verifier A/B backup could accept a C-only path, a retired W root or weaker policy without asking current W. Restoring only C need not have this effect; the broader INV-01 promise explicitly includes A/B/key restore and therefore needs a supported-restore boundary. If all permitted A/B backups already enforce W and the enforcement policy is separately protected, say how that restriction is verified before any SQL authorization path opens.

Likewise, declaring same-system-ID clones to be distinct actors does not distinguish them if they possess identical registrable credentials and verifier state. One logical owner identity can otherwise represent two physical database actors that both request fresh permits. Define actor incarnation/registration, clone rejection and fencing evidence independently of a copied system identifier or software key. An offline signature alone cannot prove that a signer or actor remains current.

**Required refinement:** specify the trusted computing/enforcement boundary and its restore/boot gate; distinguish C admin, A/B restore operator, trusted guard administrator and W custodian. State which privileged rewrites are excluded, instead of implicitly promising security against a database superuser who can bypass RLS. Explain how verifier policy/root-key epoch and actor admission survive supported restores and how all direct SQL/issuer/pooled paths remain covered. Verification material exposed to a restored guard must not confer W signing authority. No hardware, vendor or algorithm is selected by this requirement.

### E-P0-03 — Durable operation admission/hold/close is not yet a transaction contract

**References:** sections3–5, lines36–39,49,52–55,67. **Status:** BLOCKED for INV-03/05 and a commit-safety PoC specification.

The draft correctly says takeover must wait for holds. Missing are the ordering guarantees that make that statement enforceable: atomically recording OPEN with checking current owner/revocation; durable W acknowledgment before local authorization; hold validity at first and repeated use; close only after trustworthy durable local COMMIT/ABORT; and how cancellation, connection loss or W failover affects those facts. A nonce and transaction ID bind a response but do not close this distributed interval.

**Conditional schedule:** A obtains a permit; the guard's final online check succeeds; the hold is released, forgotten after W restart or judged dead from a lost connection; B activates; A's local COMMIT completes. Checking W twice without a durable exclusion covering the entire interval does not rule out this schedule. A permit delayed in transit must also not be newly admitted after revocation just because its nonce matches a request still waiting on A.

**Required refinement:** assign linearization/durability points to admission, revocation intent, activation, local effect/outcome and hold resolution; enumerate permitted interleavings and response meanings. Define an atomic serialized relationship between new admission and takeover. Explain how orphan holds survive all supported W recovery and cannot be silently released on disconnect, lease expiry, leader change or session absence. Distinguish authorized in-flight work, newly authorized work, local COMMIT and delayed returned responses; an already returned read is not retroactively revocable. Do not choose 2PC or any other implementation here: require a falsifiable lifecycle contract first.

### E-P0-04 — Safe orphan progress and promotion prerequisites remain unproved

**References:** sections4–5, lines54,64–73. **Status:** recovery progress BLOCKED; keeping FENCED_UNRESOLVED blocked is the correct conservative proposal, not a defect.

Section4 allocates/commits the successor epoch after quiescence/fencing; section5 first commits a higher/revoked epoch. These may be compatible if a revocation fence is distinct from granting a successor active authority, but the document has not assigned that meaning. A higher epoch or signed receipt must not be interpreted as permission to bypass unresolved outcomes. Resolution must remain possible, or remain explicitly blocked, even when the old owner is revoked.

The evidence terms at line68 are too broad to establish known COMMIT/ABORT: a copied/local ledger may be non-atomic with the relevant transaction, from another timeline/incarnation, or omit an already committed effect after restore. Absence is not abort. Hard fencing prevents later old-owner activity but does not undo an earlier committed effect. A manual approval or signature authenticates a decision/evidence record; it does not make an unknowable outcome known.

**Indistinguishable-history test:** in one history local effects committed and ACK was lost; in another they did not commit. If W sees OPEN and the only available local evidence is an earlier restored snapshot, the observations can be identical. Clearing as abort in both can duplicate effects; treating both as commit can omit effects. A separately specified conservative/idempotent effect protocol could alter that argument, but is not supplied here.

**Required refinement:** identify sufficient, trustworthy positive outcome/fencing evidence, identity/timeline/operation bindings, actual effect coverage and who may attest it; distinguish detached issuance ledger from local business transaction and external side effects. Define single-use resolution CAS, conflicting/replayed evidence rejection, receipt retention and rollback continuity. Reconcile revocation, FENCED_UNRESOLVED and successor readiness semantics. Otherwise exclude clearing from any initial PoC and keep it BLOCKED indefinitely. This review does not assert that safe reconciliation is impossible; it finds no general verified clearing algorithm in this proposal.

## 4. Findings — P1/P2

| ID / priority | Reference | Finding / required refinement | Status |
|---|---|---|---|
| E-P1-01 | Sections2–3, lines29,36,40 | Complete the authenticated permit contract: protocol/domain/namespace, root-key and authority incarnation, logical owner and physical actor, operation kind/intent binding, local cluster/boot/transaction identity, nonce lifetime/use state and strict response validation. Define how an old verifier learns that an old signing root is retired without trusting its restored cache. Backend PID/XID alone is not an incarnation credential. A signature proves origin, not current authority. No TTL or wire format is approved | PROPOSED; depends on P0-01/02; requires proof |
| E-P1-02 | Sections4–5, lines58,69–70 | Define idempotency-key namespace and retention, same-key/different-intent rejection, durable request-digest/outcome binding and read-after-ambiguous-write behavior. An activation retry must not accidentally allocate another epoch; an unresolved operation cannot be reclassified from a partial response. Define tombstone/receipt retention through backups and conflicting manual attempts | PROPOSED; requires proof; clearing still BLOCKED |
| E-P1-03 | Sections2/6/7, lines30,79–95 | Fault semantics and proof taxonomy need precision. A correct denial while W is down/stale is a GREEN negative assertion; disabling mandatory W enforcement must make that same security assertion RED. Do not accept an observed fail-open under an unmodified candidate as evidence of safety merely because the experiment wrapper detects it. Define minority/stale signer, delayed permit, W loss after final guard check, actual hard-fence failure and commit ambiguity schedules; post-restoration GREEN alone is insufficient | PROPOSED; all W fault tests NOT_RUN |
| E-P2-01 | Sections6–8, lines75–110 | Add claim/version/assumption-to-proof bookkeeping to the decision package. Distinguish legacy129 regression runs, unchanged rollback assertion on the legacy path, and that same invariant on a W-enforced candidate. Preserve assertions and avoid a legacy C-only fallback solely to keep old tests GREEN. This is evidence/wording hygiene, not an observed runtime bypass | PROPOSED documentation refinement |

## 5. Claim-by-claim disposition

PROPOSED means an unapproved design requirement. BLOCKED means a missing dependency prevents a safety/readiness claim. REQUIRES_EXPERIMENTAL_PROOF means NOT_RUN for W in this review, not a PASS inherited from D. Multiple labels can apply.

| Proposal claim | Disposition | Missing evidence / dependency |
|---|---|---|
| Candidate A preferred, C nonauthoritative | PROPOSED | Management may retain candidate; this review selects no technology |
| W linearizable and non-rollback across its own recovery | BLOCKED | E-P0-01; live consistency and recovery continuity are separate obligations |
| W identity/root/signing policy independent of all permitted restores | BLOCKED | E-P0-01/02, E-P1-01 |
| Candidate B invalidates every old signer by key/root change | PROPOSED / BLOCKED | Same independent retirement/fencing root problem; no escape by DB-only rotation |
| Candidate C manual permanent stop is globally safe | PROPOSED / REQUIRES_EXPERIMENTAL_PROOF | All old authorization endpoints must actually be fenced; a paused new coordinator alone is not enough |
| INV-01 no older generation can newly authorize | BLOCKED / REQUIRES_EXPERIMENTAL_PROOF | W continuity, restored enforcement, actor identity and commit ordering |
| INV-02 fresh end-to-end transaction permit | PROPOSED / REQUIRES_EXPERIMENTAL_PROOF | E-P0-02/03 and complete validation/transcript contract |
| INV-03 unique takeover / no unresolved prior authorization | BLOCKED / REQUIRES_EXPERIMENTAL_PROOF | Atomic admission/revocation, physical actor distinction, durable holds |
| INV-04 deny on uncertainty | PROPOSED / REQUIRES_EXPERIMENTAL_PROOF | W-specific outage/partition/ambiguity tests; no cached fallback |
| INV-05 no old signer/new late commit after takeover | BLOCKED / REQUIRES_EXPERIMENTAL_PROOF | Durable hold through known local outcome or proven fencing; delayed-response semantics |
| INV-06 root-key/actor/epoch binding | BLOCKED / REQUIRES_EXPERIMENTAL_PROOF | Non-restorable verification policy and clone/registration contract |
| INV-07 durable one-time audit and reconciliation | BLOCKED / REQUIRES_EXPERIMENTAL_PROOF | Receipts/tombstones share W root continuity obligation; evidence semantics unresolved |
| RESERVED/APPLIED/ACK/ACTIVE/READY activation chain | PROPOSED / REQUIRES_EXPERIMENTAL_PROOF | Transition guards, crash cuts and revoke-versus-active epoch meanings |
| Committed local apply ACK proves activation precondition | PROPOSED / REQUIRES_EXPERIMENTAL_PROOF | Candidate W integration; old authenticated C ACK experiment is not a W proof |
| Same-request lost-ACK retry returns one outcome | PROPOSED / REQUIRES_EXPERIMENTAL_PROOF | E-P1-02; application receipt discard in D is not wire-loss proof |
| Full C restore cannot revive A under W | BLOCKED / REQUIRES_EXPERIMENTAL_PROOF | Dependencies P0-01/02/03; existing legacy D outcome remains FAIL_SECURITY |
| Ordinary orphan deny survives W crash/restore | PROPOSED / REQUIRES_EXPERIMENTAL_PROOF | D established C orphan denial only; W OPEN continuity not executed |
| KNOWN_COMMIT / KNOWN_ABORT can safely release recovery | BLOCKED | E-P0-04; precise evidence and effect semantics absent |
| FENCED_UNRESOLVED does not authorize successor | PROPOSED / REQUIRES_EXPERIMENTAL_PROOF | Appropriate safety rule; no recovery-progress claim |
| Physical same-identity clone/PITR/partition safety | BLOCKED / NOT_RUN | Distinct-cluster logical copy and C channel refusal do not prove these modes |
| Minimal PoC/RED-GREEN plan | PROPOSED; not yet implementation-ready | Resolve contract prerequisites and taxonomy first; explicit Management authorization afterward |

## 6. Trust and operational assumptions that must be explicit

| Boundary | Required decision / retained limit |
|---|---|
| W administrator / backup / quorum-recovery control | State exactly which restore/rebootstrap and insider actions are in scope, the irreversible continuity fact they cannot alter, and how all-old-member recovery fails closed |
| W signer and verifier-policy custody | Define non-restorable namespace/key-policy continuity and authority to retire/re-establish roots. A private key merely surviving C restore does not itself prove W state freshness |
| Application guard / restore operator | Name the trusted code/grants boundary, supported snapshot versions and independent admission gate. Do not promise RLS security against an excluded trusted superuser while leaving that exclusion unstated |
| Physical actor / old endpoint fence | Specify externally credible incarnation and proof that all relevant old execution/storage/credential paths are fenced, including prepared work if supported. A copied node ID is not that proof |
| Outcome/effect witness | Bind evidence to the relevant transaction, operation, database incarnation/history and effects; do not trust restored C or a detached ledger by default |
| Recovery operator | Bound authorization, separation of duties, competing cases and immutable receipt custody; operator approval cannot replace missing safety evidence |
| Availability / supported failure domain | Indefinite fail-closed pause is permitted. Document operator/failure-domain independence as an assumption until proven; an extra database on one CI host cannot establish production independence |

The draft's exclusion for an actor controlling both W root and credentials is legitimate only when the boundary is explicit. It must not silently exclude the ordinary W restore event whose safety is being claimed. No key is assumed nonrecoverable or nonclonable merely because it is outside a C backup; custody evidence is required.

## 7. Required ADR amendments before asking Management to authorize a PoC

This is a review checklist for the existing proposal, not a new architecture or implementation plan:

1. Resolve E-P0-01 with a root/namespace/restore threat contract and an honest list of assumed versus enforced properties; include verifier bootstrap and full-authority recovery.
2. Resolve E-P0-02 with supported snapshot/guard versions, clone/incarnation admission and key-policy retirement boundaries. State excluded privileged capabilities explicitly.
3. Resolve E-P0-03 with a transition/linearization and crash-cut contract for durable OPEN, local authorization/outcome, hold close, revocation and successor readiness. Clarify section4 versus section5 epoch meanings.
4. Either keep orphan resolution out of the first bounded PoC and BLOCKED, or provide the additional algorithm/evidence contract in E-P0-04 for separate review before enabling clearing.
5. Adopt E-P1-01/02 validation and retry requirements without freezing a wire format, TTL, crypto algorithm, product or vendor. Define evidence taxonomy per E-P1-03/E-P2-01.
6. Request an explicit Management decision for the exact experiment/assumptions after these revisions. Do not infer approval from this review or the preference for A.

## 8. Separate experiments required after authorization — all NOT_RUN here

| Proof obligation | Required falsifiable observation |
|---|---|
| C rollback against a genuinely current W | Preserve the original old-owner-denial assertion; show it GREEN under supported C restores and RED when mandatory W enforcement is deliberately removed |
| W state rollback/rebootstrap and old signer | Restore old W data with current credentials; stale/clone signing endpoint; fresh client/verifier with restored policy; authority namespace reuse. Demonstrate denial or keep mode explicitly BLOCKED, not merely restore healthy W and retest |
| Guard/actor restore | Pre-W/old verifier snapshot and same-ID physical clone if supported; copied actor credentials; all raw SQL, issuer and pooled routes. Unsupported restore versions must be quarantined before authorization |
| Admission/COMMIT/takeover cuts | Pause before/after OPEN durable ACK, permit delivery/first use, final guard check, local durable COMMIT/ABORT and W close; race takeover, crash either side and drop replies. Never observe successor READY while old authorized work could still commit |
| W partition / minority / delayed response | Authenticated stale or conflicting W response, one-way loss, signer isolation, late valid permit and W loss around commit; deny new unsupported use and block ambiguous takeover |
| Reconciliation if later included | Known commit/abort, indistinguishable unknown histories, old timeline, prepared transaction if supported, conflicting evidence, two operators, replayed receipt, W restore after resolution and external effects. Unknown remains BLOCKED |
| Regression/evidence integrity | Keep legacy129 and the rollback safety assertion; distinguish which path is exercised, RED mutations versus GREEN fault denial, exact source/merge receipts and restoration checks. Do not change assertions to hide a failure |

An oracle-like W fixture with assumed irreversible history could later investigate integration and scheduling. That would not prove the assumed W root itself; the report must keep this distinction. No such fixture or test is authorized or created by this review.

## 9. Technical background and limits of this review

Primary references consulted 2026-11-06 solely to check boundary assumptions, not select a W product:

- [Official etcd3.6 disaster recovery documentation](https://etcd.io/docs/v3.6/op-guide/recovery/), Revision Difference / Restoring from snapshot: recovery can move observed revisions backward and creates a new logical cluster. This is an illustrative reason to demand a separate recovery-continuity argument, not a recommendation for etcd. A revision bump is not by itself a CAC authorization-epoch/key-retirement proof.
- [PostgreSQL17 PREPARE TRANSACTION](https://www.postgresql.org/docs/17/sql-prepare-transaction.html): prepared work is detached from its original session, stored on disk and can later commit from another session. If supported, such work belongs in the fencing/outcome model. This review does not assert that D uses prepared transactions or propose adopting two-phase commit.

New W properties are NOT_RUN and no formal model was executed. Conditional schedules above are analytical review counterexamples, not empirical W findings. Existing D rollback FAIL_SECURITY is observed evidence accepted by the management ruling; its129 GREEN cases are not transferred to W. Local validation in this mission checks document references, pinned hashes and a documentation-only diff; it does not test security.

## 10. Final recommendation and governance

**Not yet ready to propose implementation of an anti-rollback PoC in the current form. Targeted design refinement is required; wholesale redesign is not recommended by this review.** Candidate A can remain on Management's agenda. A future deny-only integration experiment may be considered after explicit root/enforcement/lifecycle assumptions and acceptance criteria are agreed; it must not claim demonstrated W anti-rollback or safe orphan clearing from an assumed oracle.

Four P0 contract blockers, three P1 refinements and one P2 evidence-traceability refinement are recorded. No new executable defect or exploit against an implemented W is claimed. The conservative pause, no cached fallback, durable unresolved intent, no timeout clearing and separate-authorization governance are sound requirements worth preserving.

`SOURCE-001 / GATE-SOURCE = BLOCKED`; Architecture Gate9 OPEN; S0-09D rollback mode FAIL_SECURITY/BLOCKED; E protocol PROPOSED. Prior PRs11/16/18/20/22 remain Draft and unmerged. No APR-033/034/035/036 change, Production permission, technology selection, identity/onboarding work, protocol ratification, historical-source claim or Sprint0 completion. Publish this report in a separate Draft PR and register its findings in Issue23. **The next implementation step requires an explicit Astra Management decision.**
