"""
Celery application entry point for Crown2026.

Workers are started separately from Django:
    celery -A crown_api worker -l info
    celery -A crown_api beat -l info
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")

app = Celery("crown_api")

# Read config from Django settings, using CELERY_ prefix namespace.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in each INSTALLED_APP's tasks.py module.
app.autodiscover_tasks()
