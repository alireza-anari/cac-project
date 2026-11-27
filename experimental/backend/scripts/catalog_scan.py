"""Keep CI evidence restricted to named files and scan fixture values."""
import json
import os
from pathlib import Path
import re

root = Path(os.environ["CATALOG_EVIDENCE"])
allowed = {"revision.txt", "environment.txt", "setup.log", "regression.log",
           "schema.log", "inventory.json", "roundtrip.log", "catalog.log", "scan.log"}
base = json.loads(Path(os.environ["CAC_TEST_CONFIG"]).read_text())
catalog = json.loads(Path(os.environ["CAC_CATALOG_CONFIG"]).read_text())
secrets = [*base["passwords"].values(), base["issuer_key"], catalog["password"], catalog["issuer_key"]]
for path in root.iterdir():
    if path.is_symlink() or not path.is_file() or path.name not in allowed:
        raise SystemExit("Unexpected evidence path")
    data = path.read_text()
    if ("PRIVATE KEY-----" in data or re.search(r"(?<![0-9a-f])[0-9a-f]{80,}\.[0-9a-f]{64}(?![0-9a-f])", data)
            or any(secret and secret in data for secret in secrets)):
        raise SystemExit("Credential pattern in evidence")
print("Catalog evidence allowlist and credential scan passed")
