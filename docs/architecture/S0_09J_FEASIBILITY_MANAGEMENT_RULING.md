# CAC — S0-09J Feasibility Adjudication and Option A Continuity Ruling

**Date:** 2026-11-07  
**Authority:** Astra Management / Security Architecture  
**Execution / research:** [S0-09J Issue #36](https://github.com/alireza-anari/cac-project/issues/36)  
**Architecture parent:** [S0-09I #33](https://github.com/alireza-anari/cac-project/issues/33), [#28](https://github.com/alireza-anari/cac-project/issues/28), [#23](https://github.com/alireza-anari/cac-project/issues/23)  
**Reviewed Draft PR:** [#37](https://github.com/alireza-anari/cac-project/pull/37), exact head `f513aa7ff71d55f964758cd1548520594c5309fd`, base main `d6271a75bc553eb1e047a1d658bacea61706e77d`, OPEN/DRAFT/UNMERGED, one added Markdown file.  
**Primary deliverable:** [S0-09J feasibility R0](https://github.com/alireza-anari/cac-project/blob/f513aa7ff71d55f964758cd1548520594c5309fd/docs/architecture/S0_09J_EXTERNAL_CONTINUITY_FEASIBILITY_R0.md).  
**Previously authorized scope:** [S0-09I R1 review ruling / S0-09J documentation-only authorization](S0_09I_R1_REVIEW_RULING_AND_S0_09J_RESEARCH_AUTHORIZATION.md).  
**Formal Management vote:** `NO_CREDIBLE_E_CANDIDATE_KEEP_A / CURRENT_E1_E2_NOT_QUALIFIED / OPTION_A_UNSUPPORTED_CATASTROPHIC_RESTORE_RETAINED / INDEPENDENT_READ_ONLY_CHALLENGE_REQUIRED / NO_POC_OR_PRODUCTION`.  
**Provenance:** `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`.

## Decision and boundaries

**Accept the study's negative present-qualification finding:** Neither studied E family is currently a defensible *end-to-end CAC authorization-continuity root*. This is **not a proof of universal impossibility** and does not establish that Option A implements automatic global failure denial. Reject implementation requests premised on either current sketch, including counter-only, signature-only, one more restorable quorum, or another assumed oracle.

**Maintain interim Option A** — a coherently responsive restored/rolled-back majority R, simultaneous obsolete verifier/root restore, total-root disaster, and stale-root re-genesis are **UNSUPPORTED** recovery modes. If a surviving independent current, mandatory guard really covers all authorization/data-plane routes, it is required to quarantine and deny unverifiable authority. If a complete root+verifier rewind removes that fact/enforcement, the correct status is `GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED / SECURITY_INCIDENT` (not "automatically fails closed"). Availability may be interrupted indefinitely; this is an admitted cost, **not** a safe recovery protocol.

The **next permitted action** is a separate **independent adversarial READ-ONLY review of S0-09J R0** and its negative reasoning, before final closure of research Issue #36. Do not create an E implementation or new test mission from this review; subsequent physical/custody research or a candidate PoC requires an explicit new Management vote and proof that at least G1 and G4 are credibly instantiated. A failed research candidate should be rejected without escalating G2/G3/G5 to false PASS.

## Independent assessment of E1 and E2

| Family | Genuine technical interest | Current disqualifying gaps | Decision |
|---|---|---|---|
| **E1 — separately administered authenticated current-head service** | Can express legal authority transitions, ordered journal, authenticated ancestry, idempotency and freshness *within a surviving trustworthy service*. | No concrete final nonrollback fact when E itself and its signer/administrators are restored; independently enforceable current verifier/SQL/issuer/pool admission absent. RFC log consistency or fresh signed service reply does not prove most recent CAC state. | `NOT_QUALIFIED` (G1, G4 fail) |
| **E2 — protected monotonic hardware-like root + complete external journal** | Published TPM monotonic NV-counter characteristics are meaningful for some reset/restore envelopes; must not inaccurately claim normal same-Name deletion simply resets a counter. | No approved/qualified physical instance and reset/replace/custody story; a monotonic integer is not atomic authenticated legal CAC state, available OPEN bodies or PG outcome, and old verifiers can bypass it. | `NOT_QUALIFIED` (G1, G4 and compound G2/G3 fail) |

Both remain *unselected research families*, not authorized products. No vendor, device, KMS/HSM, cryptographic scheme, transaction manager or operational topology is approved.

## Five persistent P0 stop gates

1. **G1 terminal root / latest-head continuity `DESIGN_BLOCKED`:** name exact surviving irreversibility fact, E's **own** snapshot/reset/restore/backup/key/firmware/member/replacement limits, sign/admission policy, privileged custodian and current verifier. A new root ID is not freshness proof.
2. **G2 complete OPEN/UNKNOWN obligations `DESIGN_BLOCKED`:** a current commitment can **detect-and-deny** without supplying complete authenticated journal bodies, suffixes, policy/tombstones or exact old transaction identities. Reconstruction is a separate capability; even fully reconstructed UNKNOWN still blocks successor. No "missing body means no OPEN".
3. **G3 R/E/PostgreSQL atomicity `DESIGN_BLOCKED`:** one legally valid grant/revoke order, durable OPEN-before-usable-permit, exact first use and local COMMIT/ABORT proof, root CLOSE and ACK-loss status semantics have not been solved by a counter increment or two linearizable reads. A previously admitted old transaction may finish while successor stays NOT_READY. A lost ACK cannot be promoted to an inferred outcome.
4. **G4 all-route independent mandatory guard `DESIGN_BLOCKED`:** old SQL/issuer/RLS, SECURITY DEFINER, direct DB roles, maintenance sockets, PgBouncer existing backends, pre-E verifier, old signer and active/prepared transactions must be accounted for. If restored code/credentials can operate without current E admission, global denial is not established. Blocking new connections alone does not prove an incumbent COMMIT cannot complete.
5. **G5 protected-resource continuity `DESIGN_BLOCKED`:** new root, namespace, device, key, actor, DB or cluster IDs cannot forget predecessor obligations affecting the same resource. No operator sign-off, hard fence, timeout or brand-new genesis can turn a truly unresolved OPEN into CLOSED.

Three P1 obligations (independently verifiable quarantine/incident triggers, PG outcome-observer and privileged custody, qualitative to measured economics/availability) and P2 immutable version/status provenance remain. The report's **14 adversarial schedules are theoretical and all NOT_RUN**. They do not count as green tests, proof of an exploit, or actual catastrophe recovery. S0-09J's PR has **0 final-head GitHub workflow runs** based on the verified queried endpoint, and no new active security test is claimed.

## Falsifiability and review gate

Request an **independent security architect** who did not draft the candidate report to review its exact-source claims and challenge:
- Whether rejecting current E1/E2 is justified without misrepresenting any TPM NV-counter lifetime, attestation or privileged Clear semantics;
- Whether an overlooked **bounded and enforceable** alternative genuinely meets G1+G4 under clearly separate admin/backup/trust custody; distinguish this from a recursively assumed root;
- Whether the latest-head **and** complete available OPEN/UNKNOWN are required, and whether G3's research invariants actually account for atomic grant/revoke/local effects and all 14 modeled cuts;
- Whether restored SQL/issuer/verifier/pools or active sessions can bypass "independent" E, and whether asserted global quarantine is conditioned on real enforcement;
- Whether rejection of current qualification is appropriately narrower than universal technical impossibility, with availability/cost implications and sound provenance.

**Review deliverable:** `docs/security/S0_09J_FEASIBILITY_INDEPENDENT_READ_ONLY_REVIEW.md`, a **separate docs-only Draft PR targeting latest main**, with pin of exact J head `f513aa7ff71d55f964758cd1548520594c5309fd`, base/current main SHA, one of:
- `NEGATIVE_QUALIFICATION_DEFENSIBLE_KEEP_A`;
- `TARGETED_FEASIBILITY_CORRECTION_REQUIRED`;
- `NEGATIVE_VERDICT_NOT_SUPPORTED`.

Post read-only review/PR receipt and P0/P1/P2 to Issue #36 and #33. **No PoC, CI, code, SQL, workflow, mutation, infrastructure, credential/key action, merge or Production approved.** After independent review Management may close #36 **only as a completed feasibility study**, not as closure of E's five P0 vulnerabilities. Avoid another repeated design-review loop without a named real primitive and full-route authority model.

## Historical evidence and governance unchanged

- S0-09D original C-anchor epoch2→1 rollback remains **`FAIL_SECURITY`**, not repaired by E research or H conditional success.
- S0-09H proof remains limited to a current **non-restored** 3/5 etcd majority and trusted lab guard/PG observer. Previously **169 inherited +51 new H =220 distinct security/DB tests in separate suites, plus 2 artifact-only methods**; no S0-09J runtime tests.
- Root **policy retirement** and literal stale Raft WAL/snapshot import remain **`NOT_RUN`** (signer retirement or new learner replacement are not equivalent).
- Lane3 orphan `OPEN_UNKNOWN/FENCED_UNRESOLVED` clearing remains **P0 BLOCKED/NOT_RUN**, potentially indefinitely safe downtime.
- R-majority rollback/catastrophe, independent admin/physical/backup/key custody, cloned identity, joint restored verifier and R/E/PG authority integrity remain `P0 SECURITY_UNPROVEN / NOT_RUN`.
- [Architecture Issue #33](https://github.com/alireza-anari/cac-project/issues/33) / [#28](https://github.com/alireza-anari/cac-project/issues/28) / [#23](https://github.com/alireza-anari/cac-project/issues/23), [baseline Gate #9](https://github.com/alireza-anari/cac-project/issues/9) **OPEN**, [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) / GATE-SOURCE **BLOCKED**; all prior experimental/docs Draft PRs including #37 remain OPEN/DRAFT/UNMERGED. `NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`, no original recovered CAC baseline, APR-033..036, Production, full protocol, identity/onboarding, Sprint0 or Merge approval.


## Final independent S0-09J review disposition — 2026-11-07

**Independent review:** [S0-09J read-only security assessment](https://github.com/alireza-anari/cac-project/blob/8948d76aa2e664669bac45731686729ac7944296/docs/security/S0_09J_FEASIBILITY_INDEPENDENT_READ_ONLY_REVIEW.md) in [Draft PR #38](https://github.com/alireza-anari/cac-project/pull/38) at `8948d76aa2e664669bac45731686729ac7944296`, targeting `main` at `0f5bc81d372c90788a30cbfa5e65e322b17e4f86`. The review added one Markdown file; **no code, SQL, CI, experiments or PoC**. Review independence is separate-agent role separation, **not external organizational or hardware certification**.

**Final Manager vote:** `NEGATIVE_QUALIFICATION_DEFENSIBLE_KEEP_A / S0_09J_RESEARCH_COMPLETED_ONLY / E_G1_G5_DESIGN_BLOCKED / NO_NEW_ACTIVE_WORK`. The independent reviewer confirms that **current end-to-end** E1/E2 qualification fails. Do **not** convert that finding into universal impossibility: an actually separately governed, surviving E with mandatory independently enforced effect-path control could expand protection from R-minority failures to R-majority catastrophe under a **finite bounded E-survival assumption**. It need not be indestructible under *every conceivable threat*; its actual supported restoration and reset envelope must be specified and proven. Equally, a generic HSM label, counter, new recoverable DB or additional assumed oracle is not itself a credible complete CAC protection mechanism.

**P0 disposition:** G1 terminal independently surviving current-authority state / E custody and reset; G2 available authenticated full pending OPEN/UNKNOWN bodies; G3 legally ordered R/E/PG OPEN/grant/revoke/durable outcome/CLOSE with ACK loss; G4 current mandatory guard across all restored and incumbent issuer/SQL/RLS/PgBouncer/privileged routes; G5 same-protected-resource predecessor obligations across root/actor/namespace replacement — **ALL FIVE REMAIN `DESIGN_BLOCKED / SECURITY_UNPROVEN / NOT_RUN`**. The independent reviewer examined all **14 hypothetical cuts individually**, all **NOT_RUN**, with relevant caveats about legitimate pre-revoke grants, exact originally CLOSED ACK lookups and truly unresolved OPEN_UNKNOWN. Three P1 risks continue: actual incident/quarantine evidence, trusted PG observer and privilege/custody, and operating-cost/availability measurements.

**P2 source ledger corrections acknowledged:** alongside the published TPM Library v185 documents, any future use of the S0-09J source ledger should refer to [TPM v185 Errata Version 1](https://medias.cdn.trustedcomputinggroup.org/production/Eratta_Trusted_Platform_Module_2_0_Library_Version_185_pub_17260f83c0.pdf) (2026-03-12; nonnormative until incorporated), and correct TPM Part 2 §10.11.8 NV certification structure to **printed p.161**, rather than p.160. The errata's NV certification caveats do not reverse the lifetime monotonic-counter property; they also do not prove CAC's legal transitions, complete journal or all-route enforcement. Do not modify unmerged PR #37 to silently rewrite the reviewed source.

**Governance / next action:** [Issue #36](https://github.com/alireza-anari/cac-project/issues/36) may close **only as completed bounded documentation feasibility and independent read-only review**. Keep [#33](https://github.com/alireza-anari/cac-project/issues/33), [#28](https://github.com/alireza-anari/cac-project/issues/28), [#23](https://github.com/alireza-anari/cac-project/issues/23) and baseline [#9](https://github.com/alireza-anari/cac-project/issues/9) **OPEN**; SOURCE-001 [#1](https://github.com/alireza-anari/cac-project/issues/1) / GATE-SOURCE BLOCKED. Keep PR #37, #38 and all predecessor Draft PRs unmerged. Archive E1/E2 as not currently qualified **without commissioning another generic E design/review loop**. Reopen E research only upon a **concrete independently sourced terminal/custody and mandatory route-control dossier** meeting G1+G4 and a new separate Management authorization; that alone would not close G2/G3/G5.

S0-09D original rollback remains **FAIL_SECURITY**, S0-09H evidence bounded to non-restored current 3-of-5 majority, root **policy retirement** and literal old Raft snapshot/WAL import still **NOT_RUN**, Lane3 orphan `OPEN_UNKNOWN` resolution **P0 BLOCKED**. If root/verifier are jointly restored and all trustworthy enforcement lost, `GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED`. `CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL / PROTOCOL_PROPOSED`; no Production, recovered baseline, APR033–036, onboarding, full recovery protocol, Sprint0, implementation, PoC or merge permission.
