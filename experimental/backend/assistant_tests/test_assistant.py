"""Fixed acceptance on real PostgreSQL. Administrative connections only seed and observe."""

from contextlib import contextmanager
import os
import unittest
from unittest.mock import patch
from uuid import uuid4

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.assistant_settings")

# The inherited fixture helpers initialize Django with the selected settings.
from catalog_tests.test_catalog import (
    M1, P1, P2, S1, S3, SCOPES, T1, controlled_token, fixture_connection, install, run, sql,
)
from catalog_lab import service as catalog
from django.db import DatabaseError, transaction
import psycopg

from private_assistant import service

TABLE = "catalog_lab.private_assistant"
SECURITY = "PRIVATE_ASSISTANT_DOMAIN_SUPPORTED_SECURITY_FAIL"


def snapshot():
    with fixture_connection() as observer:
        return (
            observer.execute(f"SELECT * FROM {TABLE} ORDER BY id").fetchall(),
            observer.execute("SELECT * FROM catalog_lab.product ORDER BY id").fetchall(),
        )


def configure(tenant=T1, store=S1, principal=P1, **scope):
    return run(tenant, store, principal, lambda: service.create_settings(
        tenant, store, display_name="Synthetic assistant", greeting="Synthetic welcome",
    ), **scope)


def raw_insert(tenant, store, name="Synthetic"):
    return sql(f"INSERT INTO {TABLE} (id,tenant_id,store_id,display_name,greeting) VALUES (%s,%s,%s,%s,'')",
               (uuid4(), tenant, store, name))


def product(tenant, store, principal, sku, name):
    return run(tenant, store, principal, lambda: catalog.create_product(tenant, store, sku=sku, name=name))


class AssistantContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with fixture_connection() as setup:
            setup.execute(f"TRUNCATE {TABLE}, catalog_lab.product, foundation.scoped_grant, "
                          "foundation.membership, foundation.store, foundation.tenant")
            for tenant in {tenant for tenant, _, _, _ in SCOPES}:
                setup.execute("INSERT INTO foundation.tenant (id,name) VALUES (%s,'Synthetic tenant')", (tenant,))
            for tenant, store, principal, membership in SCOPES:
                setup.execute("INSERT INTO foundation.store (id,tenant_id,name) VALUES (%s,%s,'Synthetic store')",
                              (store, tenant))
                setup.execute("INSERT INTO foundation.membership (id,tenant_id,store_id,principal_id,active) "
                              "VALUES (%s,%s,%s,%s,true)", (membership, tenant, store, principal))
                for capability in ("store.view", "store.manage"):
                    setup.execute("INSERT INTO foundation.scoped_grant "
                                  "(id,tenant_id,store_id,membership_id,capability) VALUES (%s,%s,%s,%s,%s)",
                                  (uuid4(), tenant, store, membership, capability))

    def setUp(self):
        with fixture_connection() as setup:
            setup.execute(f"TRUNCATE {TABLE}, catalog_lab.product")

    def unchanged(self, before):
        self.assertEqual(snapshot(), before, f"{SECURITY} unexpected persisted effect")

    @contextmanager
    def denied(self, code="42501"):
        before = snapshot()
        with self.assertRaises(DatabaseError, msg=f"{SECURITY} expected database denial") as error:
            yield
        self.assertEqual(error.exception.__cause__.sqlstate, code)
        self.unchanged(before)

    def test_settings_create_edit_and_fresh_readback(self):
        row = configure()
        before, products = snapshot()
        self.assertEqual(before, [(row.id, T1, S1, "Synthetic assistant", "Synthetic welcome")])
        self.assertEqual(products, [])
        self.assertEqual(run(T1, S1, P1, lambda: service.read_settings(T1, S1), read_only=True).id, row.id)
        self.assertEqual(run(T1, S1, P1, lambda: service.edit_settings(
            T1, S1, display_name="Renamed assistant", greeting="New synthetic greeting",
        )), 1)
        fresh = run(T1, S1, P1, lambda: service.read_settings(T1, S1), read_only=True)
        self.assertEqual((fresh.id, fresh.display_name, fresh.greeting),
                         (row.id, "Renamed assistant", "New synthetic greeting"))
        self.assertEqual(snapshot(), ([(row.id, T1, S1, "Renamed assistant", "New synthetic greeting")], []))

    def test_read_only_settings_and_actual_lookup_boundary(self):
        with self.denied():
            configure(read_only=True)
        row = configure()
        product(T1, S1, P1, "LAMP", "Lamp")
        before = snapshot()

        def edit():
            return service.edit_settings(T1, S1, display_name="Forbidden", greeting="Forbidden")

        self.assertEqual(run(T1, S1, P1, edit, read_only=True), 0, SECURITY)
        with fixture_connection() as setup:
            setup.execute("DELETE FROM foundation.scoped_grant WHERE membership_id=%s AND capability='store.manage'", (M1,))
        try:
            self.assertEqual(run(T1, S1, P1, edit), 0, SECURITY)
            with self.denied():
                configure()
            self.assertEqual(run(T1, S1, P1, lambda: service.read_settings(T1, S1)).id, row.id)
        finally:
            with fixture_connection() as setup:
                setup.execute("INSERT INTO foundation.scoped_grant "
                              "(id,tenant_id,store_id,membership_id,capability) VALUES (%s,%s,%s,%s,'store.manage')",
                              (uuid4(), T1, S1, M1))

        read_products = catalog.read_products

        def verified_reader(tenant, store):
            self.assertEqual(sql(
                "SELECT session_user,current_user,catalog_lab.allowed(%s,%s,false),catalog_lab.allowed(%s,%s,true)",
                (tenant, store, tenant, store),
            ), [("cac_catalog", "cac_catalog", True, False)], SECURITY)
            return read_products(tenant, store)

        with patch.object(catalog, "read_products", side_effect=verified_reader) as reader:
            self.assertEqual(service.ask(T1, S1, P1, kind="sku", query="lamp").product, ("LAMP", "Lamp"))
            reader.assert_called_once_with(T1, S1)
        self.unchanged(before)

    def test_cross_scope_service_and_unfiltered_database_controls(self):
        own = configure()
        for i, (tenant, store, principal, _) in enumerate(SCOPES):
            if store != S1:
                configure(tenant, store, principal)
            product(tenant, store, principal, "COLLISION", f"Synthetic own result {i}")
            self.assertEqual(service.ask(tenant, store, principal, kind="sku", query="collision").product,
                             ("COLLISION", f"Synthetic own result {i}"), SECURITY)
        before = snapshot()
        self.assertEqual(run(T1, S1, P1, lambda: sql(f"SELECT id FROM {TABLE}")), [(own.id,)], SECURITY)
        self.assertEqual(run(T1, S1, P1, lambda: sql("SELECT name FROM catalog_lab.product")),
                         [("Synthetic own result 0",)], SECURITY)
        for tenant, store, _, _ in SCOPES[1:]:
            with self.subTest(store=store):
                self.assertIsNone(run(T1, S1, P1, lambda: service.read_settings(tenant, store)), SECURITY)
                self.assertEqual(run(T1, S1, P1, lambda: service.edit_settings(
                    tenant, store, display_name="Forbidden", greeting="Forbidden",
                )), 0, SECURITY)
                self.assertEqual(run(T1, S1, P1, lambda: sql(
                    f"UPDATE {TABLE} SET greeting='Forbidden' WHERE store_id=%s", (store,),
                )), 0, SECURITY)
                with self.denied():
                    run(T1, S1, P1, lambda: raw_insert(tenant, store))
                with self.assertRaises(PermissionError, msg=SECURITY):
                    service.ask(tenant, store, P1, kind="sku", query="COLLISION")
        with self.assertRaises(PermissionError, msg=SECURITY):
            service.ask(T1, S1, P2, kind="sku", query="COLLISION")
        self.unchanged(before)

    def test_missing_invalid_scope_and_schema_restrictions(self):
        row = configure()
        for token in (None, "invalid"):
            with self.subTest(token=token is not None):
                for operation in (lambda: sql(f"SELECT id FROM {TABLE}"), lambda: raw_insert(T1, S1),
                                  lambda: sql(f"UPDATE {TABLE} SET greeting='Forbidden'")):
                    with self.denied(), transaction.atomic():
                        if token is not None:
                            install(token)
                        operation()

        for statement, value in (
            (f"UPDATE {TABLE} SET id=%s", uuid4()),
            (f"UPDATE {TABLE} SET tenant_id=%s", T1),
            (f"UPDATE {TABLE} SET store_id=%s", S1),
        ):
            with self.denied():
                run(T1, S1, P1, lambda: sql(statement, (value,)))
        for statement in (f"DELETE FROM {TABLE}", f"TRUNCATE {TABLE}", f"ALTER TABLE {TABLE} DISABLE ROW LEVEL SECURITY"):
            with self.denied():
                run(T1, S1, P1, lambda: sql(statement))
        with self.denied("23505"):
            configure()
        with self.denied("23514"):
            run(T1, S1, P1, lambda: service.edit_settings(T1, S1, display_name="  ", greeting=""))
        # This isolated fixture claim reaches the FK through the real catalog login and RLS.
        with self.denied("23503"), transaction.atomic():
            install(controlled_token(T1, S3, P1))
            raw_insert(T1, S3)
        before = snapshot()
        with fixture_connection() as observer:
            self.assertEqual(observer.execute(
                "SELECT relrowsecurity,relforcerowsecurity,pg_get_userbyid(relowner) "
                "FROM pg_class WHERE oid='catalog_lab.private_assistant'::regclass",
            ).fetchone(), (True, True, "cac_owner"), SECURITY)
            self.assertEqual(observer.execute(
                "SELECT cmd,roles::text FROM pg_policies WHERE schemaname='catalog_lab' "
                "AND tablename='private_assistant' ORDER BY cmd",
            ).fetchall(), [("INSERT", "{cac_catalog}"), ("SELECT", "{cac_catalog}"),
                           ("UPDATE", "{cac_catalog}")], SECURITY)
        for role in ("cac_runtime", "cac_provisioner"):
            with fixture_connection(role) as conn, self.assertRaises(psycopg.errors.InsufficientPrivilege, msg=SECURITY):
                conn.execute(f"SELECT id FROM {TABLE}")
        self.unchanged(before)
        self.assertEqual(before[0][0][0], row.id)

    def test_walkthrough_committed_create_rename_and_delete(self):
        def ask(kind, query):
            before = snapshot()
            result = service.ask(T1, S1, P1, kind=kind, query=query)
            self.unchanged(before)
            return result

        self.assertEqual(ask("name", "Lamp").status, "unconfigured")
        configure()
        self.assertEqual(ask("name", "Lamp").status, "unknown")
        item = product(T1, S1, P1, "LAMP-1", "Lamp")
        self.assertIn((item.id, T1, S1, "LAMP-1", "Lamp"), snapshot()[1])
        self.assertEqual(ask("name", " lamp ").product, ("LAMP-1", "Lamp"))
        self.assertEqual(run(T1, S1, P1, lambda: catalog.rename_product(T1, S1, item.id, "Desk lamp")), 1)
        self.assertIn((item.id, T1, S1, "LAMP-1", "Desk lamp"), snapshot()[1])
        self.assertEqual(ask("name", "Lamp").status, "unknown")
        self.assertEqual(ask("name", "Desk lamp").product, ("LAMP-1", "Desk lamp"))
        self.assertEqual(ask("sku", "lamp-1").product, ("LAMP-1", "Desk lamp"))
        duplicate = product(T1, S1, P1, "LAMP-2", "Desk lamp")
        self.assertIn((duplicate.id, T1, S1, "LAMP-2", "Desk lamp"), snapshot()[1])
        answer = ask("name", "DESK LAMP")
        self.assertEqual((answer.status, answer.product), ("ambiguous", None))
        self.assertEqual(run(T1, S1, P1, lambda: catalog.delete_product(T1, S1, item.id)), 1)
        self.assertEqual(snapshot()[1], [(duplicate.id, T1, S1, "LAMP-2", "Desk lamp")])
        self.assertEqual(ask("sku", "LAMP-1").status, "unknown")
        self.assertEqual(ask("name", "Desk lamp").product, ("LAMP-2", "Desk lamp"))
