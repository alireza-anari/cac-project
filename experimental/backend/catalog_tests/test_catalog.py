"""Fixed disposable PostgreSQL acceptance cases. Product operations use cac_catalog."""
from contextlib import contextmanager
import os
import json
import unittest
from uuid import UUID, uuid4

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.catalog_settings")
import django
django.setup()

from django.db import DatabaseError, connection, transaction
import psycopg

from catalog_lab import lab_issuer, service
from catalog_lab.models import Product

T1, T2, S1, S2, S3, P1, P2, M1, M2, M3 = [UUID(int=n) for n in range(81, 91)]
SCOPES = [(T1, S1, P1, M1), (T1, S2, P2, M2), (T2, S3, P2, M3)]
TABLE = "catalog_lab.product"


def fixture_connection(role="postgres"):
    cfg = lab_issuer._config("CAC_TEST_CONFIG")
    return psycopg.connect(**cfg["connection"], user=role, password=cfg["passwords"][role])


def run(t, s, p, operation, **kwargs):
    return lab_issuer.run(t, s, p, operation, **kwargs)


def sql(statement, values=()):
    with connection.cursor() as cursor:
        cursor.execute(statement, values)
        return cursor.fetchall() if cursor.description else cursor.rowcount


def raw_insert(t, s, sku="NEG", name="Synthetic"):
    return sql("INSERT INTO catalog_lab.product (id,tenant_id,store_id,sku,name) VALUES (%s,%s,%s,%s,%s)",
               (uuid4(), t, s, sku, name))


def read(t, s, p):
    return run(t, s, p, lambda: service.read_products(t, s), read_only=True)


def state():
    with fixture_connection() as observer:
        return observer.execute("SELECT id,tenant_id,store_id,sku,name FROM catalog_lab.product ORDER BY id").fetchall()


def controlled_token(t, s, p, **override):
    # For negative database tests only. The normal issuer derives scope from grants.
    with connection.cursor() as cursor:
        claims = lab_issuer._claims(cursor, t, s, p, "cac.catalog.lab.v1")
        claims.update(scope="manage", **override)
    return lab_issuer._signed(claims, lab_issuer._config("CAC_CATALOG_CONFIG")["issuer_key"])


def install(token):
    sql("SELECT set_config('cac.catalog_context', %s, true)", (token,))


class CatalogContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with fixture_connection() as setup:
            setup.execute("TRUNCATE catalog_lab.product, foundation.scoped_grant, "
                          "foundation.membership, foundation.store, foundation.tenant")
            for tenant in (T1, T2):
                setup.execute("INSERT INTO foundation.tenant (id,name) VALUES (%s,'Synthetic tenant')", (tenant,))
            for tenant, store, principal, member in SCOPES:
                setup.execute("INSERT INTO foundation.store (id,tenant_id,name) VALUES (%s,%s,'Synthetic store')",
                              (store, tenant))
                setup.execute("INSERT INTO foundation.membership (id,tenant_id,store_id,principal_id,active) "
                              "VALUES (%s,%s,%s,%s,true)", (member, tenant, store, principal))
                for capability in ("store.view", "store.manage"):
                    setup.execute("INSERT INTO foundation.scoped_grant "
                                  "(id,tenant_id,store_id,membership_id,capability) VALUES (%s,%s,%s,%s,%s)",
                                  (uuid4(), tenant, store, member, capability))

    def setUp(self):
        with fixture_connection() as setup:
            setup.execute("TRUNCATE catalog_lab.product")
        self.ids = {}
        for tenant, store, principal, _ in SCOPES:
            product = run(tenant, store, principal, lambda: service.create_product(
                tenant, store, sku="SEED", name="Synthetic seed"))
            self.ids[store] = product.pk
        self.assertEqual(len(state()), 3)

    def unchanged(self, before):
        self.assertEqual(state(), before, "CATALOG_DOMAIN_SUPPORTED_SECURITY_FAIL unexpected persisted effect")

    @contextmanager
    def db_denied(self, code="42501"):
        before = state()
        try:
            with self.assertRaises(DatabaseError, msg="Expected database denial") as error:
                yield
        except AssertionError:
            self.unchanged(before)
            raise AssertionError("CATALOG_DOMAIN_SUPPORTED_SECURITY_FAIL expected database denial did not occur") from None
        self.assertEqual(error.exception.__cause__.sqlstate, code)
        self.unchanged(before)

    def test_own_store_committed_crud_independent_readback(self):
        self.assertEqual(sql("SELECT session_user,current_user"), [("cac_catalog", "cac_catalog")])
        product = run(T1, S1, P1, lambda: service.create_product(T1, S1, sku="LAMP-1", name="Lamp"))
        self.assertIn(("LAMP-1", "Lamp"), read(T1, S1, P1))
        self.assertIn((product.pk, T1, S1, "LAMP-1", "Lamp"), state())
        self.assertEqual(run(T1, S1, P1, lambda: service.rename_product(T1, S1, product.pk, "Desk lamp")), 1)
        self.assertIn(("LAMP-1", "Desk lamp"), read(T1, S1, P1))
        self.assertIn((product.pk, T1, S1, "LAMP-1", "Desk lamp"), state())
        self.assertEqual(run(T1, S1, P1, lambda: service.delete_product(T1, S1, product.pk)), 1)
        self.assertEqual(read(T1, S1, P1), [("SEED", "Synthetic seed")])
        self.assertNotIn(product.pk, {x[0] for x in state()})

    def test_cross_store_and_tenant_read_and_mutations(self):
        for tenant, store, principal, _ in SCOPES[1:]:
            with self.subTest(store=store):
                self.assertEqual(read(tenant, store, principal), [("SEED", "Synthetic seed")])
                before = state()
                self.assertEqual(run(T1, S1, P1, lambda: service.read_products(tenant, store)), [],
                                 "CATALOG_DOMAIN_SUPPORTED_SECURITY_FAIL cross-scope read")
                self.assertEqual(run(T1, S1, P1, lambda: service.rename_product(tenant, store, self.ids[store], "Changed")), 0,
                                 "CATALOG_DOMAIN_SUPPORTED_SECURITY_FAIL cross-scope UPDATE")
                self.assertEqual(run(T1, S1, P1, lambda: service.delete_product(tenant, store, self.ids[store])), 0,
                                 "CATALOG_DOMAIN_SUPPORTED_SECURITY_FAIL cross-scope DELETE")
                with self.db_denied():
                    run(T1, S1, P1, lambda: raw_insert(tenant, store))
                self.unchanged(before)

    def test_read_scope_and_live_grant_changes(self):
        before = state()
        with self.db_denied():
            run(T1, S1, P1, lambda: raw_insert(T1, S1), read_only=True)
        with fixture_connection() as setup:
            setup.execute("DELETE FROM foundation.scoped_grant WHERE membership_id=%s AND capability='store.manage'", (M1,))
        try:
            self.assertEqual(read(T1, S1, P1), [("SEED", "Synthetic seed")])
            with self.db_denied():
                run(T1, S1, P1, lambda: raw_insert(T1, S1))
            self.assertEqual(run(T1, S1, P1, lambda: service.rename_product(T1, S1, self.ids[S1], "Changed")), 0)
            self.assertEqual(run(T1, S1, P1, lambda: service.delete_product(T1, S1, self.ids[S1])), 0)
            with fixture_connection() as setup:
                setup.execute("UPDATE foundation.membership SET active=false WHERE id=%s", (M1,))
            for principal in (P1, P2):
                with self.assertRaises(PermissionError):
                    run(T1, S1, principal, lambda: self.fail("CATALOG_DOMAIN_SUPPORTED_SECURITY_FAIL issuer accepted ineligible principal"))
        finally:
            with fixture_connection() as setup:
                setup.execute("UPDATE foundation.membership SET active=true WHERE id=%s", (M1,))
                setup.execute("INSERT INTO foundation.scoped_grant "
                              "(id,tenant_id,store_id,membership_id,capability) VALUES (%s,%s,%s,%s,'store.manage')",
                              (uuid4(), T1, S1, M1))
        with fixture_connection() as setup:
            setup.execute("DELETE FROM foundation.scoped_grant WHERE membership_id=%s AND capability='store.view'", (M1,))
        try:
            with self.assertRaises(PermissionError):
                run(T1, S1, P1, lambda: self.fail("CATALOG_DOMAIN_SUPPORTED_SECURITY_FAIL manage without view"))
        finally:
            with fixture_connection() as setup:
                setup.execute("INSERT INTO foundation.scoped_grant "
                              "(id,tenant_id,store_id,membership_id,capability) VALUES (%s,%s,%s,%s,'store.view')",
                              (uuid4(), T1, S1, M1))
        self.unchanged(before)

    def test_missing_bad_signature_purpose_and_expiry(self):
        for kind in ("missing", "unsigned", "tampered", "wrong-purpose", "expired", "too-long-lived",
                     "missing-principal", "bad-principal", "bad-scope", "wrong-pid", "wrong-xid", "foundation-key"):
            with self.subTest(kind=kind):
                for operation in (
                    lambda: sql("SELECT id FROM catalog_lab.product"),
                    lambda: raw_insert(T1, S1),
                    lambda: sql("UPDATE catalog_lab.product SET name='Invalid' WHERE id=%s", (self.ids[S1],)),
                    lambda: sql("DELETE FROM catalog_lab.product WHERE id=%s", (self.ids[S1],)),
                ):
                    with self.db_denied(), transaction.atomic():
                        token = controlled_token(T1, S1, P1)
                        if kind == "unsigned":
                            install('{"scope":"manage"}')
                        elif kind == "tampered":
                            install(token[:-1] + ("0" if token[-1] != "0" else "1"))
                        elif kind != "missing":
                            claims = json.loads(bytes.fromhex(token.split(".")[0]))
                            if kind == "missing-principal":
                                del claims["principal"]
                            elif kind == "too-long-lived":
                                claims["expires"] += 600
                            else:
                                claims.update({
                                    "wrong-purpose": {"purpose": "runtime"}, "expired": {"expires": 1},
                                    "bad-principal": {"principal": "bad"}, "bad-scope": {"scope": "admin"},
                                    "wrong-pid": {"pid": -1}, "wrong-xid": {"tx": "-1"},
                                    "foundation-key": {},
                                }[kind])
                            key_file = "CAC_TEST_CONFIG" if kind == "foundation-key" else "CAC_CATALOG_CONFIG"
                            install(lab_issuer._signed(claims, lab_issuer._config(key_file)["issuer_key"]))
                        operation()

    def test_context_replay_on_same_connection_new_transaction(self):
        with transaction.atomic():
            token = controlled_token(T1, S1, P1)
            original_pid = sql("SELECT pg_backend_pid()")[0][0]
            install(token)
            self.assertEqual(service.read_products(T1, S1), [("SEED", "Synthetic seed")])
        with self.db_denied(), transaction.atomic():
            self.assertEqual(sql("SELECT pg_backend_pid()")[0][0], original_pid)
            install(token)
            raw_insert(T1, S1)

    def test_composite_fk_and_constraints(self):
        with self.db_denied():
            run(T1, S1, P1, lambda: raw_insert(T1, S3))
        # Isolate the FK using a deliberately bad trusted-fixture claim under the real app login.
        with self.db_denied("23503"), transaction.atomic():
            install(controlled_token(T1, S3, P1))
            raw_insert(T1, S3)
        for sku, name, code in (("SEED", "Duplicate", "23505"), ("bad sku", "Name", "23514"), ("OK", "  ", "23514")):
            with self.subTest(sku=sku, name=name), self.db_denied(code):
                run(T1, S1, P1, lambda: raw_insert(T1, S1, sku, name))
        with self.db_denied():
            run(T1, S1, P1, lambda: sql("UPDATE catalog_lab.product SET store_id=%s WHERE id=%s", (S2, self.ids[S1])))
        self.assertEqual(read(T1, S1, P1), [("SEED", "Synthetic seed")])

    def test_rollback_does_not_persist_create_update_delete(self):
        before = state()

        def abort():
            service.create_product(T1, S1, sku="TEMP", name="Synthetic temporary")
            self.assertEqual(service.rename_product(T1, S1, self.ids[S1], "Uncommitted"), 1)
            self.assertEqual(service.delete_product(T1, S1, self.ids[S1]), 1)
            self.assertEqual(service.read_products(T1, S1), [("TEMP", "Synthetic temporary")])
            raise ValueError("Synthetic rollback")

        with self.assertRaisesRegex(ValueError, "Synthetic rollback"):
            run(T1, S1, P1, abort)
        self.unchanged(before)
        self.assertEqual(read(T1, S1, P1), [("SEED", "Synthetic seed")])

    def test_role_policy_inventory_and_direct_access_denials(self):
        before = state()
        with fixture_connection() as observer:
            self.assertEqual(observer.execute(
                "SELECT relrowsecurity,relforcerowsecurity,pg_get_userbyid(relowner) "
                "FROM pg_class WHERE oid='catalog_lab.product'::regclass").fetchone(), (True, True, "cac_owner"))
            self.assertEqual(observer.execute(
                "SELECT rolcanlogin,rolsuper,rolbypassrls,rolcreaterole,rolcreatedb,rolreplication,rolinherit "
                "FROM pg_roles WHERE rolname='cac_catalog'").fetchone(), (True, False, False, False, False, False, False))
            self.assertEqual(observer.execute(
                "SELECT count(*) FROM pg_auth_members WHERE member='cac_catalog'::regrole").fetchone(), (0,))
            self.assertEqual(observer.execute(
                "SELECT count(*) FROM pg_proc p CROSS JOIN LATERAL aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a "
                "WHERE p.oid='catalog_lab.allowed(uuid,uuid,boolean)'::regprocedure AND a.grantee=0").fetchone(), (0,))
            self.assertEqual(observer.execute(
                "SELECT policyname,cmd FROM pg_policies WHERE schemaname='catalog_lab' ORDER BY policyname").fetchall(),
                [("product_delete", "DELETE"), ("product_insert", "INSERT"), ("product_read", "SELECT"), ("product_update", "UPDATE")])
        for role in ("cac_runtime", "cac_provisioner"):
            for statement in ("SELECT id FROM catalog_lab.product", "DELETE FROM catalog_lab.product"):
                with self.subTest(role=role, statement=statement):
                    with fixture_connection(role) as conn, self.assertRaises(psycopg.errors.InsufficientPrivilege):
                        conn.execute(statement)
                    self.unchanged(before)
        for statement in ("SELECT secret FROM cac_private.catalog_key",
                          "SELECT id FROM foundation.store",
                          "TRUNCATE catalog_lab.product",
                          "ALTER TABLE catalog_lab.product DISABLE ROW LEVEL SECURITY",
                          "SET ROLE cac_owner"):
            with self.subTest(statement=statement), self.db_denied(), transaction.atomic():
                sql(statement)

