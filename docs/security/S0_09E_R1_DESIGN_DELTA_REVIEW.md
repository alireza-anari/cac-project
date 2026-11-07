# S0-09E R1 — Independent design delta review

**Date:** 2026-11-06 (Asia/Tehran). **Role:** Astra Security Architecture Reviewer / Work. **Audience:** Astra Management. **Tracking:** [Issue23](https://github.com/alireza-anari/cac-project/issues/23).

**Disposition: READY_TO_REQUEST_SCOPED_LANE1_POC_AUTHORIZATION / NOT_AUTHORIZED_TO_IMPLEMENT / SECURITY_PROOF_BLOCKED.** R1 is sufficiently explicit to ask Management to consider only an assumption-labeled, deny-only W-oracle integration experiment. No further redesign is required for that limited request. This review grants no implementation permission. Lane2 and Lane3 remain BLOCKED / NOT_RUN.

## 1. Pinned inputs and limited scope

- Reviewed [R1](https://github.com/alireza-anari/cac-project/blob/29709ad3cb15380653deb7b1c1c52e88725d2a92/docs/architecture/S0_09E_TARGETED_DESIGN_REFINEMENT_R1.md) at live management main **`29709ad3cb15380653deb7b1c1c52e88725d2a92`**.
- R1 last modifying commit: **`31d269db3cb6ca698ffdbd9a04da2fc81fa622af`**. Management main additionally records status; those commit identifiers have different purposes.
- R1 Git blob: **`4d340ba27ddd22e518ecdfbdbb74acbb0acc787b`**, verified in the remote tree and locally. File-content SHA-256: **`d0ad961546b6b1af4766f6d2d46a5c59283df11cf2bd780ae5ad0a32f96947d4`**.
- Accepted earlier review: [Draft PR24](https://github.com/alireza-anari/cac-project/pull/24), exact **`dda6fea3347e582dfdcfc27299fbc8336b7233a0`**, [report](https://github.com/alireza-anari/cac-project/blob/dda6fea3347e582dfdcfc27299fbc8336b7233a0/docs/security/S0_09E_DESIGN_READ_ONLY_REVIEW.md). Its eight findings are the baseline, not reopened as a fresh review.
- Parent proposal blob remains **`5c24e2034f539d3a6f6c59903c78ae17abcb01bd`**. Also read the current management acceptance/R1 comment in Issue23. Line numbers below refer to the pinned 87-line R1.

This is a source/document delta assessment of whether previously missing requirements are now defined or explicitly excluded sufficiently for Lane1 scoping. It is not a new root design, full protocol specification, formal proof, empirical W review or third-party certification. Independence is from authorship of the management refinement; prior CAC reviewer/implementation involvement is unchanged from the accepted review. Only this new Markdown report is added. R1, the parent proposal, PR24, code, SQL, migrations, security tests, workflows and APRs are untouched.

## 2. Four P0 findings — design coverage versus security closure

| Accepted finding | R1 delta / reference | Contract-level assessment for Lane1 | Security/evidence status |
|---|---|---|---|
| **E-P0-01: W continuity** | Lines19–32 distinguish unchanged trusted W from W-root DR; identify continuity commitment fields, durable advancement, signing-policy continuity, restore/namespace scope and independent custody; lack of a real root means pause | **COVERED_FOR_LANE1_SCOPING.** The assumption is now honest and bounded. Lane1 can assume the oracle; it cannot present that assumption as a root implementation | Root remains **BLOCKED / NOT_RUN**, Lane2. No continuity mechanism or custody system proved |
| **E-P0-02: verifier and cloned actor** | Lines36–40 require a non-restored installation/policy manifest, independent admission, quarantine of old C-only/pre-W guards, all-path coverage and separation of logical owner from physical incarnation; physical clones may be excluded | **COVERED_FOR_LANE1_SCOPING.** Old verifier/actor admission must deny in the model unless independently admitted. Actual measurement, nonclonability and privileged-operator resistance are not assumed to have been built | Enforcement/actor properties **PROPOSED / NOT_RUN**. Same-identity physical clone safety remains **BLOCKED** if independent exclusion is unavailable |
| **E-P0-03: OPEN-to-COMMIT ordering** | Lines44–53 define serialized durable OPEN before permit, fresh first use, revoke barrier, hold preservation, positively evidenced CLOSE and no successor READY/live permit while old work could commit; prepared work addressed or prohibited | **COVERED_FOR_LANE1_SCOPING.** Enough observable ordering constraints and crash cuts to build a falsifiable experiment. A concrete implementation must satisfy them; two online checks alone still do not suffice | Lifecycle correctness **PROPOSED / NOT_RUN**. No atomic W/local-DB implementation or crash safety demonstrated |
| **E-P0-04: orphan outcome/reconciliation** | Lines57–64 separate REVOKING, FENCED_UNRESOLVED and SUCCESSOR_READY; reject signatures/missing sessions/old ledgers as outcome proof; explicitly exclude orphan clearing from the first experiment | **COVERED_BY_EXCLUSION_AND_DENIAL for Lane1.** Unknown stays blocked; no safe-progress algorithm is needed to test denial. Revocation intent no longer implies successor activation | Safe clearing remains **BLOCKED / NOT_RUN**, Lane3. Known/unknown outcome handling still requires implementation evidence |

**None of the four P0 security risks is marked CLOSED or empirically resolved.** Their earlier definition gaps are sufficiently addressed or excluded for this narrower lane. The review recommendation changes because R1 narrows the question and defines the lifecycle, not because new security evidence appeared.

Answers to the four P0 questions are therefore: W's trust/recovery boundary is explicit and honest as an assumption; independent admission/quarantine is required, not observed; transaction ordering is now falsifiable, not proved; ambiguous orphan OPEN must remain blocked without an alternative release path.

## 3. P1/P2 delta coverage

| Accepted finding | R1 reference | Assessment | Remaining status |
|---|---|---|---|
| **E-P1-01: permit/identity/validation transcript** | Line68; lines25–29,36–40,45–46 | Covers domain/protocol, root and policy epoch, namespace, owner/incarnation, intent digest, local cluster/boot/transaction binding, op ID and nonce-use state; separates signature provenance from current authority and public verification from signing capability | **COVERED as future requirements; PROPOSED / NOT_RUN.** No algorithm, serialization, TTL or real root retirement approved |
| **E-P1-02: retry and idempotency** | Line69; lines45,48,62 | Same key/different digest rejects; ambiguous admission uses the same key and status query; missing COMMIT evidence preserves OPEN_UNKNOWN; receipt/tombstone continuity required for supported recovery | **COVERED as contract; PROPOSED / NOT_RUN.** No lost-wire-ACK or durable-retry proof yet |
| **E-P1-03: fault semantics and RED/GREEN taxonomy** | Line70; lines46–53 | Correctly distinguishes GREEN fault-present denial from RED caused by deliberately disabling enforcement, and lists late/stale signer, transport/leader, commit and downgrade cuts. Post-restoration GREEN alone cannot establish denial under fault | **COVERED as proof requirements; experiments NOT_RUN** |
| **E-P2-01: evidence/path bookkeeping** | Lines71,81,85 | Legacy129 regression observations, legacy rollback FAIL_SECURITY and new W-path NOT_RUN are separate. Original rollback assertion and meaning retained; no C-only fallback merely to preserve counts | **COVERED as documentation requirement.** Future receipts must actually maintain this separation |

No new blocking design defect was identified within the stated Lane1 deny-only boundary. This is not an endorsement of any implementation that merely uses the R1 terminology without enforcing its requirements.

## 4. Previously identified failure schedules after R1

These are delta checks against the earlier analytical cases, not newly executed attacks:

| Earlier counterexample | How R1 handles it | Limit to retain |
|---|---|---|
| Restore W epoch/signing policy and obtain a fresh signature over old state | Lines20,25–32 classify this as a separate continuity obligation; all-trusted-material recovery unsupported/BLOCKED | Lane1 must not test with a reset oracle and call the result real W anti-rollback |
| Restore a C-only/old verifier or copied actor credential | Lines36–40 require independent manifest admission/quarantine and explicit clone exclusion | Quarantine must prevent authorization on all supported paths, not merely toggle a READY flag that an old guard can ignore. Model admission does not prove real attestation/nonclonability |
| Permit admitted, final check passes, hold disappears, B promotes, A commits late | Lines45–53 require a durable hold until known outcome and bar successor READY/live permits across uncertainty | Oracle restart/transport failure must preserve exclusion or remain unavailable/deny; forgetting OPEN then resuming ownership is a candidate failure |
| Lost COMMIT ACK, missing session, manual signed release | Lines48,57–64 require OPEN_UNKNOWN/FENCED_UNRESOLVED and exclude clearing | Neither session loss, a detached/restored ledger, timeout nor an operator action may silently convert uncertainty into safe ABORT/COMMIT |

The separation between a reserved/revoking next epoch and a live successor is adequate for this contract-level delta review. Reserving a number is not permission to authorize. A late reply or already returned read must not be confused with fresh local admission or a still-possible durable COMMIT.

## 5. Exact recommendation for the three lanes

| Lane | Ready to request Management authorization? | Current execution/security status |
|---|---|---|
| **1 — deny-only integration under explicit W oracle assumptions** | **YES, narrowly and conditionally.** The request can now be scoped without reopening the original design from scratch | **NOT_AUTHORIZED / NOT_RUN.** No W implementation or test was run by this review; no security PASS claimed |
| **2 — real W anti-rollback / custody / own recovery** | **NO acceptance or inferred authorization.** Requires its separate concrete root/custody design, review and evidence | **BLOCKED / NOT_RUN**. Lane1 GREEN cannot discharge it |
| **3 — safe orphan OPEN clearing/reconciliation** | **NO.** Explicitly excluded; later positive outcome/effect and hard-fence proof required | **BLOCKED / NOT_RUN**. No manual or timer escape hatch |

The existing S0-09D same-C-identity rollback remains **FAIL_SECURITY / unresolved**. A future W-enforced test of the same denial invariant must be separately identified. The accepted legacy experiment does not become safe because an oracle path might later pass.

## 6. Conditions the Management vote must preserve

These are the boundaries already required by R1, not a new architecture or permission to start coding:

1. **Name the oracle assumptions.** Current namespace/root/policy identity, consistent monotonic decisions, authenticated responses and durable OPEN/exclusion behavior are assumed within the chosen failure envelope. Keep oracle history outside the C/A/B restore under test. If injected oracle loss cannot retain continuity, deny rather than reinitialize an apparently active authority. A fixture on one CI host does not prove independent infrastructure or real W custody.
2. **State supported restore/actor modes.** The first claim may cover restored C against unchanged trusted W and current admitted guard policy. Any A/B restore coverage must name accepted verifier/manifest versions. Quarantine applies before guarded SQL/issuer/pool access, not only before a readiness display. Physical same-ID clones, real guard attestation and nonclonable credentials remain excluded/BLOCKED unless separately established; stale-actor rejection in an oracle model is not that proof.
3. **Preserve the falsifiable lifecycle.** Observe durable OPEN acknowledgment before authorization; exercise delayed first use, revoke/admit races and holds through positively known local COMMIT/ABORT. Do not CLOSE from a lost ACK or disappearing backend. Test whether successor readiness/live permits remain blocked across each specified crash cut. Prepared work must be explicitly supported and accounted for, or prohibited and checked.
4. **Keep Lane1 deny-only.** OPEN_UNKNOWN never becomes a released/recovered operation. No automatic TTL clearing, manual override, fixture reset as recovery or simulated hard-fence receipt may grant successor authority. Fixture teardown between independent tests must not be described as safe reconciliation.
5. **Keep evidence categories separate.** Retain the legacy129 and original rollback invariant, distinguish legacy and W paths, require fault-present GREEN denial plus intended mutation RED/restoration/GREEN, and report unsupported modes NOT_RUN. No C-only fallback, assertion inversion or CI-success-as-security claim.
6. **Require an explicit scoped authorization.** Management must identify the lane, assumptions, exclusions, regression floor and proof criteria. This reviewer issues no vendor/KMS/consensus/crypto/TTL choice, implementation mission or Production permission. If scope expands into W-root recovery or orphan release, stop that expansion for separate review/authorization.

Failure to preserve one of these limits changes the scope assessed here; the positive Lane1 recommendation does not transfer automatically to the expanded experiment.

## 7. Evidence and validation for this review

| Item | Result |
|---|---|
| Live main and R1 provenance | Verified against29709ad3 and the remote/local blob/digest above |
| PR24 baseline | Exactdda6fea3 remains open, Draft and unmerged; earlier review accepted per management Issue23 comment |
| Four P0, three P1 and one P2 mappings | Covered in this delta report without reclassifying security as proven |
| New W/PgBouncer/database/fault experiments | **NOT_RUN**; no code, SQL, migration or security-test change or execution |
| Document validation | Pinned hashes, references, finding/claim coverage and documentation-only whitespace/diff checks |
| CI | No security CI result claimed. Existing workflow path filters exclude this report; actual run/check status is recorded in the Draft PR/Issue receipt |

No new external technical premise is introduced beyond the accepted review and R1. This mission therefore does not repeat the old literature review, D implementation review or historical CI investigation. Proof of a real W root and safe reconciliation remains absent, explicitly rather than implicitly assumed.

## 8. Handoff to Astra Management

**Recommend considering a separately authorized Lane1-only PoC request.** R1's boundary/lifecycle definition is sufficient for that request, not a demonstrated secure recovery protocol. Lane2 and Lane3 remain BLOCKED / NOT_RUN; all W results are NOT_RUN today. Maintain S0-09D rollback FAIL_SECURITY, SOURCE-001/GATE-SOURCE BLOCKED and Architecture Gate9 OPEN.

This report is submitted in a separate documentation-only Draft PR and registered in Issue23. Earlier PRs11/16/18/20/22/24 remain unchanged, Draft and unmerged. R1 and the accepted PR24 report are not rewritten. No APR-033/034/035/036 change, Production authorization, protocol ratification, historical-source claim or Sprint0 completion. **Implementation may begin only after an explicit Astra Management decision.**
