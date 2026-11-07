# CAC — S0-10A Final UX Management Ruling and S0-10A-M1 Static Mock Authorization

**Decision owner:** Astra Management / Product and Security Architecture  
**Date:** 2026-11-07  
**Reviewed UX PR:** [#40](https://github.com/alireza-anari/cac-project/pull/40), **OPEN/DRAFT/UNMERGED**, head `971bcaab79b7e249866b948243ef881cecf7045a`, based on main `44b593588573223a28ec7658ccb03966f84d45fc`.  
**Exact authored UX contract:** [S0-10A Persian UX R0](https://github.com/alireza-anari/cac-project/blob/971bcaab79b7e249866b948243ef881cecf7045a/docs/product/S0_10A_MERCHANT_UX_ASSISTANT_LIFECYCLE_R0.fa.md), blob `134e03df377eaa544617cc9a57e5108a51f47420`.  
**Independent review:** [PR #40 independent role-separated design review](https://github.com/alireza-anari/cac-project/pull/40#issuecomment-6710229702), no external certifier.  
**Delivery:** [Issue #39](https://github.com/alireza-anari/cac-project/issues/39).  
**New distinct bounded mock authorization:** [Issue #41 — S0-10A-M1](https://github.com/alireza-anari/cac-project/issues/41).  
**Formal vote:** `S0_10A_UX_CONTRACT_ACCEPTED_FOR_BOUNDED_MOCK_DESIGN / M1_OFFLINE_STATIC_VISUAL_PROTOTYPE_ONLY_AUTHORIZED / PRODUCT_AND_SECURITY_GATES_UNCHANGED`.  
**Source identity:** `CAC-NEW-ORIGIN-S0-07 / UX_DESIGN_ONLY / SOURCE_UNVERIFIED / PROTOCOL_PROPOSED`.

## 1. Management verification and accepted scope

The PR #40 final head was checked against the exact review/handoff and has **one new Markdown file**. The written contract includes **exactly four** primary sections (Overview / Conversations / Assistant Information / Settings), an Overview-hosted guided checklist, `Private Preview → owner confirmation → install → verification → Live` with explicitly gated public activation, proposed merchant-facing state labels, evidence-qualified Live-readiness, safe Persian/RTL copy, privacy and capability constraints, traceability to APR-033/034/035/036 and **10 textual scenarios, all `DESIGNED / NOT_RUN`**. Final-head workflow query returned **zero runs**. This is not an executable product or a passed security gate.

The independently attributed reviewer initially flagged three issues, all corrected in the exact reviewed document:

1. Closing a confirmation **before** submit results in no request. Closing or navigating **after** submit cannot undo a request or infer whether it succeeded; preserve a pending/unknown overlay and only check the **same** request outcome. Do not repeat an activation.
2. Confirmed loss of the final qualifying contact triggers **system-initiated public Pause** independent of a merchant clicking Pause. A transient validation timeout, by itself, does not meet that loss condition; after Pause there is **no auto-resume**.
3. `ادامه راه‌اندازی` goes to the **first actionable incomplete step based on valid current evidence**, not always to Assistant Information. If blocked by authority or other reviewer, show the correct owner/queue.

**Management accepts:** `UX_CONTRACT_READY_FOR_BOUNDED_MOCK_DESIGN`. This is approval of the **internal UX design basis for visual exploration only**; not a release, customer usability validation, approved backend API/state machine, APR change, security certification, a source baseline or automatic authorization to create code.

## 2. Separate M1 authorization — exact privilege

Management independently authorizes **one isolated, static and wholly synthetic frontend prototype**, on a fresh new feature branch **against the current main**, in a **new Draft PR**, under:

`prototypes/s0-10a-merchant-ui/`

Allowed: static `index.html`, `styles.css`, minimal plain `demo.js` for navigation/dialogs and selector of **preauthored fixture scenarios**, `README.fa.md`, and minimal same-repo local decorative SVG artwork. A local offline file or loopback-only preview is allowed; limited manual visual/keyboard/responsive inspection is allowed. This is narrow **prototype code permission**, distinct from S0-10A's documentation-only scope.

**Forbidden:** editing existing product/backend/security code or workflows, pip/npm/build dependencies, external libraries/CDN/fonts/network calls, fake API routes, Django/SQL/RLS/migrations, keys, IdP/MFA/account login, WooCommerce plugin or data access, provider egress or AI response generation, real visitor iframe/widget, real domain/site installation, public hosting, customer/merchant secrets, payments, feature-flags authorizing live mode, Production, Merge, or submitting any real authoritative command. No paid services. Do not create a runnable application server accessible beyond a local loopback.

**Prominent persistent disclosure on every view and dialog, including mobile:**

> نمونه نمایشی با داده‌های ساختگی — متصل به سرویس واقعی نیست

A sample merchant "Live" or "Paused" can be rendered **only as a clearly labeled hypothetical historical fixture**, never as an actual current service. Active buttons for public activation, account validation, payment or real moderation must be disabled or strictly explanatory; no browser interaction can cause current-verified authorization, mark an unverified item ready, or complete a real state transition. Any "status outcome" is a clearly labeled fixture preset, not a simulated secure backend. Keep demo and product claims unambiguously separate.

## 3. Must-show visual flows

Provide a cohesive Persian RTL desktop/mobile design with a simple four-section navigation, friendly beginner text and accessible interactive states. Directly trace components to [the reviewed UX contract](https://github.com/alireza-anari/cac-project/blob/971bcaab79b7e249866b948243ef881cecf7045a/docs/product/S0_10A_MERCHANT_UX_ASSISTANT_LIFECYCLE_R0.fa.md) and its U01–U10 scenarios:

- New store: Overview guide, first incomplete step and readable reasons, not a false progress-bar PASS; Conversations empty/permission/expired; Assistant Information preview/knowledge; Settings contact/Woo/catalog/domain and subscription summary.
- Real-world readiness **represented as unverified fixture states only**: qualifying owner-attested contact, domain+widget verify, public-only Woo catalog including real-observation price/stock freshness 30/10 min, two-reviewer approval for sensitive knowledge, provider/privacy approval, immutable owner confirmation, one Live/Store, security baseline/guard and visitor/30-day retention.
- Private Preview is represented as a **screen/wireframe**, with **no AI provider** and no public widget; owner confirmation and public Live are **not implemented**. Display reason why they are unavailable.
- Pre-submit cancel vs post-submit lost ACK/unknown status, competing Live requests, system-initiated last-contact Pause and **no auto-resume**, transient probe outage **not** itself contact loss.
- Security incident and `OPEN_UNKNOWN` represented only by a safe blocked/support screen. No reset, automatic reconciliation, inferred abort, safe global denial claim or new root.
- Device widths, clear focus, keyboard navigation and focus return, no information carried by color alone, no real personal/private data or sensitive demo seed.

## 4. Verification and handoff contract

Work's future M1 PR must include exact base/head SHA, changed files confined to `prototypes/s0-10a-merchant-ui/`, a README explaining it opens **offline with no external dependencies**, screenshots only **if genuinely captured locally** (no invented screenshot/automated-run claim), simple local visual/keyboard/RTL/mobile QA with `OBSERVED` vs `NOT_RUN`, and an explicit source scan showing zero remote URLs, `fetch`, XHR, WebSocket, beacon or unauthorized storage/real-data handling. It should include a review from a role-separated independent design/scope reviewer; that reviewer is not a product/security certification provider.

A mock preview cannot evidence Live/IdP/tenant/RLS/30-day retention/root safety or service implementation. **Mock UI local navigation pass ≠ S0–S6 integration gate pass.** The mock is **never** authorized for public hosting or merging by this ruling. Required final reviewer verdict: `M1_VISUAL_MOCK_READY_FOR_PRODUCT_REVIEW`, `TARGETED_MOCK_FIX_REQUIRED`, or `MOCK_UNSAFE_SCOPE_BREACH`. Management will decide afterward whether to iterate mock design, commission Woo public-catalog **contract** work, or return to source/security dependencies. No automatic next work beyond M1.

## 5. Priority, ownership and open hard gates

S0–S6 main delivery roadmap remains source/security gated. S0-10 is a permitted parallel product **design** lane, not release. [SOURCE-001 #1](https://github.com/alireza-anari/cac-project/issues/1)/GATE-SOURCE **BLOCKED**; [baseline #9](https://github.com/alireza-anari/cac-project/issues/9) OPEN. [Root #33](https://github.com/alireza-anari/cac-project/issues/33), [#28](https://github.com/alireza-anari/cac-project/issues/28), [#23](https://github.com/alireza-anari/cac-project/issues/23) OPEN. Original S0-09D C-only rollback `FAIL_SECURITY`, surviving-majority H bounded only, E G1–G5 `DESIGN_BLOCKED/NOT_RUN`, majority R and obsolete-verifier restore UNSUPPORTED, `GLOBAL_FAIL_CLOSED_NOT_ESTABLISHED` when mandatory current guard is also reverted, Lane3 truly unresolved orphan `OPEN_UNKNOWN` clearance P0 BLOCKED/NOT_RUN. Actual root policy retirement and literal old Raft snapshot/WAL import NOT_RUN. S0-09J #36 completed research only; current E1/E2 not qualified. APR-033/034/035/036 unchanged. Previous experimental and documentation PRs, including #40, remain Draft/unmerged.

**Management decision:** `UX_DESIGN_ACCEPTED_FOR_VISUAL_EXPLORATION / M1_STATIC_LOCAL_ONLY / ZERO_REAL_AUTHORITY / NO_MERGE_OR_PRODUCTION`.
