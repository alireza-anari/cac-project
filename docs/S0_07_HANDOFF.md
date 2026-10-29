# S0-07 — Work handoff to Astra Management

**NEW_IMPLEMENTATION_EXPERIMENTAL — CAC-NEW-ORIGIN-S0-07**

This is a new, isolated Django/PostgreSQL implementation. It is not recovered v3.37/v3.38/v3.39, not an approved baseline, and not a product release. SOURCE-001 / GATE-SOURCE remain **BLOCKED**. APR-033/034/035/036 are unchanged. Issue [#9](https://github.com/alireza-anari/cac-project/issues/9) requires Architecture decision; execution is tracked by [#10](https://github.com/alireza-anari/cac-project/issues/10).

## GitHub / source identity

- Repository: https://github.com/alireza-anari/cac-project
- Base main inspected: `025931e0a612ff95c8165dec7c82af0d922b181a`.
- Branch: `work/s0-07-new-origin-backend-foundation`.
- Draft PR: https://github.com/alireza-anari/cac-project/pull/11 — leave draft, no automatic merge.
- Verified implementation commit: `741ee42471fea8c7a7a8780305eddcaeb9f72d31`.
- [Exact implementation diff](https://github.com/alireza-anari/cac-project/compare/025931e0a612ff95c8165dec7c82af0d922b181a...741ee42471fea8c7a7a8780305eddcaeb9f72d31).
- This handoff and source-registry annotation are later documentation changes. Final branch head and its CI are recorded in the PR; a file cannot contain its own commit SHA.
- No original archive imported; no claim of SHA equivalence to historic sources. Source identity is the Git commit. CI evidence archive digest below is an evidence ZIP, not a source archive.

## Structure and contract diff

Added `experimental/backend/` contains Django config, models, migrations, role/RLS SQL, test scripts, hash-locked requirements, README and proposed contract inventory. Added `.github/workflows/experimental-backend.yml`, execution plan and evidence. Modified `.gitignore` to exclude private test config; appended source registry. No existing source files deleted or historical migrations rewritten.

Schema: four new experimental tables (Tenant, Store, Membership, ScopedGrant), three composite FKs, scoped uniqueness/check constraints, four ENABLE/FORCE RLS tables, ten policies, private context-key table and one signed-context verifier. These are **PROPOSED**, not a diff against unavailable historical schema. Migration graph: `foundation.0001_initial -> foundation.0002_security`; role/schema bootstrap precedes Django migrations.

Runtime is a nonowner SELECT-only login. Provisioner has scoped SELECT/INSERT, no UPDATE/DELETE/DDL/role escalation. Migration owner is separate; all three lack superuser/BYPASSRLS. Signed transaction-local context binds tenant/store/principal, role purpose, expiry, transaction ID and backend PID. Test issuer/key are synthetic; no production identity boundary is implemented.

API: no HTTP endpoints, DRF, admin, onboarding integration or public Live behavior added. Internal DB/context interface is new and proposed. See [CR-S0-07-001 / contract inventory](../experimental/backend/docs/CONTRACT_INVENTORY.md) for schema/context decisions and Architecture acceptance criteria.

## Actual validation

[Successful push CI run 40921536251](https://github.com/alireza-anari/cac-project/actions/runs/40921536251), job `123615780247`, tested exact commit `741ee42471fea8c7a7a8780305eddcaeb9f72d31`; conclusion **success**. This is actual disposable PostgreSQL execution, not SQLite.

Environment: Ubuntu 24.04 hosted runner; Python 3.12.15, Django 5.2.18 LTS, psycopg + binary 3.3.6, PostgreSQL 17.11 (Debian 17.11-1.pgdg12+2). Hash-locked transitive wheels: asgiref 3.13.0, sqlparse 0.6.0, typing-extensions 4.16.0, pip 26.2.2. Exact dependency hashes: `experimental/backend/requirements.lock`. Official PostgreSQL manifest digest: `sha256:839fbb5a4942a7758dd93e18b42ea5649807491a0545b5eeeb8f0b8bb11857a5`. Action SHAs are fixed in the workflow; token permissions contents:read, checkout credentials not persisted.

Commands below run from `experimental/backend`, with `PYTHONPATH=.` and fresh disposable config created by `scripts/bootstrap.py`; complete environment setup is in its README/workflow.

| Command/check | Actual result | Exit |
|---|---|---|
| `python -m pip install --only-binary=:all: --require-hashes -r requirements.lock` | Installed locked wheels | 0 |
| `python scripts/bootstrap.py` | Fresh roles/schema/synthetic keys | 0 |
| `python manage.py migrate foundation 0001 --noinput` | Initial schema applied | 0 |
| `python -m unittest tests.test_security.SecurityTests.test_actual_nonowner_roles_and_force_rls -v` before 0002 | Expected RED: 1 failure due to absent ENABLE/FORCE RLS; workflow requires this exact failure | 1 (expected) |
| `python manage.py migrate --noinput` | 0002 applied | 0 |
| `python manage.py check` | No issues | 0 |
| `python manage.py makemigrations --check --dry-run` | No changes detected | 0 |
| `python manage.py showmigrations --plan` | 0001 -> 0002 applied | 0 |
| `python -m unittest discover -s tests -p 'test_*.py' -v` | 32 PASS / 0 FAIL / 0 ERROR / 0 SKIPPED before rollback | 0 |
| `python scripts/roundtrip.py` | Migrate to zero, assert tables/function removed, reapply; schema/policies/ACL/owners/functions equivalent | 0 |
| Same unittest command after roundtrip | 32 PASS / 0 FAIL / 0 ERROR / 0 SKIPPED | 0 |
| `CAC_DB_ROLE=cac_runtime python scripts/orm_smoke.py` | Actual nonowner Django ORM returns only authorized scope | 0 |

There are **32 unique security tests**, executed twice (64 successful executions); not 64 distinct tests. Two Tenant / three Store synthetic fixtures cover isolation, active membership/capability, missing/forged/expired/replayed context, independent connections, role/DDL/key denial, composite-FK rejection and rollback. The expected RED is reported separately. No accept/revoke race, real authentication, MFA/CSRF or production test is claimed.

Local Python 3.12.14 virtualenv installation and `manage.py check` also passed, exit 0 ([local log](evidence/s0-07/local-check.log)). Local PostgreSQL/docker executables were unavailable; all database results above are from CI.

Evidence: [sanitized log excerpts](evidence/s0-07/ci-40921536251-excerpts.log), [full job](https://github.com/alireza-anari/cac-project/actions/runs/40921536251/job/123615780247), [18-file evidence artifact](https://github.com/alireza-anari/cac-project/actions/runs/40921536251/artifacts/12918556691). Uploaded artifact SHA-256 reported by Actions: `b17b6d602688cb863d5b112d9669a44ba3ddf6333d7606acedd2bf5e63ec0397`. Binary ZIP not downloaded/rehashed here. Artifact includes environment/libpq version, graph, structural snapshot, command logs and exit-code files; retention 30 days. Private generated passwords/signing key/config are excluded by explicit upload allowlist and removed in an always-run cleanup step.

Observed failures preserved for traceability: run 40817238531 rejected YAML colon syntax; 40817460699 exposed PL/pgSQL purpose-condition syntax; 40817634657 ran 32 tests with 31 success and one fixture conflict (`23505` uniqueness instead of expected `23503` FK). Fixed YAML scalar, explicit NULL-safe boolean purpose condition, and used a nonduplicate capability in the FK fixture. Expected FK SQLSTATE was not weakened. Run 40921536251 then passed all stages.

## Independent review and residual risks

An independent read-only code-review agent reviewed the initial implementation, parsed 14 Python files and inspected 32 test definitions. It reported no Critical/Important defect found; it did **not** execute PostgreSQL or validate CI, and its review preceded the syntax/fixture fixes. It is an AI-assisted code review, not external security certification. Actual CI evidence above is separate.

| ID | Severity / status | Finding, impact, mitigation / owner |
|---|---|---|
| S007-REV-01 | Minor / OPEN | Signed invalid mandatory-claim variants and >300-second TTL lack exhaustive direct regression cases. Existing verifier rejects malformed fields; Work should extend the matrix before baseline acceptance. |
| S007-REV-02 | Minor / OPEN | Different-principal provisioner test directly tests membership INSERT, not grant INSERT targeting another principal's same-store membership. Policy inspection found the membership filter, but Work should add that exact regression. |
| S007-SEC-01 | High if promoted / BLOCKED | Real identity issuer, key custody/rotation, MFA/CSRF, session/revocation and connection-pool integration absent. Architecture/security must decide and test before product integration. Synthetic issuer is not an authentication system. |
| S007-SEC-02 | Medium / OPEN | FK/unique errors may leak existence. Future API must translate errors; no API currently exposed. |
| S007-SEC-03 | Low / OPEN | Schema-specific default function-EXECUTE revoke does not by itself remove global PUBLIC defaults. Current verifier explicitly revokes PUBLIC and schemas restrict access; globally harden defaults and test future functions before expansion. |
| S007-INT-01 | BLOCKED | Onboarding accept/revoke concurrency, atomic/idempotent provisioning service, append-only audit and real identity integration unimplemented. No standalone onboarding connected. |
| SOURCE-001 | BLOCKED | Authentic v3.37/38/39 bytes/approved commit unavailable. Management supplies provenance-backed source; new implementation does not resolve it. |

No customer data, real credentials or provider calls are included. Test bootstrap administrator can seed/bypass RLS by design; application tests use actual separate nonowner logins. Compromise of the trusted issuer/DB administrator and production timing/performance/load are outside this proof. Empty tables may return empty results without evaluating context; no unauthorized rows are returned, and no claim that every contextless SELECT raises is made. Rollback destroys only fresh experimental fixtures; it is not data-preserving product rollback.

## Gate decisions and next actions

- Experimental clean install, nonowner PostgreSQL isolation, scoped constraints, transaction-local context, migration rollback/reapply, Django ORM: **PASS at the verified commit**, with CI evidence above.
- Historical SOURCE-001 / GATE-SOURCE: **BLOCKED**.
- Architecture/baseline promotion (#9), product integration/release: **BLOCKED**; Draft PR is not approval.
- Real identity/MFA/CSRF, onboarding accept/revoke concurrency, production: **NOT EXECUTED / out of current experiment**.

1. P0 — CAC Architecture decide #9 and CR-S0-07-001 before canonical baseline or merge.
2. P0 — Security/Work review signed-issuer trust/key model and close exact regression gaps; depends on agreed threat model.
3. P1 — Work design authenticated transaction/pool boundary and provisioning/audit contracts; depends on Architecture decisions. Keep onboarding disconnected until identity and concurrency review.
4. P1 — Work execute real PostgreSQL accept/revoke race scenarios only after a reviewed integration contract exists; present foundation does not cover those operations.
5. P0 parallel — Management supply authentic historical archives/commit provenance for SOURCE-001; do not relabel this source as recovered history.
