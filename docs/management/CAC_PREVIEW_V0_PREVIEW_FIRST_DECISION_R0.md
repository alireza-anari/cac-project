# CAC — Preview-First Product Delivery Decision R0

**Decision date:** 2026-11-07  
**Authority:** Astra Management / Product Owner directive  
**Priority:** P0 — PRODUCT DELIVERY  
**Decision:** `PREVIEW_FIRST_ADOPTED / LOCAL_USABLE_PV0_01_AUTHORIZED / PRODUCT_FEEDBACK_GATE / PRODUCTION_SECURITY_UNCHANGED`  
**Parent issue:** [CAC Preview V0 #42](https://github.com/alireza-anari/cac-project/issues/42)  
**First execution:** [PV0-01 #43](https://github.com/alireza-anari/cac-project/issues/43)  
**Previous static-only mock:** [S0-10A-M1 #41](https://github.com/alireza-anari/cac-project/issues/41) — **SUPERSEDED**, separate local-static permission does not constrain the explicitly approved local PV0-01 code scope.  
**Reference UX:** [S0-10A Draft PR #40](https://github.com/alireza-anari/cac-project/pull/40) at `971bcaab79b7e249866b948243ef881cecf7045a`, reviewed only as UX design.  
**Previously verified main before this decision:** `cacdee59fbd9b53e754e8a4c95b274e18ce6e8fb`.  
**Provenance:** `CAC-NEW-ORIGIN-S0-07 / PREVIEW_V0_NEW_ORIGIN_ISOLATED / SOURCE_UNVERIFIED / PROTOCOL_PROPOSED`.

## 1. Formal method change: working software first

The operating sequence for product iteration becomes:

> **First Usable Product → Product Owner Feedback → Product Refinement → Full Engineering & Production Hardening**

This does **not** waive critical security controls or reduce engineering quality. It **separates a deliberately narrow localhost/synthetic preview threat envelope** from public SaaS/Production authority. The progress metric is now **can the owner install, run and use a complete merchant journey**, not the number of design documents or test methods in isolation. Each Work mission must state its visible output, smallest slice, essential work, deferred work, tests and still-blocked Production permissions.

**Astra Management** continues to own architecture/product choices, scope, security gates and Work acceptance. **Astra Development / Work** owns source inspection, coding, local tests, traceable Draft PR, ZIP, verified cold-start and exact SHA, manual run instructions and handoff. Decisions affecting experience and important risk return to the product owner **after the working PV0-01 walkthrough**; noncritical stack/design decisions are delegated to Management/Work.

**This is an explicit separate authorization to build local preview code.** It supersedes the previously narrow visual-only M1 mission, **not** the security decisions or historical APR baseline. There is no automatic approval of any submitted code, merge, network service, real AI or public Live.

## 2. Live repository status and S0-09H evidence separation

At strategy review, GitHub main was `cacdee59fbd9b53e754e8a4c95b274e18ce6e8fb`; all **16 open PRs were Draft**, including [#32](https://github.com/alireza-anari/cac-project/pull/32) and UX [#40](https://github.com/alireza-anari/cac-project/pull/40). [#41](https://github.com/alireza-anari/cac-project/issues/41) was still open and had **no separate M1 Draft PR among those open PRs**. [S0-09H evidence ruling](../architecture/S0_09H_ARCHITECTURE_RULING.md) exists on main.

**Accepted S0-09H only as** `BOUNDED_Q_SURVIVAL_REAL_QUORUM_INTEGRATION`: actual five-member etcd 3.6.16 cluster, actual PostgreSQL 17.11/PgBouncer 1.22.0, same-host test harness, an **already current 3/5 admitted non-restored majority**, logical W rollback/minority learner replacement, guarded source/SQL, first-use and lost response cuts. Independent physical/admin root continuity is NOT proven. H final Draft PR #32 head `b32416c799160f0e5957506d58254a693cbc231f`, stacked on prior experimental PR #27, **UNMERGED**. Final receipts documented successful 51 distinct H DB/security methods, 169 inherited methods across separate workflows (220 total across suites), 2 separate artifact scanner methods, five mutation RED/restored GREEN probes, and successful push/PR workflows. They are **not** one combined production certification or a license to reuse the experiment as Product backend.

**Still failing/unproven:** historical S0-09D C-only anchor rollback **`FAIL_SECURITY`**; responsive majority-R rollback and jointly restored verifier/guard **UNSUPPORTED** with `GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED` when independent trusted guard does not survive; E G1–G5 P0 `DESIGN_BLOCKED`; Lane3 orphan `OPEN_UNKNOWN` release P0 BLOCKED; root policy retirement and literal stale Raft snapshot/WAL import `NOT_RUN`. No fabricated recovery security PASS. Source [#1](https://github.com/alireza-anari/cac-project/issues/1)/GATE-SOURCE BLOCKED; canonical baseline [#9](https://github.com/alireza-anari/cac-project/issues/9) OPEN; root issues [#33](https://github.com/alireza-anari/cac-project/issues/33)/[#28](https://github.com/alireza-anari/cac-project/issues/28)/[#23](https://github.com/alireza-anari/cac-project/issues/23) OPEN. The missing original historical baseline cannot be recreated simply by calling a new Preview `v3.37`.

## 3. Preview boundary and chosen minimal technical design

**PV0-01 is a real, local, test-data application**, not a mockup or a static UI. Use `preview_v0/` as an independently new-origin source root on a clean branch off latest `main`, never cherry-pick experimental S0-07/S0-09 code. **Choose** Python 3.12, supported security-patched **Django 5.2 LTS**, SQLite local persistence, Django templates and local CSS/minimal vanilla JavaScript. Standard Django sessions, password login, CSRF, ORM and built-in escaping provide suitable baseline controls within **only the single-local-demo-owner threat envelope**. Python package installation is permitted to bootstrap locally; server/application must not call external services at runtime. Pin an actually tested Django security patch in the deliverable, not an unspecified moving dependency.

**Why:** avoids the risk and operating cost of deploying R/W/etcd, PostgreSQL/RLS, Woo, external LLM, remote auth, multi-host secrets/custody before the owner can judge product experience. This Preview's SQLite, login and local tests are **NOT** substitutes for public SaaS tenancy and production root/RLS requirements. Never run/host outside loopback or allow real customer/user/business information.

**Hard local controls:** bind dev server to `127.0.0.1`; local-only `ALLOWED_HOSTS`, no public deployment; generated secret and random one-time demo-owner credential on local setup, never committed or shipped; ignored `.local_state/` for SQLite/secret and local test entries; CSRF on all writes; per-owner Store query scoping even though first demo is single-merchant; model/object validation, bounded input lengths and default escaping, negative ownership tests, no file upload/SSRF URL ingestion, no external requests/CDN/JS libraries. A local development server is **never Production secure**. A failure in a local protection blocks local delivery; it does not demand distributed DR simulation.

**Feature design for first slice:**
- Persian, RTL, mobile-aware four-section merchant panel with **Overview / Conversations / Assistant Information / Settings** from PR #40, a prominent local Preview disclosure and one next-action guide.
- Local owner sign-in, real form to create/edit a sample Store and persist it across page and server reloads.
- Local product/service CRUD (at least two examples) with price/description/availability and safe validation.
- One local Store Assistant with name, welcome message, tone (not publicly Live), store-specific preview page.
- Interactive private chat with **deterministic local rules** bound to the Store's saved products/services (list/price/availability/known vs unknown), explicitly `Demo — NOT AI`. No fake LLM attribution or calls.
- Visible clear state `PRIVATE_DEMO / PUBLIC_LIVE_DISABLED`. APR-034 at most one **public** Live assistant per store is preserved; a demo private assistant is not the public Live product. Verified contact, Woo, real IdP, consent/provider checks are **absent**, not fake completed.
- Owner can actually change a product/assistant and see updated chat response, then restart app and confirm persistence. This is the mandatory **owner feedback checkpoint**.

**Do not implement** real public assistant, visitor iframe/links, payment/billing, real Woo sync, real AI provider, contact/domain verification, production multi-tenant identity and RLS, actual 30-day transcript privacy guarantees, SSRF ingestion, payment/account administration, root epoch/failover, external storage/hosting or real data. Display missing functionality as `not in Preview V0`, not as completed authentication/Live readiness.

## 4. Small roadmap and deliverable gate

| Increment | Minimum observable delivery | Owner acceptance | Authorization |
|---|---|---|---|
| **PV0-01 — FIRST** | User logs in locally, configures test Store, adds/edits products or services, configures one private assistant, asks real typed questions and receives explicit Demo-grounded answers; SQLite persistence and real RTL pages | Source + clean ZIP/startup, local smoke/test evidence and complete owner walkthrough | **AUTHORIZED via #43** |
| **Product owner feedback** | Owner actually tries the ZIP and comments on layout, beginner guidance and assistant/product flow | Collect accept/revise/reject and top 3 desired improvements, no speculative hardening task | **REQUIRED BEFORE NEXT FEATURE SLICE** |
| **PV0-02** | Only improve UI/usability/feature gaps chosen from owner feedback; new runnable ZIP and smoke tests | Owner approves changes | **NOT YET AUTHORIZED** |
| **PV0-03 (optional)** | Real AI connection only if provider/privacy, explicit credential/cost/user decision and prompt/data boundary can be enforced safely; otherwise continue explicitly labeled Demo | Separate technical/security authorization | **NOT AUTHORIZED** |
| **Full architecture + Production** | Independent accepted source baseline, actual IdP/MFA/tenant RLS, Woo/product privacy, knowledge review, widget, retention and operational security including allowed disaster/unknown states | Independent gate-specific acceptance, owner release consent | **BLOCKED** |

**Critical rule:** do not expand PV0-01 into full S0–S6, billing or unqualified E/R root. If a proposed feature depends on unresolved security, omit or disable it clearly. A UX-only green mock is not accepted as "usable"; the app must persist edits and interactively answer the owner from the local demo DB.

## 5. Exact PV0-01 acceptance (PRODUCT_OWNER_LOCAL_PREVIEW only)

Required outcomes on a **clean extracted ZIP**:

1. Install pinned dependencies and bootstrap local demo credentials without embedding the SQLite DB, secret/private key or user data in ZIP. Provide **Windows PowerShell and macOS/Linux** instructions; no cloud account needed.
2. Start local server `127.0.0.1:8000`, authenticate as bootstrap demo owner, open a visible **local/experimental** Persian RTL merchant dashboard.
3. Create/edit sample Store, add two test products/services and see them persisted after reload and server restart.
4. Set assistant's name/greeting/style and see those choices reflected in customer-view Preview.
5. Type real questions; demo rule engine answers from the **saved products**, updates after a product change, declines unsupported unknown questions and unmistakably declares **no real AI**.
6. See four merchant areas, clear explanation that public Live, Woo, payments, external AI, real domains, user data and Production are unavailable.
7. Run at least minimal tests for login/ownership, Store/product boundaries, CSRF, input validation/XSS escaping, one assistant/store, chat grounding/fallback, persistence, no outbound API and no public endpoint. Publish **actual commands/results and failures**, not generic PASS.
8. Work hands off exact Draft PR/branch/head/base SHA, full source, downloadable ZIP location + SHA-256, cold-start and manual acceptance evidence, test log and limitations table. A role-separated read-only source review is appropriate **within that same deliverable**, not a multi-stage architecture project.

**After this acceptance, pause scope expansion for real product owner feedback.** Do not claim owner acceptance merely because Work's tests pass. Owner's visual judgment is a different gate from technical handoff.

## 6. Work command template for future slices

Each new Work mission must include six explicit answers: visible owner experience; smallest executable slice; essential engineering and security controls; deferred work; exact functional/manual/negative tests; remaining **Production-blocked** areas and what would change that status. Preserve change trace (SHA/PR), executable ZIP and clear DEMO/WORKING_LOCAL/UNIMPLEMENTED statuses.

**Evidence labels:** `LOCAL_PREVIEW_WORKING` / `DEMO_RULE_BASED` / `PRODUCT_OWNER_FEEDBACK_PENDING` / `PRODUCTION_BLOCKED`. Never use `SECURITY_PROVEN` to describe local CRUD tests or `ORIGINAL_SOURCE_RECOVERED` for new-origin Preview. Source recovery and security research may proceed independently when genuinely new evidence exists, not as a dependency on product owner seeing the local tool.

## 7. Governance and rollback of obsolete mock-only priority

The prior [Issue #41](https://github.com/alireza-anari/cac-project/issues/41) for a nonfunctional offline HTML/CSS mock is **superseded by PV0-01**. A separate static-only M1 PR is no longer the critical path and should not consume Work time. This does not delete/rewrite the earlier signed Management authorization; it adds a **later, explicit and more narrowly outcome-oriented** development permission and closes #41 as not planned due to changed product owner strategy, if no implementation has started. The reviewed UX PR #40 remains Draft/unmerged and is used only as a design reference. No previous experimental/review PR is automatically merged or treated as verified product backend.

**Formal vote:** `PREVIEW_FIRST_STRATEGY_ACCEPTED / PV0_01_NEW_ORIGIN_LOCAL_EXECUTION_AUTHORIZED / M1_STATIC_ONLY_SUPERSEDED / OWNER_FEEDBACK_REQUIRED / PRODUCTION_GATES_OPEN`.

### Engineering framework reference (not CAC proof)

Django 5.2 is a long-term support release with supported Python 3.12; Django's `runserver` and SQLite can support a local development application, but `runserver` is expressly not appropriate for Production. See https://docs.djangoproject.com/en/5.2/releases/5.2/ and https://docs.djangoproject.com/en/5.2/ref/django-admin/#runserver .
