# S0-08 — trusted identity and onboarding security contracts

**DESIGN_ONLY / PROPOSED_CONTRACTS. Every MUST/SHALL below is a proposed contract obligation, not an approved architecture decision.** Source identity remains **CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL**. SOURCE-001 and GATE-SOURCE remain BLOCKED. No executable code, migration, OpenAPI change, deployment or new test execution is delivered here.

## Review order

1. [Threat boundaries](01-threat-model.md)
2. [Identity, session, MFA and CSRF](02-identity.md)
3. [Context issuer and key lifecycle](03-context-keys.md)
4. [Transactions, roles and pooling](04-transactions-pooling.md)
5. [Provisioning, invitations, revocation, audit/outbox](05-onboarding.md)
6. [Acceptance tests and eight race mappings](06-acceptance.md)
7. [ADR/CR decisions, risks and conditional S0-09](07-decisions-risks.md)

## Evidence actually read

Repository https://github.com/alireza-anari/cac-project. Design branch starts at main **25dca018008cd7a4bab31196d1f146cea9f588cc**, which accepts S0-07B narrowly and opens S0-08 #13. Architecture ruling [#9](https://github.com/alireza-anari/cac-project/issues/9) permits isolated experiments, not baseline promotion or merge. [#13](https://github.com/alireza-anari/cac-project/issues/13) is the execution scope.

[PR #11](https://github.com/alireza-anari/cac-project/pull/11) was read at **a27eab0e978c6c60d54fab45b9f467ebd7ddff56**, Draft/unmerged: S0_07_HANDOFF, S0_07B_HANDOFF, backend README/contract inventory, settings, models, SQL verifier/roles and regressions. These files are not present on main; use [immutable source links](https://github.com/alireza-anari/cac-project/tree/a27eab0e978c6c60d54fab45b9f467ebd7ddff56/experimental/backend), not an implied merge into this branch. Existing proof is 39 PostgreSQL tests + 4 configuration tests; it does not prove the proposals below.

Main inputs: `docs/ARCHITECTURE_GOVERNANCE.md`, `docs/PROJECT_STATUS.md`, `docs/SOURCE_ARTIFACTS.md`, `docs/MVP_ROADMAP.md`, `docs/SECURITY_RELEASE_GATES.md`, `docs/cac/03_SECURITY_DATA_CONTRACTS_AND_RELEASE_GATES.fa.md`; standalone service `revoke_capability`, `issue_invitation`, `accept_invitation`, revocation regressions; `standalone/onboarding/docs/POSTGRES-ACCEPT-REVOKE-RACE-PLAN.fa.md`; pending `docs/changes/CR-S0-05-001-invitation-error-response.md`. Main paths refer to the starting SHA above.

## Definite requirements vs proposals

| Authority | Preserved constraint | This design does not establish |
|---|---|---|
| APR-033 | Qualifying verified contact before public Live | Verified owner email is not qualifying business contact |
| APR-034 | At most one public active assistant per Store in V1 | No assistant activation implementation here |
| APR-035 | Confirmed loss of final qualifying contact pauses public access; private Preview preserved | A transient probe outage is not confirmed loss |
| APR-036 | v3.37 remains the approved Freeze | No recovered historical source or compatibility certificate |
| Governance docs/cac/03 | Scoped capabilities, real composite FKs, ENABLE/FORCE RLS; server-trusted transaction identity; same-origin admin session/CSRF and sensitive MFA; idempotency/outbox | Exact issuer format, lifetimes, new tables/roles or lock algorithm are not approved |
| CR-340-001 / standalone bytes | Independent onboarding and SEC-REV-001 behavior are real references | Python/SQLite interfaces are not accepted Django/PG contracts |
| #9 / #13 | New-origin design/exploration is allowed | All new decisions below need Architecture review before coding |

## Approaches considered (Work recommendations, not owner approvals)

- Identity-derived unsigned GUC: rejected; arbitrary runtime SQL can forge it, conflicting with governance.
- Signer key inside every web worker: smaller system, but worker compromise grants unrestricted minting authority. Not recommended.
- **Recommend isolated identity/issuer boundary**, using server-side sessions and independent authoritative checks; DB verifies signed context and current authorization state. More operational complexity; compromised web worker can still abuse sessions it sees. It cannot legitimately mint arbitrary principal/scope without issuer evidence. No vendor selected.
- For initial approved experiment, retain HMAC with protected broker/DB copies rather than introduce an unverified asymmetric PostgreSQL extension. Both trust boundaries are explicit. Asymmetric verification is a future alternative requiring module and key-custody review.
- Recommend short explicit transactions and a coarse Store authorization guard for mutations over premature fine-grained locking. Throughput is lower but lock ordering and revoke semantics are reviewable. PgBouncer transaction mode is conditional on a pinned real compatibility suite, not assumed supported.

## Publication and validation boundary

Only new Markdown under `docs/s0-08/` is intended. No change to PR #11, its branch, executable configuration, schema or API. Validation in S0-08 means diff/link/coverage review only; all future acceptance cases are NOT_RUN. Design review readiness is not a security gate PASS. Final commit and Draft PR identify this document snapshot; #9 reviewers decide ADR/CR candidates explicitly.

## Design validation receipt

Local relative-link scan: 8 Markdown files, zero missing local targets; `git diff --check` clean. No application tests, PostgreSQL tests, migrations or lint of a changed API were run because this is documentation only. A separate read-only builder review identified an epoch-refresh/race-order inconsistency; the proposal now defines effective Store epoch increments and bounded authenticated snapshot refresh, distinct from revoked identity denial. A second finding showed a transactional registry alone cannot prevent savepoint-induced context switching; the proposal now requires an independent issuer ledger, challenge age window and direct-SQL negative test. This review is design feedback, not independent security certification. All new contracts remain PROPOSED.
