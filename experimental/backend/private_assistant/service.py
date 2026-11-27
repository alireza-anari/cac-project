"""Private deterministic lookup inside the disposable synthetic catalog boundary."""

from dataclasses import dataclass
from typing import Literal

from django.db import connection

from catalog_lab import lab_issuer, service as catalog
from .models import Assistant


def _settings(tenant, store):
    if not connection.in_atomic_block or connection.settings_dict["USER"] != "cac_catalog":
        raise RuntimeError("Assistant settings require a catalog transaction")
    return Assistant.objects.filter(tenant_id=tenant, store_id=store)


def create_settings(tenant, store, *, display_name, greeting=""):
    return _settings(tenant, store).create(
        tenant_id=tenant, store_id=store, display_name=display_name, greeting=greeting,
    )


def read_settings(tenant, store):
    return _settings(tenant, store).first()


def edit_settings(tenant, store, *, display_name, greeting):
    return _settings(tenant, store).update(display_name=display_name, greeting=greeting)


@dataclass(frozen=True)
class Answer:
    status: Literal["found", "unknown", "ambiguous", "unconfigured"]
    message: str
    product: tuple[str, str] | None = None


def ask(tenant, store, principal, *, kind, query):
    """Look up an exact case-folded name or SKU with a fresh signed read scope."""
    if kind not in ("name", "sku"):
        raise ValueError("Expected lookup kind 'name' or 'sku'")

    def lookup():
        if read_settings(tenant, store) is None:
            return Answer("unconfigured", "No private assistant is configured for this store.")
        term = query.strip().casefold()
        index = 0 if kind == "sku" else 1
        matches = [product for product in catalog.read_products(tenant, store)
                   if term and product[index].casefold() == term]
        if len(matches) == 1:
            sku, name = matches[0]
            return Answer("found", f"{name} (SKU {sku})", (sku, name))
        if matches:
            return Answer("ambiguous", "Multiple products match. Ask by SKU.")
        return Answer("unknown", "No product matches this inquiry in this store.")

    return lab_issuer.run(tenant, store, principal, lookup, read_only=True)
