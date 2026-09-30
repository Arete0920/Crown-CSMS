import pytest
from django.test import override_settings

from crown_api import metrics_views


@pytest.mark.parametrize(
    "env_value",
    ["prod", "production", "live"],
)
@override_settings(
    CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS=True,
    CROWN_DEMO_MODE=True,
    CROWN_DEV_OPEN_API=True,
)
def test_sample_metrics_never_allowed_in_production(monkeypatch, env_value):
    monkeypatch.setattr(metrics_views.settings, "CROWN_ENV", env_value, raising=False)
    monkeypatch.delenv("WEBSITE_HOSTNAME", raising=False)
    assert metrics_views._sample_metrics_allowed() is False


@override_settings(
    CROWN_ENV="development",
    DJANGO_ENV="",
    ENVIRONMENT="",
    CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS=False,
    CROWN_DEMO_MODE=False,
    CROWN_DEV_OPEN_API=False,
)
def test_sample_metrics_require_explicit_nonproduction_opt_in(monkeypatch):
    monkeypatch.delenv("WEBSITE_HOSTNAME", raising=False)
    monkeypatch.delenv("CROWN_ENV", raising=False)
    monkeypatch.delenv("DJANGO_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    assert metrics_views._sample_metrics_allowed() is False


@override_settings(
    CROWN_ENV="development",
    DJANGO_ENV="",
    ENVIRONMENT="",
    CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS=True,
    CROWN_DEMO_MODE=False,
    CROWN_DEV_OPEN_API=False,
)
def test_sample_metrics_allowed_only_when_explicitly_enabled_in_nonproduction(monkeypatch):
    monkeypatch.delenv("WEBSITE_HOSTNAME", raising=False)
    monkeypatch.delenv("CROWN_ENV", raising=False)
    monkeypatch.delenv("DJANGO_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    assert metrics_views._sample_metrics_allowed() is True
