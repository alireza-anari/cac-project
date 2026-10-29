"""NEW_IMPLEMENTATION_EXPERIMENTAL. No production settings or endpoints."""
import json
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
# No real identity/session integration is authorized by this experiment.
SECRET_KEY = os.environ.get('CAC_DJANGO_SECRET')
if not SECRET_KEY:
    if os.environ.get('CAC_EXPERIMENTAL_DISPOSABLE') == '1':
        SECRET_KEY = 'synthetic-check-only-not-a-deployment-key'
    else:
        raise ImproperlyConfigured('CAC_DJANGO_SECRET is required outside explicit disposable tests')
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
