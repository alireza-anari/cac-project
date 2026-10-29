"""Prove Django ORM uses a nonowner runtime connection and the same RLS boundary."""
import os
os.environ['CAC_DB_ROLE']='cac_runtime'
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.db import connection,transaction
from foundation.models import Store,Tenant,Membership,ScopedGrant
from tests.test_security import context,S1,T1,M1
with transaction.atomic():
    context(connection.connection)
    assert connection.cursor().execute('SELECT current_user').fetchone()==('cac_runtime',)
    assert [str(x) for x in Store.objects.values_list('id',flat=True)]==[S1]
    assert [str(x) for x in Tenant.objects.values_list('id',flat=True)]==[T1]
    assert [str(x) for x in Membership.objects.values_list('id',flat=True)]==[M1]
    assert list(ScopedGrant.objects.values_list('capability',flat=True))==['store.view']
print('ORM PASS: Django transaction + signed context + actual cac_runtime login, scoped records only.')
