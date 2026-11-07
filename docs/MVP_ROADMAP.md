# CAC MVP — Execution Roadmap

**Architecture freeze:** v3.37 / APR-036. **Working state:** NOT_MERGED / SOURCE_UNVERIFIED.

| Sprint | Execution scope | Acceptance gate | Status |
|---|---|---|---|
| S0 | Source recovery, verification, standalone handoff, reproducible bootstrap | SOURCE and BOOT | BLOCKED |
| S1 | Django/PostgreSQL tenancy, RLS, identity, secure onboarding | MIG, TENANT, ONBOARD | BLOCKED |
| S2 | Assistant lifecycle and merchant UI | ASSISTANT | Not started |
| S3 | WooCommerce public-catalog integration | WOO | Not started |
| S4 | Reviewed knowledge and scoped AI provider adapter | KNOWLEDGE/AI | Not started |
| S5 | Embedded widget, isolated visitor conversations and retention | WIDGET/RETENTION | Not started |
| S6 | Subscription, operations and release readiness | PRODUCTION | Not started |

## MVP product guardrails

- Admin information architecture: Overview, Conversations, Assistant Information, Settings.
- Owner approval required for production deployment, approved AI provider/processing terms, contracts and spending.
- **APR-033:** qualifying, verified contact before public assistant activation.
- **APR-034:** V1 maximum one active public assistant per store, while permitting a future extensible data model.
- **APR-035:** confirmed loss of final qualifying contact pauses public assistant; a transient probe outage alone does not.
- WooCommerce connector reads only public product/variant data; no order, customer or payment private access.
- Visitor raw message retention target: 30 days from last real message; expired content must not be returned even before physical purge.

## Management controls

Every Work delivery must specify real repo/ref or archive SHA-256, changed files, environment, executed commands, exit codes, test logs, API/schema changes, security findings and blocking dependencies. Missing evidence is never PASS.

S0 and S1 remain blocked until authentic source recovery and required environment gates are evidenced.

Issue tracking: [SOURCE-001](../issues/1) · [Standalone handoff](../issues/2).


## S0-10 parallel design-readiness lane — management checkpoint 2026-11-07

This section **does not replace** S0–S6, unblock Sprint0/Sprint1, approve production or change APR-033/034/035/036. It is a parallel, **documentation-only** product design lane permitted while source/security integration gates remain blocked.

| Lane | Next bounded action | State / required evidence |
|---|---|---|
| SOURCE-001 / architecture baseline | Authentic v3.37–v3.39 source recovery/verification **if real source becomes available**; separate review of experimental new-baseline identity | [#1](https://github.com/alireza-anari/cac-project/issues/1) GATE-SOURCE **BLOCKED**, [#9](https://github.com/alireza-anari/cac-project/issues/9) **OPEN** |
| S0-09 root/security obligations | Preserve original D rollback FAIL_SECURITY, H non-restored majority limited evidence, I/J negative current E qualification and OPEN_UNKNOWN blocking | [#33](https://github.com/alireza-anari/cac-project/issues/33), [#28](https://github.com/alireza-anari/cac-project/issues/28), [#23](https://github.com/alireza-anari/cac-project/issues/23) **OPEN**; no new E/PoC |
| **S0-10A merchant UX + assistant lifecycle** | Four top-level screen narratives, guided private Preview/verified activation, contact/domain/privacy readiness and honest Pause/blocked states, no actual app/endpoint | [Design-only Issue #39](https://github.com/alireza-anari/cac-project/issues/39) **AUTHORIZED FOR DOCUMENTATION ONLY**; reviewable Draft PR required |
| Next possible source-independent work | Public-only Woo catalog contract, content-review UX and privacy/retention screen plan | **NOT YET AUTHORIZED**; separate Management scope after S0-10A design review |
| Actual application integration/public Live | Django/PostgreSQL RLS, identity/onboarding, Woo/AI/Widget secure deployment, legal/provider and production operations | **BLOCKED / NOT AUTHORIZED** until independent relevant approval and all actual evidence gates |

[Detailed S0-10 management decision](management/S0_10_PARALLEL_PRODUCT_DELIVERY_PLAN_R0.md). A demo/mock that displays READY or LIVE does not prove any real readiness; no new API/schema/privilege contract follows from a UX label.


## S0-10A accepted UX contract / S0-10A-M1 explicitly authorized static mock — 2026-11-07

- [UX contract Draft PR #40](https://github.com/alireza-anari/cac-project/pull/40), head `971bcaab79b7e249866b948243ef881cecf7045a`, **DESIGN_ACCEPTED_FOR_BOUNDED_MOCK_ONLY**, [documentation Issue #39](https://github.com/alireza-anari/cac-project/issues/39) completed/closed strictly as UX documentation. Ten merchant journeys remain `DESIGNED/NOT_RUN`.
- [Separate M1 Issue #41](https://github.com/alireza-anari/cac-project/issues/41) and [Management authorization](management/S0_10A_UX_ACCEPTANCE_AND_M1_STATIC_MOCK_AUTHORIZATION.md) allow **only a standalone offline, synthetic HTML/CSS/minimal-JS visual panel prototype** under `prototypes/s0-10a-merchant-ui/`, in a new unmerged Draft PR. No backend, login, Woo/AI, network, real data, actual public Live/Preview, hosted demo, Production, or canonical source claim.
- S0/S1 and actual S2–S6 implementation/release gates **remain BLOCKED/NOT_RUN**; this is a parallel *visual design* exercise, not evidence of application readiness. `SOURCE-001/GATE-SOURCE` BLOCKED, #9 OPEN, S0-09D original FAIL_SECURITY, root majority catastrophe UNSUPPORTED, Lane3 orphan clearing BLOCKED and E P0 G1–G5 DESIGN_BLOCKED.
