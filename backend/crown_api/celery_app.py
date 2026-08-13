"""
Celery application entry point for CROWN.

Workers are started separately from Django:
    celery -A crown_api worker -l info
    celery -A crown_api beat -l info
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")

app = Celery("crown_api")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
