"""Compare real PostgreSQL catalog objects before and after migration reversal."""
import json
import os
from pathlib import Path
import subprocess
import sys

import psycopg

cfg = json.loads(Path(os.environ["CAC_TEST_CONFIG"]).read_text())
if (os.environ.get("CAC_EXPERIMENTAL_DISPOSABLE") != "1" or cfg["connection"]["dbname"] != "cac_s007_test"
        or cfg["connection"]["host"] not in ("127.0.0.1", "localhost", "::1")):
    raise SystemExit("Local disposable database required")


def observe():
    return psycopg.connect(**cfg["connection"], user="postgres", password=cfg["passwords"]["postgres"])


def snapshot():
    queries = {
        "relation": "SELECT relrowsecurity,relforcerowsecurity,relacl::text,pg_get_userbyid(relowner) "
                    "FROM pg_class WHERE oid='catalog_lab.product'::regclass",
        "columns": "SELECT column_name,data_type,is_nullable,column_default,character_maximum_length "
                   "FROM information_schema.columns WHERE table_schema='catalog_lab' AND table_name='product' ORDER BY ordinal_position",
        "grants": "SELECT grantee,column_name,privilege_type FROM information_schema.column_privileges "
                  "WHERE table_schema='catalog_lab' AND table_name='product' ORDER BY 1,2,3",
        "constraints": "SELECT conname,pg_get_constraintdef(oid) FROM pg_constraint "
                       "WHERE conrelid='catalog_lab.product'::regclass ORDER BY 1",
        "policies": "SELECT policyname,roles,cmd,qual,with_check FROM pg_policies "
                    "WHERE schemaname='catalog_lab' AND tablename='product' ORDER BY 1",
        "verifier": "SELECT pg_get_functiondef(oid),proacl::text FROM pg_proc "
                    "WHERE oid='catalog_lab.allowed(uuid,uuid,boolean)'::regprocedure",
        "roles": "SELECT rolname,rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolinherit,rolreplication "
                 "FROM pg_roles WHERE rolname IN ('cac_catalog','cac_runtime','cac_provisioner') ORDER BY 1",
        "schema_grants": "SELECT nspname,nspacl::text FROM pg_namespace "
                         "WHERE nspname IN ('catalog_lab','cac_private','foundation') ORDER BY 1",
    }
    with observe() as conn:
        return {key: conn.execute(query).fetchall() for key, query in queries.items()}


def manage(*args):
    subprocess.run([sys.executable, "manage.py", *args, "--noinput"], check=True)


before = snapshot()
manage("migrate", "catalog_lab", "zero")
with observe() as conn:
    assert conn.execute("SELECT to_regclass('catalog_lab.product'), to_regclass('cac_private.catalog_key'), "
                        "to_regprocedure('catalog_lab.allowed(uuid,uuid,boolean)')").fetchone() == (None, None, None)
    assert conn.execute("SELECT to_regclass('foundation.store') IS NOT NULL").fetchone() == (True,)
manage("migrate", "catalog_lab")
assert snapshot() == before, "Catalog schema/RLS/ACL changed after rollback and reapply"
Path(os.environ["CATALOG_EVIDENCE"], "inventory.json").write_text(json.dumps(before, indent=2) + "\n")
print("Catalog rollback and reapply match schema, constraints, RLS, verifier and grants")
