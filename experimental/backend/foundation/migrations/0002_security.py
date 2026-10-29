from pathlib import Path
from django.db import migrations
SQL = Path(__file__).resolve().parents[2] / 'sql'
class Migration(migrations.Migration):
    dependencies = [('foundation','0001_initial')]
    operations = [migrations.RunSQL((SQL/'security.sql').read_text(), (SQL/'security_reverse.sql').read_text())]
