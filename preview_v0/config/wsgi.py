import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from config.network import install
install()
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
