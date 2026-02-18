"""
Root-level pytest conftest for the backend.
Disables production-safety middleware by default so existing tests pass.
Individual tests opt in via @override_settings().
"""
import os

# Set env vars BEFORE django.setup() reads settings.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
os.environ["TENANT_HEADER_REQUIRED"] = "false"
os.environ.setdefault("CROWN_DEMO_MODE", "false")


def pytest_configure(config):
    import django
    django.setup()
