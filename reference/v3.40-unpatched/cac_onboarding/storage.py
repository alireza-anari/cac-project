"""SQLite-backed domain demonstration. NOT a production PostgreSQL/RLS backend.

DB-level composite foreign keys, idempotency, unique ownership, and transactions
are exercised by tests. Production requires a separate isolated provisioning worker.
"""
import contextlib
import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS requests(
 id TEXT PRIMARY KEY, principal_id INTEGER NOT NULL CHECK(principal_id > 0),
 key_digest TEXT NOT NULL, payload_digest TEXT NOT NULL,
 tenant_name TEXT NOT NULL, store_name TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('QUEUED','COMPLETED','BLOCKED')),
 tenant_id TEXT, store_id TEXT, error_code TEXT, created_at TEXT NOT NULL,
 UNIQUE(principal_id,key_digest)
);
CREATE TABLE IF NOT EXISTS tenants(
 id TEXT PRIMARY KEY, owner_principal_id INTEGER NOT NULL UNIQUE CHECK(owner_principal_id > 0),
 display_name TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stores(
 id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id),
 display_name TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'DRAFT'
 CHECK(state IN ('DRAFT','PREVIEW','READY','LIVE')), created_at TEXT NOT NULL,
 UNIQUE(tenant_id,id)
);
CREATE TABLE IF NOT EXISTS memberships(
 tenant_id TEXT NOT NULL REFERENCES tenants(id), principal_id INTEGER NOT NULL CHECK(principal_id>0),
 is_active INTEGER NOT NULL CHECK(is_active IN (0,1)),
 PRIMARY KEY(tenant_id,principal_id)
);
CREATE TABLE IF NOT EXISTS grants(
 tenant_id TEXT NOT NULL, store_id TEXT NOT NULL, principal_id INTEGER NOT NULL,
 capability TEXT NOT NULL, granted_by INTEGER NOT NULL CHECK(granted_by > 0),
 revoked_at TEXT, created_at TEXT NOT NULL,
 FOREIGN KEY(store_id,tenant_id) REFERENCES stores(id,tenant_id),
 FOREIGN KEY(tenant_id,principal_id) REFERENCES memberships(tenant_id,principal_id),
 UNIQUE(store_id,principal_id,capability)
);
CREATE TABLE IF NOT EXISTS invitations(
 id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, store_id TEXT NOT NULL,
 target_principal_id INTEGER NOT NULL CHECK(target_principal_id>0),
 inviter_principal_id INTEGER NOT NULL CHECK(inviter_principal_id>0),
 caps_json TEXT NOT NULL, token_digest TEXT NOT NULL UNIQUE,
 expires_at TEXT NOT NULL, accepted_at TEXT, revoked_at TEXT,
 FOREIGN KEY(store_id,tenant_id) REFERENCES stores(id,tenant_id)
);
CREATE TABLE IF NOT EXISTS audit_events(
 id INTEGER PRIMARY KEY AUTOINCREMENT, store_id TEXT, actor_id INTEGER,
 event TEXT NOT NULL, entity_id TEXT NOT NULL, created_at TEXT NOT NULL
);
"""


class SQLiteReferenceRepository:
    """Execute local reference transactions only, with an isolated file per test."""
    def __init__(self, path: str | Path):
        self.path = str(path)
        with self.connection() as con:
            con.executescript(SCHEMA)

    @contextlib.contextmanager
    def connection(self):
        con = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        try:
            yield con
        finally:
            con.close()

    @contextlib.contextmanager
    def transaction(self):
        with self.connection() as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                yield con
                con.execute("COMMIT")
            except BaseException:
                con.execute("ROLLBACK")
                raise
