# S0-04 — standalone security import

**NOT_MERGED / SOURCE_UNVERIFIED.** Architecture remains v3.37 / APR-036; APR-033/034/035 are unchanged. Related: #2; blocked for backend integration by #1.

## Source and scope

- Verified actual corrected S0-02 ZIP: SHA-256 `bdae7c4d6d146714bc0ef4a3e2d0280944c1ecf85560a491050fa427315ac39f`.
- Verified actual S0-03 ZIP: SHA-256 `94f4d586023779500ea85a8cc7f76f092817e6b7da8a0dcb06aec2e59391a240`.
- Verified CRC/internal manifests. Eight selected Python/test/OpenAPI files are exact corrected-artifact bytes; see [provenance](../standalone/onboarding/PROVENANCE.json).
- Compared seven historical blobs at `0923d9bd761e04ba5bcf83c37e91ef7332f64c64` to original v3.40 ZIP: exact matches. Historical branch is untouched. Only service.py differs in existing executable source; test_revocation.py adds thirteen tests.
- Imported source ID: `CAC-SEC-REV-001-STANDALONE-S0-02`. No reconstruction or new frozen baseline.
- New metadata: installable pyproject, README, GitHub Actions, source provenance, sanitized local evidence and this handoff. No existing file is deleted.

## Tests and CI evidence

Fresh venv, Python 3.12.14, SQLite 3.53.1: package installation, installed import outside source root and all **45 tests passed** with exit 0. See [command/environment records](evidence/s0-04/execution.json) and [full test output](evidence/s0-04/unittest.log). There are 32 unchanged original tests and 13 new regression cases; no failures, errors or skips.

GitHub Actions installs the distribution and runs the real suite on Python 3.12. The workflow uploads environment, checked-out SHA, PR head SHA, exit code and full log. CI conclusions and URLs must come from the actual run attached to this PR/commit; this committed document does not predeclare a run outcome. A PR run may test GitHub's synthetic merge SHA, which is recorded separately from the source head.

PostgreSQL CLI/server/container binaries were not available on PATH in the local environment. No verified backend or PostgreSQL adapter exists here. PostgreSQL race tests, Django checks/migrations, RLS and real IdP/MFA/CSRF are **NOT_RUN / BLOCKED**, not SQLite PASS.

## Security review and publication

The prior independent S0-02 review covers exactly the imported service/test bytes and reported no Critical/Important/Minor findings. Review digest is in provenance; this is historical review evidence, not a fresh integrated audit. It excluded PostgreSQL concurrency/RLS, live IdP, production adapters and deployment.

Selected import files were inspected: tests contain synthetic identities and locally generated test tokens; no real customer data, credentials, secret keys or literal access tokens are needed. No historical evidence ZIP, unrelated repository inventory or raw customer/private log is imported. Local build paths and package-index URLs are sanitized in published logs. The original source provides no license notice; this import adds no license grant or third-party code and preserves its CAC origin.

Open risks: SOURCE-001; DB-001/RLS and scoped role enforcement; IDENTITY-001/MFA/CSRF/delivery; AUDIT-001 append-only audit/retention; RISK-PG-RACE-001. The fix preserves transactionality, scoped target/store invalidation, owner/delegation/MFA guards, effective audit, no-op replay and newly authorized invitations after revoke.

## Integration and next work

API diff: none. DB/schema diff: none. Migration: none executed/created. Import into the repository is not integration into a backend.

1. **P0 Management — SOURCE-001:** supply actual v3.37/v3.38/v3.39 archives or authenticated repository refs with provenance. New GitHub repository creation does not recover those sources.
2. **P0 Work — after recovery:** map real models/services/migrations and compare contracts before adapting the standalone fix. [Conditional plan](../standalone/onboarding/docs/INTEGRATION-READINESS.fa.md).
3. **P0 Work/DB — after baseline and disposable PostgreSQL:** run the [eight accept/revoke race scenarios](../standalone/onboarding/docs/POSTGRES-ACCEPT-REVOKE-RACE-PLAN.fa.md), multi-store RLS and role/context tests with real nonowner roles. Any schema/API/policy change requires separate impact review/CR.
4. **P1 independent work:** improve package/CI reproducibility and add contract validation tooling for the existing standalone addendum without declaring compatibility with absent frozen OpenAPI; API-001/API-002 remain open.
5. **P0 Work/Identity — after backend mapping:** wire trusted identity/MFA/CSRF, secure delivery and append-only audit, then seek Management integration acceptance.

This PR must remain open for Management review; do not auto-merge. GATE-SOURCE, BOOT/MIG/TENANT/ONBOARD and PRODUCTION remain BLOCKED. Local standalone test PASS is scoped evidence only.
