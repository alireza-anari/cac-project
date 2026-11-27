import uuid

from django.db import models


class Assistant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField()
    store_id = models.UUIDField()
    display_name = models.CharField(max_length=120)
    greeting = models.CharField(max_length=280, blank=True)

    class Meta:
        db_table = '"catalog_lab"."private_assistant"'
        constraints = [
            models.UniqueConstraint(fields=["tenant_id", "store_id"], name="assistant_store_unique"),
            models.CheckConstraint(
                condition=models.Q(display_name__regex=r"[^[:space:]]"),
                name="assistant_display_name_nonblank",
            ),
        ]
