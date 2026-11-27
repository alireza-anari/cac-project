from pathlib import Path
import uuid

from django.db import migrations, models

SQL = Path(__file__).with_name("assistant.sql")


class Migration(migrations.Migration):
    dependencies = [("catalog_lab", "0001_catalog")]
    operations = [
        migrations.CreateModel(
            name="Assistant",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField()),
                ("store_id", models.UUIDField()),
                ("display_name", models.CharField(max_length=120)),
                ("greeting", models.CharField(blank=True, max_length=280)),
            ],
            options={
                "db_table": '"catalog_lab"."private_assistant"',
                "constraints": [
                    models.UniqueConstraint(fields=("tenant_id", "store_id"), name="assistant_store_unique"),
                    models.CheckConstraint(
                        condition=models.Q(display_name__regex=r"[^[:space:]]"),
                        name="assistant_display_name_nonblank",
                    ),
                ],
            },
        ),
        # Reversing CreateModel drops the table and its table-local policies, FK and grants.
        migrations.RunSQL(SQL.read_text(encoding="utf-8"), migrations.RunSQL.noop),
    ]
