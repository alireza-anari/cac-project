from copy import deepcopy
import json
import os
from pathlib import Path

from .settings import *  # Use the unmodified foundation configuration.

if os.environ.get("CAC_EXPERIMENTAL_DISPOSABLE") != "1":
    raise ImproperlyConfigured("Catalog requires explicit disposable mode")

INSTALLED_APPS = [*INSTALLED_APPS, "catalog_lab"]
DATABASES = deepcopy(DATABASES)
db = DATABASES["default"]
if db["NAME"] != "cac_s007_test" or db["HOST"] not in ("127.0.0.1", "localhost", "::1"):
    raise ImproperlyConfigured("Catalog requires the local disposable database")
if os.environ.get("CAC_CATALOG_LOGIN") == "1":
    role_file = json.loads(Path(os.environ["CAC_CATALOG_CONFIG"]).read_text())
    db.update(USER="cac_catalog", PASSWORD=role_file["password"])

