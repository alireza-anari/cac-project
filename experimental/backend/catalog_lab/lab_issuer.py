"""Trusted synthetic issuer. Keep both credential files outside the repository."""
import hashlib
import hmac
import json
import os
from pathlib import Path
from uuid import UUID

from django.db import connection, transaction
import psycopg


def _config(name):
    if os.environ.get("CAC_EXPERIMENTAL_DISPOSABLE") != "1":
        raise RuntimeError("Disposable mode required")
    return json.loads(Path(os.environ[name]).read_text())


def _signed(claims, key):
    payload = json.dumps(claims, sort_keys=True, separators=(",", ":")).encode()
    return payload.hex() + "." + hmac.new(bytes.fromhex(key), payload, hashlib.sha256).hexdigest()


def _claims(cursor, tenant, store, principal, purpose):
    cursor.execute("SELECT txid_current()::text, pg_backend_pid(), floor(extract(epoch FROM statement_timestamp()))::bigint")
    xid, pid, now = cursor.fetchone()
    return dict(tenant=str(UUID(str(tenant))), store=str(UUID(str(store))), principal=str(UUID(str(principal))),
                purpose=purpose, tx=xid, pid=pid, expires=now + 45)


def _scope(foundation, tenant, store, principal):
    db = foundation["connection"]
    if db["dbname"] != "cac_s007_test" or db["host"] not in ("127.0.0.1", "localhost", "::1"):
        raise RuntimeError("Local disposable database required")
    with psycopg.connect(**db, user="cac_runtime", password=foundation["passwords"]["cac_runtime"]) as check:
        with check.cursor() as cursor:
            claims = _claims(cursor, tenant, store, principal, "runtime")
            cursor.execute("SELECT set_config('cac.context', %s, true)", (_signed(claims, foundation["issuer_key"]),))
            cursor.execute("SELECT capability FROM foundation.scoped_grant")
            capabilities = {row[0] for row in cursor.fetchall()}
    if "store.view" not in capabilities:
        raise PermissionError("Active store view grant required")
    return "manage" if "store.manage" in capabilities else "read"


@transaction.atomic(durable=True)
def run(tenant, store, principal, operation, *, read_only=False):
    """Run one synthetic, issuer-authorized catalog operation with a fresh scope."""
    if connection.settings_dict["USER"] != "cac_catalog":
        raise RuntimeError("Catalog login required")
    foundation = _config("CAC_TEST_CONFIG")
    scope = _scope(foundation, tenant, store, principal)
    private = _config("CAC_CATALOG_CONFIG")
    with connection.cursor() as cursor:
        claims = _claims(cursor, tenant, store, principal, "cac.catalog.lab.v1")
        claims["scope"] = "read" if read_only else scope
        cursor.execute("SELECT set_config('cac.catalog_context', %s, true)", (_signed(claims, private["issuer_key"]),))
    return operation()

