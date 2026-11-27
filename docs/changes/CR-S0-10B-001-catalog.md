# CR-S0-10B-001 · Proposed synthetic catalog contract

Status **PROPOSED**. Source identity **NEW_IMPLEMENTATION_EXPERIMENTAL**. Issue #57 authorizes this isolated implementation on the exact S0-07B base. Architecture #9 and the source gates remain open. Historical compatibility is unknown.

A store can create, list, rename, and delete products identified by a store-local SKU. Catalog rows have a UUID, tenant UUID, store UUID, SKU and name. PostgreSQL enforces a composite tenant/store foreign key, SKU uniqueness per scope, SKU format and nonblank name. Stock, pricing, customer data and public surfaces are outside this slice.

- A separate disposable `cac_catalog` login has SELECT, INSERT, DELETE and UPDATE of SKU/name only on the catalog table. ENABLE and FORCE RLS use a separate catalog-only HMAC verifier owned by `cac_owner`. The verifier has a fixed search path and explicit grants. Catalog scope and product ID cannot be updated.
- A test-only trusted issuer uses the existing signed, nonowner foundation read path to derive access from active membership plus `store.view`, with `store.manage` required for writes. A short-lived catalog token binds principal, purpose, scope, tenant, store, backend PID and transaction ID. Independent keys prevent reuse of a foundation token for catalog access. The caller is trusted fixture code and must choose the synthetic principal. Authorization is evaluated when issuing a fresh token. Immediate invalidation during an already-issued transaction or between the foundation check and issuance is unproven.
- The catalog settings module opts into the new app. Bootstrap adds one role and an empty schema. The migration creates the Product table and catalog verifier/key table. Migrating catalog to zero removes those three objects and leaves the bootstrap scaffold. The inherited settings, role SQL, verifier, migrations, policies and tests remain unchanged.
- Real authentication, MFA/CSRF, invitations and live membership administration are outside the lab. The trusted fixture, migration owner and disposable administrator are outside the application-role threat boundary. The lab does not use the P guard and does not establish independent authority, real issuer custody, Production compatibility or the historical onboarding race gates.

## Reproduce locally with disposable PostgreSQL

Run from `experimental/backend` in a POSIX shell with the pinned Python environment and a fresh local PostgreSQL 17 service named `cac_s007_test`. The commands create disposable roles and schemas. Do not point them at an existing application database. Set `PGPASSWORD` to the disposable PostgreSQL admin password through your local environment.

```bash
set -euo pipefail
export CAC_EXPERIMENTAL_DISPOSABLE=1 PGDATABASE=cac_s007_test PGHOST=127.0.0.1 PGPORT=5432
export CAC_DB_ROLE=cac_owner PYTHONPATH=.
private_dir="$(mktemp -d)"
trap 'rm -f "$private_dir/foundation.json" "$private_dir/catalog.json"; rmdir "$private_dir"' EXIT
export CAC_TEST_CONFIG="$private_dir/foundation.json"
export CAC_CATALOG_CONFIG="$private_dir/catalog.json"
export CATALOG_EVIDENCE="$(mktemp -d)"
python -m pip install --only-binary=:all: --require-hashes -r requirements.lock
python scripts/bootstrap.py
python manage.py migrate --noinput
python -m unittest discover -s tests -p 'test_*.py' -v
export DJANGO_SETTINGS_MODULE=config.catalog_settings
python scripts/catalog_bootstrap.py role
python manage.py migrate --noinput
python manage.py check
python manage.py makemigrations --check --dry-run
python scripts/catalog_roundtrip.py
python scripts/catalog_bootstrap.py key
CAC_CATALOG_LOGIN=1 python -m unittest catalog_tests.test_catalog -v -f
python scripts/catalog_scan.py
```

Run only the CRUD walkthrough with `CAC_CATALOG_LOGIN=1 python -m unittest catalog_tests.test_catalog.CatalogContract.test_own_store_committed_crud_independent_readback -v`. The test seeds three stores across two tenants under disposable test setup. Product CRUD and adverse statements execute using the real nonowner catalog login. Fresh signed read transactions and an independent read-only database observer verify committed values and no-effect cases. The mismatched composite FK control uses a deliberately invalid trusted fixture claim solely to reach the constraint under the nonowner role.

## Frozen acceptance

Eight new native test methods cover committed own-store CRUD and independent readback, same-tenant cross-store and cross-tenant read/write isolation, read-only/downgraded/inactive/other-principal authorization, missing and invalid signatures/claims, replay across transactions, composite FK/format/uniqueness/immutability constraints, rollback, and real role/ACL/RLS checks. The inherited cohort has 43 distinct methods. Each final Push and PR runs the fixed catalog suite once. The scoped workflow compares inherited source bytes and synthetic merge tree, rolls catalog migration back and reapplies it, and scans the allowlisted evidence. Actual results and review links go in Issue #57 so they can reference the exact tested SHA.
