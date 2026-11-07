# CAC — S0-10 R0 | Parallel Product Delivery and Security-Gated Readiness Plan

**Management decision date:** 2026-11-07  
**Owner:** Astra Management / Product & Security Architecture  
**Status:** `ROADMAP_REPRIORITIZED / DESIGN_ONLY_S0_10A_AUTHORIZED / SECURITY_GATES_UNCHANGED / NO_PRODUCT_IMPLEMENTATION_OR_PRODUCTION`  
**Execution first slice:** [S0-10A Merchant UX contract Issue #39](https://github.com/alireza-anari/cac-project/issues/39)  
**Source classification:** `CAC-NEW-ORIGIN-S0-07 / SOURCE_UNVERIFIED / PROTOCOL_PROPOSED`  
**Scope:** management coordination, contract and UX documentation. Does not ratify an APR, approve Merge, exercise a root/PoC, change data-plane security, or clear any release gate.

## 1. Why move the roadmap now

The bounded S0-09H tests used real PostgreSQL/PgBouncer and a five-member etcd cluster **on one CI host** and produced useful `Q_SURVIVAL_INTEGRATION_EVIDENCE_UNDER_NONRESTORED_MAJORITY`: 169 inherited +51 H =220 distinct security/DB tests **across separate suites**, plus two artifact-only methods and five sensitivity controls. The original S0-09D C-anchor epoch rollback `FAIL_SECURITY` remains real and separate.

After S0-09I/J, [S0-09J final ruling](../architecture/S0_09J_FEASIBILITY_MANAGEMENT_RULING.md) and independent [Draft PR #38](https://github.com/alireza-anari/cac-project/pull/38) support a **negative current E1/E2 qualification**, not universal impossibility. Five P0 G1–G5 are `DESIGN_BLOCKED` and a coherent R-majority catastrophe/joint obsolete-verifier restore is **UNSUPPORTED**. Safe global denial is **NOT ESTABLISHED** if every independent guard/root is restored. [Research Issue #36](https://github.com/alireza-anari/cac-project/issues/36) closed **as documentation completed only**. Additional speculative E PoCs would repeat an unqualified assumption; no new E implementation is authorized.

Simultaneously, source and product readiness remain blocked: [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) lacks verifiable original v3.37/38/39 bytes; [ARCH-BASELINE #9](https://github.com/alireza-anari/cac-project/issues/9) stays OPEN. Prior experiments on unmerged Draft PRs are **not a canonical product backend or permission to expose Live**.

**Management decision:** stop launching generic E design loops; deliver tangible **merchant UX and contract-readiness documents in parallel** while the source recovery and security threads remain explicitly gated. This separates useful product definition from unproved runtime authorization.

## 2. Existing product basis — preserve, do not silently amend

Reference: [CAC product V1](../cac/01_PRODUCT_V1_AND_USER_EXPERIENCE.fa.md), [architecture decisions](../cac/02_APPROVALS_AND_ARCHITECTURE_GOVERNANCE.fa.md), [security gates](../cac/03_SECURITY_DATA_CONTRACTS_AND_RELEASE_GATES.fa.md), [backlog](../cac/05_EXECUTION_BACKLOG_AND_PRIORITY.fa.md), [MVP S0–S6 roadmap](../MVP_ROADMAP.md).

**Approved/preserved product constraints:**
- SaaS for WooCommerce merchants; simple self-serve setup, *four* navigation sections: **Overview, Conversations, Assistant Information, Settings**. A merchant should not need to understand provider tokens/usage billing; simple monthly subscription packaging, no invented prices.
- `APR-033`: one verified, owner-attested qualifying contact is necessary before *public* Live.
- `APR-034`: **at most one** public Live assistant per Store in V1, but future-extensible Store/Assistant relationships.
- `APR-035`: confirmed loss of final qualifying contact pauses public service, preserves private Preview; a transient probe outage by itself cannot trigger Pause.
- `APR-036`: v3.37 architecture freeze still governs; v3.42 is a **reference document bundle**, not recovered executable source or a new Freeze.
- Honest merchant lifecycle: **Private Preview → owner confirmation → install → verify → Live**, with no automatic public activation; verified domain and readiness/security/privacy approvals required.
- Woo reads **public products and variants only** (no orders, customer, payment or private account data). Recorded freshness: product price maximum 30 minutes, stock maximum 10 minutes; a heartbeat alone is not a data-observation timestamp.
- Approved/reviewed knowledge before publishing; sensitive knowledge needs two independent reviewers; safe URL/file ingestion without SSRF or unapproved AI egress.
- Visitor separation, iframe origin/source/nonce/epoch checks, visit-specific transcripts; target raw-message visibility retention 30 days after **last real message** and no API access after expiry, even before physical purge.
- No V1 order processing, autonomous administration, live-agent SLA, sales-dependent payment logic or unsupported AI provider data processing.

**Identity, sessions, issuer/challenge, key custody, internal APIs, backend state enums, schemas, exact error status codes, real billing prices and provider selections are NOT automatically approved** by listing desired screens. Relevant S0-08 direction is `DESIGN_RECORDED / CONDITIONAL_DIRECTION / NOT_BASELINE_ACCEPTED`; [CR-S0-05-001 #7](https://github.com/alireza-anari/cac-project/issues/7) remains OPEN for invitation errors and cannot be decided against missing backend source.

## 3. Prioritized streams and independence rules

| Stream | Immediate permitted work | Owner / deliverable | Absolute block / transition |
|---|---|---|---|
| **A — Authentic source and integration gate** (P0, ongoing) | Curate actual historical v3.37/v3.38/v3.39 source **if it appears**, SHA/provenance, diffs, migration compatibility, reproducible build evidence. No speculative reconstruction. | Management/source custodian; [#1](https://github.com/alireza-anari/cac-project/issues/1), [#9](https://github.com/alireza-anari/cac-project/issues/9). | GATE-SOURCE stays BLOCKED until authentic evidence and explicit separate acceptance. New-origin code does not satisfy it. |
| **B — Security architecture and experimental trust boundary** (P0, parked unless new evidence) | Maintain archived D FAIL_SECURITY, H bounded tests, I/J negative E qualification and Lane3 deny controls. Reactivate E research **only with concrete G1+G4 fact/custody/enforcement dossier and new explicit Management authorization**. | Security Architecture; [#33](https://github.com/alireza-anari/cac-project/issues/33), [#28](https://github.com/alireza-anari/cac-project/issues/28), [#23](https://github.com/alireza-anari/cac-project/issues/23). | No root-majority restore, clone/old-verifier safety, orphan CLEAR, Product Live, runtime PoC or Production proof inferred. |
| **C — Merchant UX and assistant lifecycle** (P1, **FIRST NEW WORK**) | Four-screen information architecture, onboarding and private Preview, readiness/copy/CTA, owner-confirmed Live journey, Pause, merchant errors and accessibility. UI contract **documentation only** with synthetic states. | Astra Product / Work via [S0-10A #39](https://github.com/alireza-anari/cac-project/issues/39). | **NO** real Django/backend, login, Woo connector, AI calls, public widget or live activation. All backend state/action names PROPOSED. |
| **D — WooCommerce public catalog contract** (P1 next candidate) | Design-only signed pairing, public-only product/variation projection, price/stock actual freshness, reconciliation, subscription to events and failure UX. | Future separately approved S0-10B **design** task, not yet authorized. | No Woo plugin or external API connection; no private order/customer/payment access. |
| **E — Knowledge, AI, widget and subscription UX** (P1/P2 later) | Documentation for source review workflow, privacy and retention, isolated conversations, capability-tier packaging and owner approvals. | Future separate design tasks after C review. | No provider selection/egress, public visitor endpoint, real billing integration, customer content or spend. |
| **F — Canonical implementation and release** (blocked) | None presently approved by S0-10. Decide only after authentic source/selected new-baseline Architecture signoff, approved API/security contracts and reproducible real PostgreSQL/IdP/onboarding evidence. | Separate Management + Architecture gate. | No silent use/merge of Draft experimental PRs as production backend, no Sprint0 complete or Production. |

**Parallelization rule:** C may advance at the requirements/wireframe/documentation layer while A/B remain blocked. D/E may be designed later with separate scope decisions. No UI may interpret a successful design review or optimistic backend mock as evidence that real security, Live, sessions, provider processing or data retention has passed.

## 4. Actual priority and next tangible deliverable (S0-10A)

**Choose merchant first-run experience, not more generic security research, as the first visible product design slice.** [Execution Issue #39](https://github.com/alireza-anari/cac-project/issues/39) is authorized **docs only** and demands:

- Persian/RTL-capable, mobile-friendly IA of Overview, Conversations, Assistant Information and Settings, beginner-friendly "next step" descriptions and a transparent status/progress sequence.
- State/copy contract: `DRAFT / PRIVATE_PREVIEW / READY_PENDING_VERIFICATION / LIVE / PAUSED / RECOVERY_REQUIRED` as **proposed UI labels** only; enforce approved product rules but no claim actual backend enum/API.
- Owner onboarding walkthrough for verified identity, Woo read-only pairing, domain/widget, minimum owner-attested verified contact, reviewed knowledge, privacy/provider approval, owner confirmation and verified Live readiness. **No direct public activation on unchecked local mock values.**
- UI readiness truth table: a missing/stale item is never green; denote approved backend gate evidence versus an unavailable/unknown check, safe denials/incident state and appropriate call-to-action.
- 6–10 distinct **DESIGNED / NOT_RUN** merchant journey cases: successful private Preview, missing final contact, temporary probe issue, confirmed contact loss/automatic Pause, competing Live assistants, failed widget installation, missing content/provider approval, tenant/permission denial, no current root, and 30-day conversation expiry.
- Trace every proposed screen element to existing APR/docs or an explicit CR-required decision and relevant release gate; no invention of source interfaces or “prototype passed” claims.

**Expected output:** `docs/product/S0_10A_MERCHANT_UX_ASSISTANT_LIFECYCLE_R0.fa.md` in a separate **docs-only Draft PR targeting current main**, with peer review, SHA and Issue #39 handoff. The resulting positive design review can recommend an **isolated visual/static mock** in a *later* specifically authorized mission; it cannot authorize real code, an endpoint or Production.

## 5. Gate and evidence matrix for any future step

| Milestone | Evidence to ask from Work / other responsible owner | State today and implications |
|---|---|---|
| Source identity / baseline | Authenticated original source hashes + diff/compatibility or explicit *separate* new-origin canonical-baseline ruling and security approvals | `SOURCE-001 BLOCKED`, [#9](https://github.com/alireza-anari/cac-project/issues/9) OPEN, not resolved by S0-09H tests |
| PostgreSQL / tenancy | Reproducible migration graph; RLS/composite FK and least-privilege actor tests at full final SHA, including P0 rollback and pool paths | Experimental bounded H evidence `OBSERVED`, broad product integration `BLOCKED` |
| Identity / onboarding | Trusted identity/MFA/CSRF, current owner contact attestation, revocation/provisioner/audit/outbox and real app/DB tests with approved key/role policy | `NOT INTEGRATED / PROPOSED / BLOCKED`; do not promise actual Live |
| Merchant UX contract | APR-linked screen/readiness and realistic blocked/waiting states; independent docs review, accessible merchant copy | S0-10A newly `AUTHORIZED_DESIGN_ONLY`, not implemented |
| Woo / knowledge / AI | Real signed public catalog data/freshness/reconciliation and privacy/provider review, scoped retrieval and approvals | `NOT_RUN / NOT_AUTHORIZED_FOR_LIVE` |
| Widget / retention / billing | Isolated visit and public widget with actual domain/security tests, 30-day API expiry + purge/backup, owner-agreed subscription contract | `NOT_RUN / NOT_AUTHORIZED_FOR_LIVE` |
| Overall root/recovery/security | An accepted architecture covering relevant restore and verifier paths plus independently evidenced controls, or explicit ***supported*** restricted deployment envelope approved by owner/security | Root catastrophe and Lane3 remain P0 blocked. No Product Production approval or supported global fail-closed guarantee. |

No implicit numerical release date, vendor, tier price, performance target, cost estimate, SLA, success rate or owner signoff is made by this planning document.

## 6. Product and security risk register

| Risk | Severity | Requirement / stop rule |
|---|---|---|
| A visual "Live" toggle implies a safe public backend even though Source, RLS, root continuity or provider approvals are unknown | P0 | In design-only work, show demo labels only and mark unavailable actions as BLOCKED. Real public activation never inferred from frontend state. |
| Owner contact erroneously marked verified by a self-checked box or temporary probe | P0 | Distinguish owner attestation + validated qualifying contact from a form field; confirm final contact loss before Pause; transient outage alone does not Pause. |
| PR #32 H success or S0-09J research closure mislabeled as canonical/Production security | P0 | Keep historical D FAIL_SECURITY, root-majority P0/OPEN_UNKNOWN Lane3 BLOCKED, #9 OPEN, Source blocked and all experiments Draft/unmerged. |
| Raw messages/customer Woo private data or API credentials shown in design/evidence or sent to an unapproved provider | P0 | Synthetic text-only examples; Woo public catalog only; no real secrets, private history or provider egress. |
| UX doc redefines auth/session/API route/status/retention/Live invariant without CR | P1 | Traceability and explicit PROPOSED/CR_REQUIRED label; Architecture review before any final contract. |
| Project stalls in repeated E-only document loops without genuine terminal root/guard evidence | P1 | No new E generic mission absent G1+G4 feasibility dossier + separate Management approval; prioritize C design while security remains fenced. |
| Unbounded product scope or misleading cost estimates | P2 | Keep V1 four-section IA and simple monthly packages; no complex token metering, no fictional pricing or commitments. |

## 7. Immediate Management checkpoints

1. Establish [S0-10A Issue #39](https://github.com/alireza-anari/cac-project/issues/39) with a **clear docs-only Work brief** and a Draft PR requirement; **no runtime code or real integration** is authorized.
2. Continue [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1) as independently BLOCKED, with no source reconstruction masquerading as recovery. Do not silently rename unmerged experimental PRs as an accepted backend.
3. Freeze further speculative E design/PoCs pending *actual* terminal latest-head and independently mandatory guard G1+G4 evidence. [S0-09J #36](https://github.com/alireza-anari/cac-project/issues/36) is closed **only** as research delivery; #33/#28/#23 open.
4. After S0-10A docs plus review are delivered, Management chooses between a **bounded static frontend/wireframe-only design** (if safe and separately authorized), a Woo public-catalog contract study, or required source/identity/security contract clarification. **No automatic coding permission** follows a UX approval.

**Current enforced gates:** [#9](https://github.com/alireza-anari/cac-project/issues/9) OPEN; [#1](https://github.com/alireza-anari/cac-project/issues/1)/GATE-SOURCE BLOCKED; root-majority rollback/joint obsolete-verifier restoration UNSUPPORTED with `GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED` when no current guard; S0-09D legacy C rollback `FAIL_SECURITY`; Lane3 orphan `OPEN_UNKNOWN` clearing P0 BLOCKED/NOT_RUN; root policy retirement and literal stale Raft snapshot import NOT_RUN. Previous experimental/review Draft PRs including #37/#38 remain UNMERGED.

**Decision:** `S0-10_PARALLEL_DESIGN_READINESS_APPROVED / S0-10A_DOCS_ONLY / SOURCE_AND_SECURITY_BLOCKERS_RETAINED / NO_MERGE / NO_PRODUCT_PRODUCTION`.


## Product owner supersession — Preview-First executable V0 is the active delivery path (2026-11-07)

The above S0-10 design-only prioritization was appropriate when product UX existed only as a contract. The product owner has now **explicitly replaced** it with a new priority: an actual runnable, local and synthetic CAC Preview V0 before further heavy product-engineering/hardening. **Current governing decision:** [CAC Preview V0 Preview-First R0](CAC_PREVIEW_V0_PREVIEW_FIRST_DECISION_R0.md), [Management Issue #42](https://github.com/alireza-anari/cac-project/issues/42), [PV0-01 execution #43](https://github.com/alireza-anari/cac-project/issues/43).

**Immediate executable slice:** independent `preview_v0/` Python 3.12 + Django 5.2 LTS (pin Work-tested security patch) + SQLite local-only seller application: demo owner login, create/edit sample Store, products/services CRUD, private one-assistant/Store configuration, **interactive rules-based Demo chat grounded in locally saved products**, actual local state persistence, clean ZIP and manual owner walkthrough. It must remain localhost-only with no external calls at runtime, data/secret shipments, real users, Woo/AI providers or public Live. After working artifact handoff, **get owner feedback before expanding PV0-02**.

This **separately authorizes local Preview development code**, overriding the earlier static-only mock priority of superseded [#41](https://github.com/alireza-anari/cac-project/issues/41) without silently changing the previous scope or treating the original UX Draft PR #40 as implemented software. Source #1/GATE-SOURCE, canonical #9, root #33/#28/#23, original D FAIL_SECURITY, E G1–G5, and orphan OPEN_UNKNOWN Lane3 remain unchanged. Local functional preview cannot be promoted to a production source baseline or security acceptance.
