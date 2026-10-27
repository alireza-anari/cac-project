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
