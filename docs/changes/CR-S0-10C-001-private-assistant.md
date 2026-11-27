# CR-S0-10C-001 · Private assistant configuration and catalog lookup

Status **PROPOSED** · NEW_IMPLEMENTATION_EXPERIMENTAL · synthetic disposable PostgreSQL only. See [Issue #59](https://github.com/alireza-anari/cac-project/issues/59).

The new `catalog_lab.private_assistant` relation stores a UUID, a composite tenant/store reference to `foundation.store`, a display name and greeting. Unique tenant/store is a finite lab choice. The assistant has its own identity, so a later separately approved migration can reconsider multiplicity. This proposal does not implement public Live state or APR-034 enforcement.

The new settings module `config.assistant_settings` adds only the `private_assistant` app to the inherited disposable configuration. New policies reuse the existing signed catalog scope and verifier. The catalog role may read and insert scoped rows and has column-level update on display name and greeting. The update and insert policies require manage scope. Catalog queries run under a fresh signed read scope through the inherited product service. Name and SKU lookups use case-folded exact equality and return a product only for one match. Missing or ambiguous inquiries have fixed fallbacks.

## Local walkthrough

Use a fresh disposable PostgreSQL 17 instance on loopback with database `cac_s007_test` and an administrative bootstrap login. From `experimental/backend`, run the following in Bash with `PGPASSWORD` already supplied through the local session. The walkthrough seeds and clears synthetic fixtures and must use a disposable database.

```bash
export PGHOST=127.0.0.1 PGPORT=5432 PGDATABASE=cac_s007_test
export CAC_EXPERIMENTAL_DISPOSABLE=1 CAC_DB_ROLE=cac_owner PYTHONPATH=.
fixture_dir=$(mktemp -d)
trap 'rm -f "$fixture_dir/foundation.json" "$fixture_dir/catalog.json"; rmdir "$fixture_dir"' EXIT
export CAC_TEST_CONFIG="$fixture_dir/foundation.json" CAC_CATALOG_CONFIG="$fixture_dir/catalog.json"
python -m pip install --only-binary=:all: --require-hashes -r requirements.lock
python scripts/bootstrap.py
python manage.py migrate --noinput
python scripts/catalog_bootstrap.py role
DJANGO_SETTINGS_MODULE=config.catalog_settings python manage.py migrate --noinput
python scripts/catalog_bootstrap.py key
DJANGO_SETTINGS_MODULE=config.assistant_settings python manage.py migrate --noinput
CAC_CATALOG_LOGIN=1 DJANGO_SETTINGS_MODULE=config.assistant_settings python -m unittest -v \
  assistant_tests.test_assistant.AssistantContract.test_walkthrough_committed_create_rename_and_delete
```

The walkthrough configures the assistant, commits a product through the inherited service, asks by name, commits a rename, asks by the new name and SKU, then commits a deletion and verifies the deleted SKU is missing. It also demonstrates ambiguous names. A separate observer reads both tables between operations.

## Frozen matrix

| Group | Distinct methods | Evidence |
| --- | ---: | --- |
| Inherited foundation | 43 | Verbatim existing suite, before catalog migration |
| Inherited catalog | 8 | Verbatim existing suite, before assistant migration |
| Private assistant | 5 | Settings readback, read scope, cross-scope, schema and scope denials, committed catalog walkthrough |
| Migration and evidence | — | Apply/reverse/reapply, inherited inventory equality, model check, evidence allowlist and synthetic credential scan |

The dedicated workflow runs this matrix on the branch push and the stacked pull request. The inherited S0-10B workflow may also run on the pull request and enforces its own exact S0-07B target. Its workflow and tests are preserved as supplied.

Out of scope are real authentication, individual shopper access, immediate in-flight revocation, grant-check/issuance atomicity, global write guarantees, historical compatibility, SKU update coverage, price and inventory, real customer data, previews, UI/HTTP, external AI, Woo, Live, billing, deployment and egress. The work makes no release or management gate decision.
