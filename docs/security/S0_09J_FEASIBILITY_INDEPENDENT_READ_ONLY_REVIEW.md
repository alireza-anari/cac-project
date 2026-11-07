# CAC — S0-09J Independent Read-Only Feasibility Review

**Date:** 2026-11-07
**Reviewer:** Separate adversarial security architecture review agent, commissioned through the coordinating agent.
**Verdict:** **`NEGATIVE_QUALIFICATION_DEFENSIBLE_KEEP_A`**
**Scope:** Documentation and official public-source analysis only; no empirical PASS, execution authorization or accepted recovery protocol.
**Tracking:** [Issue #36](https://github.com/alireza-anari/cac-project/issues/36), architecture [#33](https://github.com/alireza-anari/cac-project/issues/33), parents #28/#23.
**Origin:** `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`.

## 1. Independent judgment and its limits

The negative **present end-to-end qualification** of the two studied sketches is defensible. Their unresolved legal-transition binding, outcome semantics and mandatory enforcement are real design gaps. Keeping majority-catastrophe restoration unsupported is consequently defensible. I found no source-supported reason to promote either sketch to a qualified CAC authority, and no argument supporting universal impossibility.

My strongest challenge is to the possible interpretation of “no credible candidate.” A bounded independent surviving E and mandatory enforcement boundary can be a finite trust base. It need not survive its own total destruction, simultaneous compromise of every administrator or arbitrary rollback of every trust anchor to be worth feasibility research. Moving the surviving-majority assumption to an **actually independent** E can increase the supported failure envelope from ordinary R failure to R-majority catastrophe. That is a meaningful architectural difference, even if E-majority catastrophe remains unsupported. Report §§1 and 3 explicitly allow bounded assumptions; those qualifications govern my verdict over the potentially overbroad shorthand in §4.1.

This review therefore accepts neither “E is impossible” nor “no deployment yet proves infeasibility.” Missing deployment is expected in documentation-only feasibility work. The present rejection is justified by incomplete system specification and unidentified custody/enforcement boundaries, supplemented by absence of qualification evidence. It is not an impossibility theorem or a requirement to deploy hardware before proposing a credible bounded design.

I did not author the candidate report and independently chose the verdict after reading it and checking official sources. This establishes **separate-agent role independence only**. The coordinator authored the candidate and supplied the assignment/provenance; both agents use the same environment and organizational context. External, organizational, financial and institutional independence are not established. This is not a third-party certification.

## 2. Exact inputs, method and evidence boundaries

| Input | Immutable identity and use |
|---|---|
| [Candidate feasibility R0](https://github.com/alireza-anari/cac-project/blob/f513aa7ff71d55f964758cd1548520594c5309fd/docs/architecture/S0_09J_EXTERNAL_CONTINUITY_FEASIBILITY_R0.md) | Entire report read; local HEAD independently checked as `f513aa7ff71d55f964758cd1548520594c5309fd`; report blob `3350402dc26a1283118481f9bdb16b95a1d57174`. |
| [Current management ruling](https://github.com/alireza-anari/cac-project/blob/0f5bc81d372c90788a30cbfa5e65e322b17e4f86/docs/architecture/S0_09J_FEASIBILITY_MANAGEMENT_RULING.md) | Read from review baseline main `0f5bc81d372c90788a30cbfa5e65e322b17e4f86`; its acceptance is a review input, not the reviewer’s premise of correctness. |
| [R1 scope and five gates](https://github.com/alireza-anari/cac-project/blob/0f5bc81d372c90788a30cbfa5e65e322b17e4f86/docs/architecture/S0_09I_R1_SCOPE_AND_E_FEASIBILITY_GATES.md) | Normative requirements checked against candidate reasoning. |
| [R1 ruling and research authorization](https://github.com/alireza-anari/cac-project/blob/0f5bc81d372c90788a30cbfa5e65e322b17e4f86/docs/architecture/S0_09I_R1_REVIEW_RULING_AND_S0_09J_RESEARCH_AUTHORIZATION.md) | Read for permission and inherited evidence boundaries. |

The coordinator verified live GitHub/main/PR metadata; I independently checked both local worktree HEADs, the report blob and the clean initial review worktree. I did not independently audit GitHub delivery history, underlying H test artifacts, deployed infrastructure or historical source recovery. Prior experiment statuses below are governance inputs, not rerun findings.

Method: adversarial deductive review of failure envelopes, state/permission ordering, all fourteen proposed cuts and possible bounded counterexamples to a negative conclusion; independent public official-source retrieval on 2026-11-07. Source versions and precise limits are in §9. Direct PDF opens initially failed for some TCG documents; following their official landing-page links succeeded. No device access, accounts, secrets, protocol implementation or empirical security test was used. The only authored artifact is this Markdown review.

## 3. Primitive facts independently checked

**TPM counters:** Published TCG Library v185 Part 1 §34.2.6.3 specifies an NV counter modified by increment; the first increment after initialization must exceed prior values of the same Name over TPM lifetime. Same-Name deletion/redefinition is expressly prevented from lowering it. Hybrid-counter rules preserve nondecrease after unorderly startup, potentially skipping forward. NV-extend persistence differs, especially for orderly indices [O1]. The candidate correctly preserves these facts. A generic “delete the index and reset to zero” rebuttal would be wrong. A replacement device or changed Name cannot inherit resource history merely from numerical monotonicity; that latter statement is a CAC deduction.

**Lifecycle and keys:** Part 3 §24.6 says Clear flushes storage/endorsement resident objects, deletes non-platform-created NV indices, changes the storage seed and resets several authorization/policy values. It requires platform or lockout authorization; §24.7 permits platform authorization to reenable Clear after disabling it [O3]. These are concrete custody concerns, not evidence that Clear rolls back every counter. Loss/change of attestation keys affects authenticated continuity independently of counter arithmetic. A fresh key requires trusted enrollment; a surviving old key alone proves neither current policy nor latest application state.

**Attestation:** Part 2 §10.11.8 records index Name, offset and certified contents; Part 3 §31.16 supports NV-content certification [O2/O3]. The signed data does not itself validate CAC legal transitions or PG outcomes. RATS separates evidence appraisal and relying-party decisions [O5]; mandatory enforcement still needs its own argument.

**Errata omission:** I inspected v185 Errata Version 1, March 12, 2026, including all listed changes. §§2.7–2.8 clarify certification hashing for schemes without a scheme hash and possible size rejection for large ML-DSA NV certification. Its introduction labels the errata non-normative until incorporated [O4]. It does not reverse the cited counter guarantee or supply journal semantics. The candidate source ledger should include it; this is a P2 completeness correction, not contrary evidence overturning its vote. No cryptographic algorithm is selected here.

## 4. Could a bounded alternative satisfy G1 and G4?

I challenged the negative result against three bounded arrangements already within the research families, without proposing a new protocol or recommending a product.

| Bounded possibility | Why it could satisfy G1 plus G4 in principle | What prevents present qualification |
|---|---|---|
| Independently governed surviving state-machine E and current external resource controller | Current E quorum retains the latest legally committed state while R/W/application images rewind; every protected effect remains behind the surviving controller. Finite quorum survival is a legitimate stopping assumption. | Membership, restore privileges, signer/enrollment continuity and resource-path dominance are unspecified. A spare ordinary database plus optional client consultation does not establish these properties. |
| Protected physical state plus a non-restored enforcement boundary | A named physical lifetime fact could distinguish old R state while a separately protected controller rejects restored pre-E code before effects. | Compound state/journal association, constrained updater, lifecycle and actual path coverage are unresolved. Counter nondecrease alone cannot establish admission legality. |
| Surviving current installation/policy boundary that refuses restoration entirely | A narrow deny-only envelope can remain safe without reconstructing lost bodies if old routes cannot operate and prior obligations remain excluded. | Incumbent PG work, local/direct/admin effects and control-plane custody must be bounded. A gateway blocking only new connections cannot dominate already admitted effects. This is no availability recovery claim. |

These possibilities defeat a universal negative argument. They do not contradict the report’s explicit current-qualification conclusion. Nor does arbitrary unbounded adversarial power provide a useful rejection test: if the threat model permits rewriting the final enforcement root without limit, the claimed boundary has already been removed by assumption.

For E1, stating that a surviving independent quorum merely repeats H’s limitation is incomplete if taken to dismiss its value. It can cover R’s catastrophe because its membership and custody differ. Its own total rewind must either be prevented within the claimed envelope or explicitly yield unsupported/deny; a succession of unnamed witnesses is unnecessary. For E2, meaningful physical monotonicity exists at primitive level, while legal H updates and enforcement remain unqualified. Neither family currently documents enough to claim an implementable complete bounded CAC arrangement.

## 5. Five P0 gates and exact evidence that could change this vote

All five remain **DESIGN_BLOCKED**. Research-level necessary invariants are not gate closure.

| Gate / finding | Independent assessment | Minimum documentary evidence to reopen qualification |
|---|---|---|
| G1 / I-P0-01 | E1 lacks a named terminal continuity/custody boundary. E2 supplies a relevant primitive but no qualified compound authority binding. This combines missing evidence with an actual unspecified state/lifecycle contract. | Finite supported adversary envelope; named surviving artifact and legal updater; identities, reset/restore/firmware/key/enrollment powers; explicit behavior on loss; no assumption of universal survivability. |
| G2 / I-P0-02 | Head equality is not a complete-history argument unless every legally admissible OPEN, same-epoch mutation, retirement and checkpoint is bound. Missing bodies preclude reconstruction; missing exact outcomes preserve UNKNOWN. | Recoverable authenticated pending bodies, prefix/suffix and absence proofs, transaction/incarnation/idempotency mappings, compaction/retention rules and inability to discard live obligations. A separate deny-only scope may need less availability, never a false empty set. |
| G3 / I-P0-03 | The seven invariants are useful rejection rules; they do not give a crash-recoverable grant/revoke/close protocol. This is a design deficiency beyond absence of deployment. | Complete legal-state model for R/E disagreement and local outcome, exact usable-permission point, recovery/idempotency rules for all ACK losses and proof that successor READY never overlaps possible prior effects. No specific transaction mechanism is prescribed. |
| G4 / I-P0-04 | Current E does not compel restored SQL to consult it. The route inventory is honest but a requirement list is not enforcement architecture. | A concrete, independently surviving admission boundary with trusted current policy floor, all issuer/SQL/private/RLS/direct/pool/local/admin routes, loaded code and active/prepared transactions accounted for; privilege exclusions stated. It must control effects, not merely label endpoints quarantined. |
| G5 / I-P0-05 | Replacement identity cannot establish disappearance of an old resource’s obligations. A new device or namespace can bypass numerical comparisons if predecessor binding is absent. | Resource identity across aliases/incarnations, authenticated predecessor and old-actor/key retirement continuity, no clean genesis on missing history. Genuinely distinct resource isolation must include external effects. |

A complete bounded dossier resolving the **design** gaps could change my research recommendation without prior deployment. It would still not establish empirical security, close P0 findings automatically or authorize a PoC. Actual security qualification would require later separately governed evidence against the stated envelope. Conversely, evidence of an unavoidable legal-history ambiguity or an authorized unguarded effect path would strengthen rejection; administrative separation alone would not weaken it.

G2 reconstruction and Lane3 must stay distinct. Even perfect reconstruction can reveal a real unresolved operation and require indefinite exclusion. A current authenticated lookup can recover a previously canonical CLOSED record; it cannot convert uncertain work into a newly justified closure. The outcome witness must identify the operation, DB incarnation and effect, and itself remain trustworthy under the selected restore powers.

## 6. Individual assessment of fourteen hypothetical cuts

Each row is **logical analysis / NOT_RUN**. None is a test result, observed exploit or empirical PASS. “Deny” is conditional on G4 actually holding. The cuts falsify weaker designs under their prerequisites; satisfying their stated result would not exhaustively prove a future protocol.

| Cut | Prerequisite and adversarial reasoning | Hole, limit or additional obligation |
|---|---|---|
| J-C01 | E’s backup and signer can jointly rewind, and verifier has no surviving latest-state floor. A fresh nonce authenticates a fresh response about old state. The negative example is sound. | No detection signal exists merely from R/E agreement. It does not attack a bounded surviving E quorum; that prerequisite must be kept explicit. |
| J-C02 | Epoch comparison omits an OPEN created later in the same epoch. Equal epoch then cannot justify an empty pending set. | Require every safety-relevant operation and policy mutation in authenticated latest state, not just one example OPEN. Head commitment also needs complete-body verification. |
| J-C03 | R-only durable OPEN is treated as permission before E inclusion. This violates the report’s before-use invariant. No usable permission should exist. | A staged candidate can remain conservatively blocking; its existence does not prove a local effect occurred. Recovery must not discard it on timeout or reinterpret an R ACK as a grant. |
| J-C04 | E may have durably granted while ACK was lost; changing retry identity can hide the first operation. Retain the old possible hold. | A new operation identifier is not inherently forbidden if separately legitimate and compatible; it cannot erase an old hold or evade resource exclusion. Exact original-id lookup must authenticate digest and incarnation. |
| J-C05 | Counter update and head/body association have a crash window. A larger counter with an older body is insufficient compound authority. | This attacks a torn multi-step binding, not monotonicity itself. Conservative blocking is necessary but does not specify recovery from skipped counts or identify the unique legal candidate. |
| J-C06 | A caller can increment a real primitive and certify a stale digest without legal-prior-state validation. Numeric progress then authenticates no legal transition. | Possession of update privilege must be within the threat model. A constrained, independently trusted legal updater excludes this prerequisite; certification by itself does not. |
| J-C07 | Reply arrives after revoke and is used for a substituted/new PG transaction. Rejecting that use is correct. | Distinguish an exact grant canonically ordered before revoke: its allowed completion can occur afterward while its hold excludes successors. Arrival time alone neither revokes old work nor supplies first-use serialization. |
| J-C08 | PG COMMIT may persist while its reply disappears; client/session loss is used to clear the hold. That inference is invalid. | Local disconnection, timeout and lack of a visible active transaction are not exact ABORT evidence. A later trusted exact outcome may resolve status; a truly unknown operation remains blocked. |
| J-C09 | E publishes usable CLOSE before durable exact outcome; successor is admitted while old work can still commit. This is a genuine overlap counterexample. | An internal tentative close that is unusable for READY need not violate safety. Distinguish proposal/receipt from authoritative close in both roots, including lost close ACK. |
| J-C10 | A partitioned stale signer/cache authorizes concurrently with another branch. Without current serialization, old-work holds and enforced policy, conflicting permission is possible. | A properly authenticated quorum read and nonreplayable exact admission may deny the stale side within a finite failure model. Partition itself is not proof every family must fail. |
| J-C11 | Restored SQL/verifier and an incumbent pool route can affect the resource without current E admission. E’s continued correctness is irrelevant to that path. | Distinguish a bypassed new permission from completion of old legitimately admitted work. New-client denial or isolation request proves neither incumbent termination nor durable outcome. |
| J-C12 | An old header/prefix is accepted despite missing OPEN body or policy/tombstone suffix. Reconstruction cannot establish completeness. | A trustworthy current commitment can expose inconsistency without recovering data; authenticate complete replay before progress. Missing bytes mean denial, not proof the underlying operation was absent. |
| J-C13 | New device/root/actor is enrolled against the same resource while predecessor obligations are lost. Empty-history enrollment launders possible old effects. | Hardware loss may force permanent exclusion. A genuinely distinct, independently isolated resource is analytically different; renamed identity or operator ceremony does not demonstrate that isolation. |
| J-C14 | Exact positive outcome and canonical CLOSED already persist in both current roots; only final response is lost. Recovering that record does not invent closure. | Query must establish current canonical identity, digest, policy and incarnation. If any premise is unknown, retain the hold. This row is not permission to resolve orphan UNKNOWN via status speculation. |

The matrix is substantial but not exhaustive: it does not itself specify simultaneous failures, compaction/replay concurrency, outcome-observer equivocation or total custody compromise. Those belong in any later bounded model, not in invented PASS claims. PostgreSQL’s prepared-transaction facility can retain distributed obligations for extended periods under external management [O7]; its existence supplies no missing R/E ordering argument.

## 7. Option A honesty and retained P1/P2 risks

Option A correctly limits support rather than promising a runtime recovery defense. A responsive stale R majority can continue serving internally coherent old authority. If the only current guard is also restored or bypassed, a runbook prohibiting restore cannot force global denial. The honest state is **GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED / SECURITY_INCIDENT**. A surviving mandatory guard must deny unverifiable new work; legitimately admitted old work still has its old hold. Successful stale detection does not resolve missing history or make an outage finite.

| Retained risk | Assessment and evidence needed |
|---|---|
| I-P1-01: incident/quarantine | Silent coherent rewind need not announce itself. Require independently current observation and actual route-isolation evidence; request, receipt and effective quarantine are different. Previously admitted effects remain accounted for. |
| I-P1-02: outcome custody | Outcome observer rollback or privileged PG operator can invalidate alleged close evidence. Require exact operation/incarnation/effect attribution and explicit observer, superuser, storage/restore and external-effect assumptions. Attestation of a head is not an outcome receipt. |
| I-P1-03: operational feasibility | Independent authority, sustained journal retention, monotonically protected updates, unavailable outcomes and lifecycle procedures can impose indefinite downtime. A qualitative burden inventory is justified; numeric cost, throughput, endurance, latency, RPO/RTO and availability remain unmeasured. |
| I-P2-01: evidence/provenance | Preserve current-qualification wording, finite-boundary qualification and exact source versions. Add v185 Errata1 to the candidate ledger; distinguish printed page numbers from PDF offsets (Part 2 certification structure is printed p.161). No material counter-specification error was found. |

These notes do not require another generic rewrite before retaining Option A. They constrain how the accepted negative shorthand may be used. If a future ruling asserts impossibility, rejects every independently surviving E by recursive demand for another root, or claims missing deployment alone disproves feasibility, that would require targeted correction and a different review decision.

## 8. Unchanged project disposition

All G1–G5 / I-P0-01..05 remain **DESIGN_BLOCKED**; real external continuity, independent custody, catastrophic-majority recovery and simultaneous old-verifier behavior remain **SECURITY_UNPROVEN / NOT_RUN**. Legacy S0-09D C-only rollback remains **FAIL_SECURITY**. Inherited H evidence remains bounded to a surviving non-restored majority and is not independently recertified here. Actual policy retirement and literal stale Raft snapshot/WAL import remain **NOT_RUN**. Lane3 orphan OPEN_UNKNOWN release remains **P0 BLOCKED / NOT_RUN**.

SOURCE-001 / GATE-SOURCE remain **BLOCKED**; Gate #9 and architecture #33/#28/#23 remain **OPEN**. This document closes no issue, changes no prior Draft/unmerged PR, approves no Production use, protocol, implementation, source baseline, APR-033..036, identity/onboarding, infrastructure, keys, vendor or hardware. No code, SQL, migrations, workflows, tests, CI, PoC, dependencies, device commands, commits, pushes, merges or external comments were performed by this reviewer.

## 9. Independently retrieved official-source ledger

Versions are retrieval-time references, not claims of device compliance. Source facts above are narrow; CAC conclusions and hypothetical traces are reviewer deductions.

| Ref | Official source/version inspected | Evidence scope and limitation |
|---|---|---|
| O1 | [TCG Library v185 Part 1, March 12, 2026](https://medias.cdn.trustedcomputinggroup.org/production/Trusted_Platform_Module_2_0_Library_Part_1_Architecture_Version_185_pub_2a3392dc49.pdf), §§34.2.4, 34.2.6.3, 34.2.6.5; reached through [official library index](https://www.trustedcomputinggroup.org/resources/documents/tpm-library-specification) | Counter lifetime/nondecrease and different index persistence. No selected physical instance or CAC transition validation. |
| O2 | [TCG Library v185 Part 2](https://medias.cdn.trustedcomputinggroup.org/production/Trusted_Platform_Module_2_0_Library_Part_2_Structures_Version_185_pub_c0a962a931.pdf), §10.11.8, printed p.161 | Certified NV data structure, not legal completeness/outcome semantics. |
| O3 | [TCG Library v185 Part 3](https://medias.cdn.trustedcomputinggroup.org/production/Trusted_Platform_Module_2_0_Library_Part_3_Commands_Version_185_pub_87a5c10230.pdf), §§24.6–24.7, 31.16 | Clear/control privileges, key-context and NV certification boundaries; not universal counter reset or device qualification. |
| O4 | [TCG v185 Errata Version 1, March 12, 2026](https://medias.cdn.trustedcomputinggroup.org/production/Eratta_Trusted_Platform_Module_2_0_Library_Version_185_pub_17260f83c0.pdf), entire ten-page document, especially §§1, 2.7–2.8 | Certification caveats; non-normative status. No change to cited counter rule identified. |
| O5 | [RFC 9334, January 2023, Informational](https://www.rfc-editor.org/rfc/rfc9334.html), architecture and freshness | Attestation/appraisal/relying-party separation; no automatic SQL enforcement. |
| O6 | [etcd v3.6 API guarantees](https://etcd.io/docs/v3.6/learning/api_guarantees/), KV and completed-operation definitions | Durability/strict serializability within its system contract and client uncertainty after disruption; no whole-authority rollback or PG atomicity theorem. |
| O7 | [PostgreSQL 17 §66.4, Two-Phase Transactions](https://www.postgresql.org/docs/17/two-phase.html) | External transaction management and persistent prepared state; no selected CAC protocol. |
| O8 | [RFC 9162, December 2021, Experimental](https://www.rfc-editor.org/rfc/rfc9162.html), CT model and consistency/freshness framework | Append-only-prefix evidence is distinct from latest CAC admission. It cannot fill missing operation bodies or enforce protected effects. |

**Final independent vote: `NEGATIVE_QUALIFICATION_DEFENSIBLE_KEEP_A`.** The vote retains unsupported catastrophe restoration, conditional current-guard denial and possible indefinite downtime. It is bounded to the pinned sketches, leaves every P0 open, and explicitly leaves room for a finite independently surviving authority/enforcement arrangement to change a future feasibility judgment.
