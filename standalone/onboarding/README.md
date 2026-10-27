# CAC standalone onboarding — SEC-REV-001

**NOT_MERGED / SOURCE_UNVERIFIED / NOT_PRODUCTION_READY**

Source ID: `CAC-SEC-REV-001-STANDALONE-S0-02`. This import is the actual previously delivered correction, not a recreation. `PROVENANCE.json` records verified archive SHA-256 values and exact imported source hashes. The packaging version `0.3.40.post2` identifies this standalone distribution only; it is not a new architecture Freeze or integrated backend release.

The original `archive/v3.40-unpatched-reference` branch remains unchanged. Its seven source/test/API files match the original v3.40 archive. The corrected service and thirteen additional tests match S0-02 byte-for-byte.

## Install and test

From the repository root (Python 3.12 recommended):

```bash
python -m venv .venv
.venv/bin/python -m pip install ./standalone/onboarding
cd standalone/onboarding
PYTHONPATH=. ../../.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

The runtime uses only Python stdlib and SQLite. Installation uses pinned setuptools 80.9.0 in its isolated build environment. For offline source tests, no installation or third-party package is needed:

```bash
cd standalone/onboarding
PYTHONPATH=. python -m unittest discover -s tests -p 'test_*.py' -v
```

There are 45 tests: 32 unchanged original tests plus 13 revocation regressions. All fixtures are synthetic. CI records environment, exact tested SHA, exit status and full logs as workflow artifacts. GitHub PR workflows may test a synthetic merge SHA; their evidence records both the PR head and the actual checked-out SHA.

## Security scope

Revoke invalidates matching pending invitations even when no active grant exists. Grant changes, invitation invalidation and the effective `CAPABILITY_REVOKED` audit event remain in one transaction. Unrelated target/store/capabilities are preserved; owner, delegation and MFA policy are unchanged. No-op repeats do not create effective audit events. A new authorized invitation after revoke remains allowed.

SQLite tests do **not** prove PostgreSQL concurrency, RLS, real identity/MFA/CSRF, secure delivery or append-only audit. See [integration readiness](docs/INTEGRATION-READINESS.fa.md) and [PostgreSQL race design](docs/POSTGRES-ACCEPT-REVOKE-RACE-PLAN.fa.md). Those inherited S0-03 plans are design-only; their historical candidate paths map to this directory. Backend destinations remain unknown until source recovery.

`SOURCE-001` and backend integration gates remain BLOCKED: authentic v3.37/v3.38/v3.39 source is not recovered merely by publishing this module. No schema, API, migration or RLS policy is changed by this import. `integration/` contains reference contracts only, not wired endpoints.

## Provenance and review

The prior independent S0-02 review reported no Critical/Important/Minor findings for the identical service/test bytes. Its review digest is recorded in `PROVENANCE.json`; it explicitly excluded PostgreSQL/RLS, real IdP, production adapters and integration. Current execution evidence is separate from that historical review.

All imported code originates from the owner-provided CAC artifacts. No third-party implementation was copied and no new license grant is introduced. The upstream artifacts and repository do not declare an open-source license; public visibility alone is not a license. Do not package credentials, customer data or original evidence ZIPs into this distribution.
