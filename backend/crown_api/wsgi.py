"""
WSGI config for crown_api project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from crown_api.production_secret_guard import enforce_production_secret

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
enforce_production_secret()

application = get_wsgi_application()
