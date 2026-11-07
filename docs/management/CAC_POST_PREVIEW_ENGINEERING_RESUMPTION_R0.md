# CAC — Management Ruling: Resume Detailed Engineering After Preview Visibility Checkpoint

**Date:** 2026-11-07  
**Authority:** Astra Management, reflecting explicit Product Owner clarification  
**Current main at decision start:** `f9f465c3387833d44e537c163c9dacff75e352ac`  
**Status:** `PREVIEW_VISIBILITY_OBJECTIVE_MET / DETAILED_ENGINEERING_RESUMED / OWNER_FEEDBACK_NO_LONGER_GLOBAL_BLOCKER / PRODUCTION_GATES_UNCHANGED`  
**New bounded mission:** [S0-09K Issue #45](https://github.com/alireza-anari/cac-project/issues/45)  
**Existing Preview delivery:** [Issue #43](https://github.com/alireza-anari/cac-project/issues/43) / [Draft PR #44](https://github.com/alireza-anari/cac-project/pull/44) head `8b99a9c6db7f9b88278aca3f967dc1b1ecb56639`; [parent #42](https://github.com/alireza-anari/cac-project/issues/42).

## 1. Owner clarification and what changes

The owner says the Preview was requested **to see the project**, and requests a return to the previous **detailed architecture / development / test / security review / management acceptance** workflow.

Accordingly, revise the sequencing **without revoking the useful delivered Preview**:

- **Keep** the actual runnable local Preview V0 as a traceable optional owner-visibility checkpoint, not a public or Production product. Source and ZIP are independent new-origin experimental artifacts, not recovered v3.37–39 baseline. The current Preview's owner-local manual browser/mobile/keyboard trial and screenshots remain `NOT_RUN` until actually observed. The delivered ZIP hash was reported by Work, but Management has not independently rehashed the private Library bytes.
- **Remove** the previous global stop on *all* feature/security engineering pending top-three product feedback. The owner does **not** need to install/accept the Preview before independent, safety-bounded engineering continues. If the owner later shares UI feedback, address it as a separately scoped product workstream. No invented product acceptance is implied.
- **Do not** automatically expand PV0-02, implement real AI/Woo/Live or merge Preview code without a separate owner/product-scope decision. Keep [#43](https://github.com/alireza-anari/cac-project/issues/43) OPEN as `TECHNICAL_HANDOFF_COMPLETED / OWNER_VISUAL_TRIAL_OPTIONAL_PENDING` until a distinct explicit closure decision; [#42](https://github.com/alireza-anari/cac-project/issues/42) remains an OPEN product lane, not the sole prerequisite for security work.
- Resume the former division of labor: Astra Management prioritizes/rules/checks; Astra Development / Work implements bounded tests, Draft branches and evidence; security reviewers check actual source/fault windows; Management issues scope-specific rulings. Prefer **one meaningful executable evidence slice** over repeated docs-only design cycles when no new fact can be proven.

This decision is a refinement of [Preview-first product strategy](CAC_PREVIEW_V0_PREVIEW_FIRST_DECISION_R0.md): its initial usable-product milestone has been technically delivered, while the Product Owner explicitly removed **feedback as an absolute dependency for unrelated engineering**. The Preview-first strategy may still guide future UX increments, but it **does not block P0 security work**.

## 2. Current evidence snapshot

- [PR #44](https://github.com/alireza-anari/cac-project/pull/44) is OPEN/DRAFT/UNMERGED at `8b99a9c6db7f9b88278aca3f967dc1b1ecb56639`, based on `f9f465c3387833d44e537c163c9dacff75e352ac`, changes only 51 `preview_v0/` files. Its evidence reports 17 Django tests PASS and successful cold ZIP extraction, new local secrets/DB/login, loopback HTTP product+assistant+rules-based chat and restart/persistence. [Management PR #44 review](https://github.com/alireza-anari/cac-project/pull/44#pullrequestreview-5814697935) accepted only `READY_FOR_OWNER_LOCAL_TRIAL` technical handoff, **not actual browser/owner acceptance**; browser/mobile/keyboard/Windows/macOS remain `NOT_RUN`.
- [S0-09H PR #32](https://github.com/alireza-anari/cac-project/pull/32) OPEN/DRAFT/UNMERGED at `b32416c799160f0e5957506d58254a693cbc231f`, stacked on PR #27. Actual surviving non-restored 3/5 etcd R majority + real PG/PgBouncer test evidence: 51 H distinct tests +169 inherited across separate suites, 2 artifact scanner tests, 5 mutation RED/restored GREEN probes. **S0-09D original C-only rollback FAIL_SECURITY** remains unchanged.
- [S0-09J research #36](https://github.com/alireza-anari/cac-project/issues/36) closed for completed negative feasibility review **only**: neither E1 nor E2 qualifies today. No new E root has been selected; G1–G5 remain `DESIGN_BLOCKED`. Root majority rollback and jointly restored obsolete verifier remain `UNSUPPORTED`, with `GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED` where all independent control planes rewind. Lane3 orphan `OPEN_UNKNOWN` clearing P0 blocked.
- [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) / GATE-SOURCE **BLOCKED**; [Gate #9](https://github.com/alireza-anari/cac-project/issues/9) OPEN; [#23](https://github.com/alireza-anari/cac-project/issues/23), [#28](https://github.com/alireza-anari/cac-project/issues/28), [#33](https://github.com/alireza-anari/cac-project/issues/33) OPEN. Existing 17 open PRs, including #32 and #44, were Draft/unmerged when checked at the start of this decision. No merge authorized.

## 3. Next prioritized executable security slice

**S0-09K: real root policy retirement under the current healthy/non-restored majority R premise.**

Why: H actually exercised signer retirement, but `state['policy']=1` mismatch negatives are **not** an actual policy retirement transition. The remaining proof is high-signal, measurable and bounded to the already real etcd/PostgreSQL/PgBouncer fixture without inventing an unqualified E. The objective is to implement and adversarially test a real authenticated policy-generation transition and mandatory current guard/SQL denial of old-policy **new** operations, while continuing to permit known historical pre-revoke in-flight transaction outcomes without admitting a new successor too soon.

**Work authority:** [S0-09K Issue #45](https://github.com/alireza-anari/cac-project/issues/45) authorizes a narrow **`NEW_IMPLEMENTATION_EXPERIMENTAL`** branch based on the exact H PR #32 head (not on main's product code), with a **new stacked Draft PR** against the H experimental branch, real root/PG/guard tests, negative mutation witness, inherited regression gates, immutable receipts, and independent read-only source review. No modifications or merges of Preview, H, main product/backend, or earlier experiments.

**Stop on security failure:** Report `K_SUPPORTED_SECURITY_FAIL` for any supported stale-policy authorization that survives current guard/SQL and do not suppress assertions. If true retirement would require a fictional oracle or defeat the supported trust model, report `K_BLOCKED_NOT_RUN`, not an invented PASS. H's independent full-root majority rollback proof, actual old Raft WAL/snapshot import and Lane3 remain outside K and are not inherited as completed.

**Next after K:** Management reviews real measured evidence and independently decides either an additional sharply scoped stale-Raft-snapshot admission/rejection experiment **under non-restored majority**, recovery contract correction, or a different source/security priority. **No automatic S0-09L**.

## 4. Preview lane now and feedback policy

- Keep [#42](https://github.com/alireza-anari/cac-project/issues/42)/[#43](https://github.com/alireza-anari/cac-project/issues/43) as archived/in-progress product workstream with an **optional** hands-on trial. No requirement that owner state three changes **before unrelated Work security missions**.
- Owner feedback can inform subsequent PV0-02 UX/business decisions, but no unapproved new PV0-02, public Live, AI provider, data ingestion, or deployment is authorized by this ruling.
- Source ZIP/README remain available in the existing Library and GitHub links; don't repackage or claim new delivery without actually doing it.

## 5. Hard boundaries

A completed local Preview or a successful H/K test is **not** a Production, canonical baseline, true public Live, identity/onboarding, real tenant PostgreSQL/RLS, physical root catastrophe, E G1–G5 or orphan recovery approval. Original APR-033/034/035/036 unchanged. No recovered v3.37/38/39 source, no Sprint0 completion, no Merge, no remote deployment, no real customer/merchant data.

**Management decision:** `RETURN_TO_DETAILED_ENGINEERING / SECURITY_K_EXECUTION_AUTHORIZED_WITHIN_SURVIVING_Q / PRODUCT_OWNER_FEEDBACK_OPTIONAL / ALL_PRODUCTION_GATES_STILL_OPEN`.
