"""
Root-level pytest conftest for the backend.
Disables production-safety middleware by default so existing tests pass.
Individual tests opt in via @override_settings().
"""
import os
import pytest

# Set env vars BEFORE django.setup() reads settings.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
os.environ["TENANT_HEADER_REQUIRED"] = "false"
os.environ.setdefault("CROWN_DEMO_MODE", "false")


def pytest_configure(config):
    import django
    django.setup()


@pytest.fixture(autouse=True)
def explicit_sample_dashboard_contracts(request):
    """These shape/access contracts test samples, not live business operations."""
    sample_modules = {
        "test_metrics_permissions_contract.py",
        "test_51x51_evidence_031_administrative_portal.py",
        "test_51x51_evidence_25_nutrition_food_services.py",
        "test_later_tier_metrics_api.py",
    }
    if request.node.path.name in sample_modules:
        request.getfixturevalue("settings").CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS = True
