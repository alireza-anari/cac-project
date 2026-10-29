"""NEW_IMPLEMENTATION_EXPERIMENTAL. No production settings or endpoints."""
import json
import os
from pathlib import Path
# No sessions/tokens use this key. A deployment must supply its own secret/config.
SECRET_KEY = os.environ.get('CAC_DJANGO_SECRET', 'synthetic-check-only-not-a-deployment-key')
DEBUG = False
ALLOWED_HOSTS = []
INSTALLED_APPS = ['foundation']
MIDDLEWARE = []
ROOT_URLCONF = 'config.urls'
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'cac_s007_test',
                         'USER': 'cac_runtime', 'HOST':'127.0.0.1', 'PORT':'5432',
                         'OPTIONS': {'options':'-c search_path=foundation,public'}, 'CONN_MAX_AGE':0}}
if os.environ.get('CAC_TEST_CONFIG'):
    config = json.loads(Path(os.environ['CAC_TEST_CONFIG']).read_text())
    role = os.environ.get('CAC_DB_ROLE','cac_runtime')
    db = config['connection']
    DATABASES['default'].update(NAME=db['dbname'], HOST=db['host'], PORT=str(db['port']),
                                USER=role, PASSWORD=config['passwords'][role])
