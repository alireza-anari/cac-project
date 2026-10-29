# CAC new-origin experimental backend foundation

**NEW_IMPLEMENTATION_EXPERIMENTAL — CAC-NEW-ORIGIN-S0-07**

This code is new. It is not recovered/reconstructed v3.37/v3.38/v3.39, not an accepted baseline and not production-ready. Historical SOURCE-001 and GATE-SOURCE stay BLOCKED. Issue #9 must be decided and security evidence reviewed before baseline promotion; execution is tracked by #10. No onboarding import, public endpoint, admin site, customer data, AI/Woo/billing connector or real identity integration exists.

Read [contract inventory / CR-S0-07-001](docs/CONTRACT_INVENTORY.md) first. All concrete schema/context choices are PROPOSED. APR-033/034/035/036 remain unchanged.

## Layout and versions

- `foundation/models.py`, `migrations/0001_initial.py`: proposed UUID Tenant, Store, Membership, ScopedGrant; experimental capabilities.
- `migrations/0002_security.py`, `sql/security.sql` and `security_reverse.sql`: composite FKs, ENABLE/FORCE RLS, signed context verification, exact table/function grants and reversible policies.
- `sql/roles.sql`: distinct migration owner, runtime and bootstrap provisioner; no superuser/BYPASSRLS/role membership for application roles.
- `scripts/bootstrap.py`: refuses nonfresh schemas, requires explicitly disposable DB name/flag; creates random role passwords/key in a mode-0600 file outside the repository.
- `tests/test_security.py`: real independent PostgreSQL connections/nonowner roles, synthetic principal/issuer fixtures. `scripts/roundtrip.py`: rollback/reapply schema/policy/ACL equivalence. `scripts/orm_smoke.py`: Django ORM under runtime login.

Target: Linux x86_64 / CPython 3.12.15 (local tooling 3.12.14), Django 5.2.18 LTS, psycopg/binary 3.3.6. Every Python distribution including transitive dependencies is exact-version/hash locked in `requirements.lock`. PostgreSQL 17.11 official bookworm image is fixed to manifest digest `sha256:839fbb5a4942a7758dd93e18b42ea5649807491a0545b5eeeb8f0b8bb11857a5`. GitHub Actions use immutable SHAs previously reviewed in S0-05. Registries/hosted runner availability remain external dependencies; no hermetic-build claim.

## Reproduce only on a fresh disposable database

From repository root:

```bash
python -m venv .venv-s007
.venv-s007/bin/python -m pip install --only-binary=:all: --require-hashes -r experimental/backend/requirements.lock
cd experimental/backend
# Use the activated venv for the commands below.
export CAC_EXPERIMENTAL_DISPOSABLE=1 PGDATABASE=cac_s007_test
export PGHOST=127.0.0.1 PGPORT=5432
# Supply ONLY your disposable cluster's synthetic postgres password through PGPASSWORD.
export CAC_TEST_CONFIG="${TMPDIR:-/tmp}/cac-s007-runtime.json"
export CAC_EVIDENCE_DIR="${TMPDIR:-/tmp}/cac-s007-evidence"
export CAC_DB_ROLE=cac_owner PYTHONPATH=.
mkdir -p "$CAC_EVIDENCE_DIR"
python scripts/bootstrap.py
python manage.py migrate --noinput
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations --plan
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/roundtrip.py
python -m unittest discover -s tests -p 'test_*.py' -v
CAC_DB_ROLE=cac_runtime python scripts/orm_smoke.py
```

The initial database must be newly created, named exactly `cac_s007_test`, with no application roles/schemas from a previous run. The bootstrap role needs privileges to create roles, extension and schemas; application traffic never uses it. Never point these scripts at a pre-existing product database. `roundtrip.py` intentionally destroys experimental domain rows while rolling migrations to zero; it is not a data-preserving production rollback strategy. Delete the private config after testing and destroy the disposable cluster. Do not publish that file, issuer key, password, DSN, environment dump or database dump.

The CI service uses a public, explicitly synthetic container-only bootstrap password. Application passwords and test issuer key are generated afresh. No repository secret or real credential is required. The database service is temporary and no external provider is contacted. CI uploads only named log/schema/version files, not credentials or the workspace. The schema snapshot contains structure/ACL only, not rows or keys.

CI also demonstrates an expected RED regression: after 0001 but before 0002, `test_actual_nonowner_roles_and_force_rls` must fail because RLS is absent; it then applies 0002 and requires the full suite to pass before and after rollback/reapply. An unexpected RED success or unrelated setup error fails the job. Actual runs, versions and exit codes belong in the Draft PR; no test outcome is asserted by existence of this code.

## Security model and limits

Runtime can only SELECT. Membership alone does not authorize Store/Tenant viewing: the active scoped membership must have `store.view`. Runtime can read its own active membership/grant metadata. Provisioner can SELECT/INSERT only within a signed bootstrap scope and only for the signed principal; it cannot UPDATE/DELETE/TRUNCATE, edit roles, own objects or read issuer keys. No ongoing authorization management or onboarding workflow is implemented.

`cac.context` is untrusted storage. The security-definer verifier authenticates HMAC-signed claims and binds them to login purpose, transaction ID, connection PID and expiry (maximum five minutes). A caller able to run arbitrary SQL as runtime still cannot forge other scopes or replay a token on another transaction/connection. The verifier uses a fixed search path and key table inaccessible to app roles. Empty-table queries may return no rows without evaluating a policy; this is fail-closed, not a guarantee that every missing-context SELECT throws. No HTTP identity boundary is implemented.

The test harness intentionally has the synthetic signing key and postgres fixture credentials. Production must have a separate trusted identity issuer, protected/rotated keys, no caller-controlled scope issuance, session/MFA/CSRF/revocation policies and pool integration. Compromise of that issuer or DB administrator is outside these RLS tests. PostgreSQL FK/unique violations may reveal existence through error timing/details; future APIs need safe error translation. RLS does not replace capability checks on future mutations. No claims about accept/revoke race ordering, invitation delivery, audit append-only storage, Live contact gates or production readiness follow from this foundation.

## Work evidence

See [S0-07 handoff](../../docs/S0_07_HANDOFF.md) for verified commit, actual PostgreSQL CI, rollback/ORM results, independent review limitations and open findings. Draft PR #11 remains experimental; no historical or product gate is cleared.

## S0-07B configuration and evidence

Without `CAC_EXPERIMENTAL_DISPOSABLE=1`, a missing/empty `CAC_DJANGO_SECRET` now refuses settings import. The synthetic fallback is only for explicitly disposable tests. Future functions created by `cac_owner` have no PUBLIC EXECUTE by default in any schema of that database; grants must be explicit. Bootstrap is fresh-database-only, not an upgrade of existing environments.

[Hardening handoff](../../docs/S0_07B_HANDOFF.md) supersedes the three S0-07 regression/default-privilege findings. CI also runs `python scripts/regression_sensitivity.py` in the disposable service: it temporarily weakens three controls, requires targeted assertion failures, restores catalog definitions in `finally`, then runs the full suite and rollback/reapply. Never use this harness against an existing or production database. Startup subprocess tests are configuration-only; security/ACL tests use actual PostgreSQL, not SQLite or mocks.
