"""Set up the catalog-only login and signing key for a disposable database."""
import json
import os
from pathlib import Path
import secrets
import sys

import psycopg
from psycopg import sql


def main():
    if os.environ.get("CAC_EXPERIMENTAL_DISPOSABLE") != "1":
        raise SystemExit("Explicit disposable mode required")
    cfg = json.loads(Path(os.environ["CAC_TEST_CONFIG"]).read_text())
    db = cfg["connection"]
    if db["dbname"] != "cac_s007_test" or db["host"] not in ("127.0.0.1", "localhost", "::1"):
        raise SystemExit("Local disposable database required")
    path = Path(os.environ["CAC_CATALOG_CONFIG"])
    stage, = sys.argv[1:]
    if stage == "role":
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        private = {"password": secrets.token_urlsafe(40), "issuer_key": secrets.token_hex(32)}
        with os.fdopen(fd, "w") as stream:
            json.dump(private, stream)
        with psycopg.connect(**db, user="postgres", password=cfg["passwords"]["postgres"]) as conn:
            conn.execute("SET LOCAL log_statement = 'none'")
            # Password-bearing utility SQL is never printed.
            conn.execute(sql.SQL("CREATE ROLE cac_catalog LOGIN NOSUPERUSER NOCREATEDB "
                                "NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD {}")
                         .format(sql.Literal(private["password"])))
            conn.execute("CREATE SCHEMA catalog_lab AUTHORIZATION cac_owner")
            conn.execute("GRANT CONNECT ON DATABASE cac_s007_test TO cac_catalog")
    elif stage == "key":
        private = json.loads(path.read_text())
        with psycopg.connect(**db, user="cac_owner", password=cfg["passwords"]["cac_owner"]) as conn:
            conn.execute("INSERT INTO cac_private.catalog_key VALUES (true,%s)",
                         (bytes.fromhex(private["issuer_key"]),))
    else:
        raise SystemExit("Expected role or key")
    print(f"Catalog bootstrap {stage} completed")


if __name__ == "__main__":
    main()

