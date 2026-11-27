from pathlib import Path
import uuid

from django.db import migrations, models


SQL = Path(__file__).with_name("catalog.sql")


class Migration(migrations.Migration):
    dependencies = [("foundation", "0002_security")]
    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField()),
                ("store_id", models.UUIDField()),
                ("sku", models.CharField(max_length=32)),
                ("name", models.CharField(max_length=120)),
            ],
            options={
                "db_table": '"catalog_lab"."product"',
                "constraints": [
                    models.UniqueConstraint(fields=("tenant_id", "store_id", "sku"), name="product_scope_sku_unique"),
                    models.CheckConstraint(condition=models.Q(sku__regex=r"^[A-Z0-9][A-Z0-9-]*$"), name="product_sku_format"),
                    models.CheckConstraint(condition=models.Q(name__regex=r"[^[:space:]]"), name="product_name_nonblank"),
                ],
            },
        ),
        migrations.RunSQL(SQL.read_text(encoding="utf-8"), """
            DROP POLICY product_delete ON catalog_lab.product;
            DROP POLICY product_update ON catalog_lab.product;
            DROP POLICY product_insert ON catalog_lab.product;
            DROP POLICY product_read ON catalog_lab.product;
            DROP FUNCTION catalog_lab.allowed(uuid, uuid, boolean);
            DROP TABLE cac_private.catalog_key;
        """),
    ]

