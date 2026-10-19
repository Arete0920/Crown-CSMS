import pytest
from django.core.exceptions import ImproperlyConfigured

from crown_api.production_secret_guard import (
    enforce_production_secret,
    validate_database_runtime,
)


@pytest.mark.parametrize(
    "env_name,env_value",
    [
        ("CROWN_ENV", "production"),
        ("DJANGO_ENV", "staging"),
        ("ENVIRONMENT", "prod"),
        ("CROWN_ENV", "live"),
        ("AZURE_ENVIRONMENT", "staging"),
        ("AZURE_ENVIRONMENT", "production"),
        ("WEBSITE_HOSTNAME", "crown-api-prod.azurewebsites.net"),
        ("CROWN_DEPLOY_SECURITY", "true"),
    ],
)
def test_hardened_context_rejects_missing_secret(monkeypatch, env_name, env_value):
    for key in (
        "CROWN_ENV",
        "DJANGO_ENV",
        "ENVIRONMENT",
        "AZURE_ENVIRONMENT",
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
        "AZURE_ENVIRONMENT",
        "WEBSITE_HOSTNAME",
        "WEBSITE_INSTANCE_ID",
        "CROWN_DEPLOY_SECURITY",
        "DJANGO_SECRET_KEY",
        "SECRET_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    enforce_production_secret(["manage.py", "runserver"])


@pytest.mark.parametrize("hosted", [False, True])
def test_hardened_runtime_rejects_missing_database(hosted):
    with pytest.raises(ImproperlyConfigured, match="DATABASE_URL"):
        validate_database_runtime("", hardened=True, hosted=hosted)


@pytest.mark.parametrize("scheme", ["sqlite:///./db.sqlite3", "sqlite3:///tmp/data.db"])
def test_hosted_runtime_rejects_explicit_sqlite(scheme):
    with pytest.raises(ImproperlyConfigured, match="SQLite"):
        validate_database_runtime(scheme, hardened=True, hosted=True)


def test_local_and_ci_keep_explicit_sqlite_available():
    validate_database_runtime("sqlite:///./ci.sqlite3", hardened=False, hosted=False)


def test_hardened_runtime_accepts_external_database_url():
    validate_database_runtime(
        "postgresql://db.example.invalid/crown",
        hardened=True,
        hosted=True,
    )


def test_deploy_check_without_host_allows_explicit_ci_database():
    validate_database_runtime(
        "sqlite:///./ci.sqlite3",
        hardened=True,
        hosted=False,
    )
