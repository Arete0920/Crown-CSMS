import pytest
from django.core.exceptions import ImproperlyConfigured

from crown_api.production_secret_guard import enforce_production_secret


@pytest.mark.parametrize(
    "env_name,env_value",
    [
        ("CROWN_ENV", "production"),
        ("DJANGO_ENV", "staging"),
        ("ENVIRONMENT", "prod"),
        ("WEBSITE_HOSTNAME", "crown-api-prod.azurewebsites.net"),
        ("CROWN_DEPLOY_SECURITY", "true"),
    ],
)
def test_hardened_context_rejects_missing_secret(monkeypatch, env_name, env_value):
    for key in (
        "CROWN_ENV",
        "DJANGO_ENV",
        "ENVIRONMENT",
        "WEBSITE_HOSTNAME",
        "WEBSITE_INSTANCE_ID",
        "CROWN_DEPLOY_SECURITY",
        "DJANGO_SECRET_KEY",
        "SECRET_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(env_name, env_value)

    with pytest.raises(ImproperlyConfigured):
        enforce_production_secret([])


def test_deploy_check_rejects_weak_secret(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "weak")

    with pytest.raises(ImproperlyConfigured):
        enforce_production_secret(["manage.py", "check", "--deploy"])


def test_hardened_context_accepts_strong_secret(monkeypatch):
    monkeypatch.setenv("CROWN_ENV", "production")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "aB3!xY7@" * 10)

    enforce_production_secret([])


def test_local_development_allows_missing_secret(monkeypatch):
    for key in (
        "CROWN_ENV",
        "DJANGO_ENV",
        "ENVIRONMENT",
        "WEBSITE_HOSTNAME",
        "WEBSITE_INSTANCE_ID",
        "CROWN_DEPLOY_SECURITY",
        "DJANGO_SECRET_KEY",
        "SECRET_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    enforce_production_secret(["manage.py", "runserver"])
