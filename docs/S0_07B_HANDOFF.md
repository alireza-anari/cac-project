# S0-07B — experimental security hardening receipt

**CAC-NEW-ORIGIN-S0-07 / NEW_IMPLEMENTATION_EXPERIMENTAL**

Repository: https://github.com/alireza-anari/cac-project. Continue branch `work/s0-07-new-origin-backend-foundation`, Draft PR #11, execution #12. Architecture #9 permits experimentation only; canonical baseline/merge not approved. SOURCE-001 and GATE-SOURCE remain BLOCKED. APR-033/034/035/036 unchanged.

## Source and exact evidence

- Starting head: `ba8a2d8ce0aa0dc825b2a55c02f7f6d5c9278e16`.
- Test-first head: `d800e5cc293803a9ea60dd9b36e9d7dd533a5a31`; [RED CI](https://github.com/alireza-anari/cac-project/actions/runs/40924525920).
- Implementation head: **`6b6474480b63293807a328b404ce7e599bf2cd53`**; [GREEN CI](https://github.com/alireza-anari/cac-project/actions/runs/40924821282), job 123627387700, success.
- The final handoff commit changes documentation only after that implementation and incorporates main `75fb67256bb891ae12c38f6178b0c534007146a9` (Management review documents). The Source Registry append conflict was resolved by retaining both Work and Management records; no main source was overwritten. The exact final branch head, push run and PR synthetic-merge commit/run are recorded in the [final-head receipt in Issue #12](https://github.com/alireza-anari/cac-project/issues/12) and [Draft PR #11](https://github.com/alireza-anari/cac-project/pull/11) after they complete. This avoids claiming a document contains its own enclosing commit SHA.
- [Committed RED/GREEN excerpts](evidence/s0-07/s007b-excerpts.log); [full GREEN job](https://github.com/alireza-anari/cac-project/actions/runs/40924821282/job/123627387700); [19-file evidence ZIP](https://github.com/alireza-anari/cac-project/actions/runs/40924821282/artifacts/12920246469).
- Actions-reported evidence ZIP SHA-256: `b3d77f410a72dd458fe564acc61a299903db28f68194322b89c7a007d5646cd6`. ZIP not independently downloaded/rehashed. It is test evidence, not a historical source archive. Logs/artifacts retained 30 days; selected excerpts are committed.

## Changes and test coverage

| Gap | Correction / proof | Status at implementation head |
|---|---|---|
| S007-REV-02: indirect membership test | New actual scoped-grant INSERT by provisioner P1 targets P2 membership in same tenant/store. P1 own-membership positive control succeeds then rolls back; P2 attempt raises 42501 and admin query verifies no grant persisted. Existing test retained. | PASS |
| S007-REV-01: malformed signed context | Missing and null for all seven mandatory fields; invalid UUIDs/wrong types; malformed expiry/tx/pid; invalid tx=0, pid=-1 and overflowing expiry. Every case is signed with the synthetic issuer and executed via both actual runtime/provisioner logins; asserts SQLSTATE 42501 and generic `Invalid request context`. | PASS |
| Maximum TTL | Signed expiry +600 seconds rejected; server-time +299 seconds accepted for both roles; existing expired-context tests retained. | PASS |
| PUBLIC verifier permission | ACL inspection plus transactional unprivileged probe role with schema USAGE; EXECUTE denied specifically at function permission. Probe uses SET LOCAL ROLE; runtime/provisioner tests use actual separate logins. | PASS |
| S007-SEC-03: future function defaults | Global default EXECUTE revoke for creator cac_owner in this database, all schemas. Fresh owner-created function has no PUBLIC EXECUTE and cannot be called by runtime/provisioner absent an explicit grant. Current verifier keeps explicit grants. | PASS |
| Django static fallback | Missing/empty CAC_DJANGO_SECRET refuses settings import unless disposable flag equals exactly `1`. Subprocess tests cover missing/empty key, false/nonexact flags, explicit disposable mode, explicit synthetic key. | PASS |

**43 distinct tests:** original 32 + 7 PostgreSQL hardening tests + 4 isolated configuration tests. Full suite runs twice: **43 PASS / 0 FAIL / 0 ERROR / 0 SKIPPED per run**, exit 0. The context matrix exercises 108 invalid role/case combinations inside subtests, not 108 additional unittest methods. Configuration subprocess tests do not query a database and are not presented as PostgreSQL evidence. Fixture setup, FK isolation checks, ACL introspection and mutation orchestration necessarily use the disposable administrator/owner; application authorization tests use actual nonowner logins. No SQLite or mocked DB is used.

RED test-first CI ran 43 tests before fixes: future-function PUBLIC ACL assertion failed plus missing/empty-secret startup assertions (6 failure records including four flag subtests; no setup errors). The two intended weaknesses were thereby reproduced. Initial malformed-context/grant tests already passed against existing controls.

To prove sensitivity of those already-correct controls, `scripts/regression_sensitivity.py` temporarily (1) relaxes grant INSERT policy, (2) substitutes a verifier missing mandatory-claim validation, (3) increases allowed TTL. For each mutation a targeted regression must exit 1 with assertion FAIL and no ERROR. All three were detected. Each original catalog definition is restored in finally; the full green suite then runs. This script refuses non-disposable flag/database name and is only used in a new isolated CI service. Initial before-0002 RLS RED remains intact and is separately expected.

## Commands, environment and migration evidence

From `experimental/backend`, with `PYTHONPATH=.` and disposable config initialized as documented in README:

| Command | Exit / result |
|---|---|
| `python -m pip install --only-binary=:all: --require-hashes -r requirements.lock` | 0; locked install |
| `python scripts/bootstrap.py` | 0; new isolated roles/schema |
| `python manage.py migrate foundation 0001 --noinput` | 0 |
| `python -m unittest tests.test_security.SecurityTests.test_actual_nonowner_roles_and_force_rls -v` | 1 expected before security migration |
| `python manage.py migrate --noinput` | 0 |
| `python manage.py check` | 0; no issues |
| `python manage.py makemigrations --check --dry-run` | 0; no changes |
| `python manage.py showmigrations --plan` | 0; 0001 -> 0002 |
| `python scripts/regression_sensitivity.py` | 0; three targeted subprocesses each expected exit 1, all controls restored |
| `python -m unittest discover -s tests -p 'test_*.py' -v` | 0; 43 successful, before rollback |
| `python scripts/roundtrip.py` | 0; rollback to zero, removal verified, reapply identical structure/policies/ACL/owners/functions |
| Same complete unittest command after reapply | 0; 43 successful |
| `CAC_DB_ROLE=cac_runtime python scripts/orm_smoke.py` | 0; actual nonowner Django ORM |

Actual server: **PostgreSQL 17.11 (Debian 17.11-1.pgdg12+2), x86_64, gcc 12.2.0**, digest-pinned service. Python 3.12.15, Django 5.2.18, psycopg/binary 3.3.6, Ubuntu 24.04. Dependency lock/action/image pins unchanged. Local Python 3.12.14 settings-only tests: RED exit 1, after fix all four PASS exit 0. Local PostgreSQL unavailable; DB evidence is CI execution. Initial local test-file write used an incorrect relative path and ran zero tests (exit 5); corrected before any test result was claimed.

## File diff / compatibility

Changed implementation: `experimental/backend/config/settings.py`, `experimental/backend/sql/roles.sql`, `.github/workflows/experimental-backend.yml`.
Added tests/harness: `experimental/backend/tests/test_hardening.py`, `experimental/backend/tests/test_settings.py`, `experimental/backend/scripts/regression_sensitivity.py`.
Documentation: this handoff, RED/GREEN excerpts, updates to `docs/S0_07_HANDOFF.md`, backend README and contract inventory. No file deleted. No models, migration files, HTTP API, capability meaning, RLS policy or verifier implementation changed by this mission.

Default privilege fix applies only to **future functions created by cac_owner in the current database**, across its schemas; not to other owners/databases or existing functions. Fresh bootstrap refuses existing schemas; no automatic upgrade/migration of prior environments is claimed. Function probe cleanup runs in finally. Rollback test destroys disposable fixtures, not a product data-preserving rollback. Secret configuration change enforces existing explicit-test-only scope; no product/API/schema CR is introduced. Original CR-S0-07-001 remains proposed for baseline acceptance.

## Residual risks / gates

The three named test/default-privilege findings are closed by the linked evidence; the new fail-closed configuration requirement is met. This is not a new independent security certification. Existing issuer/key custody/rotation, real identity, MFA/CSRF/session revocation, pool integration, provisioning/audit and onboarding accept/revoke race contracts remain unresolved and unimplemented. A valid provided Django key does not make the experiment deployment-ready. Trusted issuer/admin compromise is outside the current RLS proof. FK/unique error side-channel mitigation for future API remains open. No onboarding module connected, no public endpoint, provider call, production data or credential used.

Experimental regression/rollback/configuration gates: PASS at the implementation commit; final-head receipts must confirm push and PR CI. Canonical baseline/merge: BLOCKED by #9 review. Historical SOURCE-001/GATE-SOURCE: BLOCKED. Production authorization and Sprint 0 completion: not granted. Issue #12 is updated for Management review, not used to close historical or architecture gates.
