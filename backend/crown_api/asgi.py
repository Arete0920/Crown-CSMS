"""
ASGI config for crown_api project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from crown_api.production_secret_guard import enforce_production_secret

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
enforce_production_secret()

application = get_asgi_application()
