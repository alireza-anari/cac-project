"""PROPOSED schema, new origin; not recovered or Freeze-approved."""
import uuid
from django.db import models

class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    class Meta:
        db_table = 'tenant'

class Store(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT)
    name = models.CharField(max_length=120)
    class Meta:
        db_table = 'store'
        constraints = [models.UniqueConstraint(fields=['tenant','id'], name='store_tenant_id_unique')]

class Membership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT)
    # Composite DB FK is installed separately; Django's scalar FK is insufficient.
    store = models.ForeignKey(Store, on_delete=models.PROTECT, db_constraint=False)
    principal_id = models.UUIDField()
    active = models.BooleanField(default=True)
    class Meta:
        db_table = 'membership'
        constraints = [models.UniqueConstraint(fields=['tenant','store','principal_id'],name='membership_principal_scope_unique'),
                       models.UniqueConstraint(fields=['tenant','store','id'],name='membership_scope_id_unique')]

class ScopedGrant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT)
    store = models.ForeignKey(Store, on_delete=models.PROTECT, db_constraint=False)
    membership = models.ForeignKey(Membership, on_delete=models.PROTECT, db_constraint=False)
    capability = models.CharField(max_length=32)
    class Meta:
        db_table = 'scoped_grant'
        constraints = [models.UniqueConstraint(fields=['membership','capability'],name='grant_member_cap_unique'),
                       models.CheckConstraint(condition=models.Q(capability__in=['store.view','store.manage']),name='grant_capability_known')]
