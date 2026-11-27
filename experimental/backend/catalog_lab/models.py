import uuid

from django.db import models


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField()
    store_id = models.UUIDField()
    sku = models.CharField(max_length=32)
    name = models.CharField(max_length=120)

    class Meta:
        db_table = '"catalog_lab"."product"'
        constraints = [
            models.UniqueConstraint(fields=["tenant_id", "store_id", "sku"], name="product_scope_sku_unique"),
            models.CheckConstraint(condition=models.Q(sku__regex=r"^[A-Z0-9][A-Z0-9-]*$"), name="product_sku_format"),
            models.CheckConstraint(condition=models.Q(name__regex=r"[^[:space:]]"), name="product_name_nonblank"),
        ]

