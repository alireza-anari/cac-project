"""Local catalog operations. The caller holds a signed catalog transaction."""
from django.db import connection

from .models import Product


def _products(tenant, store):
    if not connection.in_atomic_block or connection.settings_dict["USER"] != "cac_catalog":
        raise RuntimeError("Catalog operations require a catalog transaction")
    return Product.objects.filter(tenant_id=tenant, store_id=store)


def create_product(tenant, store, *, sku, name):
    return _products(tenant, store).create(tenant_id=tenant, store_id=store, sku=sku, name=name)


def read_products(tenant, store):
    return list(_products(tenant, store).order_by("sku").values_list("sku", "name"))


def rename_product(tenant, store, product_id, name):
    return _products(tenant, store).filter(pk=product_id).update(name=name)


def delete_product(tenant, store, product_id):
    return _products(tenant, store).filter(pk=product_id).delete()[0]

