# CAC — Security gates and evidence requirements

All gates require direct evidence (code ref, execution command, environment, output/log and reviewer), never a plan-only PASS.

| Gate | Required evidence | Current status |
|---|---|---|
| SOURCE | Authentic Freeze source or repo commit, checksums, conflict log | BLOCKED |
| BOOT/MIG | Reproducible Django checks; migrations up/down on PostgreSQL | BLOCKED |
| TENANT | Composite FKs; ENABLE/FORCE RLS; non-owner runtime role; multi-tenant/multi-store negative tests | BLOCKED |
| ONBOARD | Verified identity + fresh MFA for sensitive operations; atomic provisioning, invite/revoke, audit, race tests | BLOCKED |
| ASSISTANT | Readiness, contact, domain verification, race-safe one-public-Live invariant and pause behavior | NOT RUN |
| WOO | HMAC, nonce/replay defense, reconciliation, product-only ingestion, price/stock freshness | NOT RUN |
| KNOWLEDGE/AI | Human review, safe URL/file ingest, tenant-scoped RAG, approved provider and terms | NOT RUN |
| WIDGET/RETENTION | Origin/source/nonce checks, visit isolation, 30-day expiration and deletion tests | NOT RUN |
| PRODUCTION | Integrated E2E/security/ops/legal approvals with owner signoff | NOT AUTHORIZED |

## Known technical security blockers

- `DB-001`: PostgreSQL RLS, FK and least-privilege roles not verified.
- `IDENTITY-001`: trusted identity/MFA/CSRF at actual service boundary not verified.
- `PROVISION-001`: privileged provisioning worker and accept/revoke PostgreSQL concurrency not verified.
- `SOURCE-001`: authenticated baseline not recovered.

No credentials or actual customer-private data should be committed. Public repository access may enable anyone to inspect or clone published commits even if privacy is changed later.
