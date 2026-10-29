import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=120)),
            ],
            options={
                'db_table': 'store',
            },
        ),
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=120)),
            ],
            options={
                'db_table': 'tenant',
            },
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('principal_id', models.UUIDField()),
                ('active', models.BooleanField(default=True)),
                ('store', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.PROTECT, to='foundation.store')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='foundation.tenant')),
            ],
            options={
                'db_table': 'membership',
            },
        ),
        migrations.AddField(
            model_name='store',
            name='tenant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='foundation.tenant'),
        ),
        migrations.CreateModel(
            name='ScopedGrant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('capability', models.CharField(max_length=32)),
                ('membership', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.PROTECT, to='foundation.membership')),
                ('store', models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.PROTECT, to='foundation.store')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='foundation.tenant')),
            ],
            options={
                'db_table': 'scoped_grant',
            },
        ),
        migrations.AddConstraint(
            model_name='store',
            constraint=models.UniqueConstraint(fields=('tenant', 'id'), name='store_tenant_id_unique'),
        ),
        migrations.AddConstraint(
            model_name='scopedgrant',
            constraint=models.UniqueConstraint(fields=('membership', 'capability'), name='grant_member_cap_unique'),
        ),
        migrations.AddConstraint(
            model_name='scopedgrant',
            constraint=models.CheckConstraint(condition=models.Q(('capability__in', ['store.view', 'store.manage'])), name='grant_capability_known'),
        ),
        migrations.AddConstraint(
            model_name='membership',
            constraint=models.UniqueConstraint(fields=('tenant', 'store', 'principal_id'), name='membership_principal_scope_unique'),
        ),
        migrations.AddConstraint(
            model_name='membership',
            constraint=models.UniqueConstraint(fields=('tenant', 'store', 'id'), name='membership_scope_id_unique'),
        ),
    ]
