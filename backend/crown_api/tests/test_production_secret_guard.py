import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured

from crown_api.production_secret_guard import (
    enforce_production_secret,
    validate_database_runtime,
    validate_debug_runtime,
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



@pytest.mark.parametrize("hardened", [False, True])
def test_debug_false_remains_valid_in_any_context(hardened):
    validate_debug_runtime(False, hardened=hardened)


def test_debug_true_is_allowed_only_for_local_development():
    validate_debug_runtime(True, hardened=False)
    with pytest.raises(ImproperlyConfigured, match="DEBUG=True"):
        validate_debug_runtime(True, hardened=True)


# Real Django settings-import matrix. These cases do not connect to a database
# or invoke Azure resources; they validate configuration before app startup.
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_STRONG_TEST_KEY = "configuration-matrix-nonproduction-fixture-" + ("Ab7!" * 16)
_HOSTED_MARKERS = [
    pytest.param({"CROWN_ENV": "dev", "WEBSITE_HOSTNAME": "dev.example.azurewebsites.net"}, id="azure-dev"),
    pytest.param({"WEBSITE_INSTANCE_ID": "mock-app-service-instance"}, id="azure-instance"),
    pytest.param({"CROWN_ENV": "staging"}, id="staging"),
    pytest.param({"CROWN_ENV": "production"}, id="production"),
    pytest.param({"DJANGO_ENV": "sandbox"}, id="sandbox"),
    pytest.param({"AZURE_ENVIRONMENT": "production"}, id="azure-production"),
    pytest.param({"ENVIRONMENT": "live"}, id="live-alias"),
]

_IMPORT_SETTINGS = (
    "import json; from django.conf import settings; "
    "print('CROWN_SETTINGS_MATRIX=' + json.dumps({"
    "'engine': settings.DATABASES['default']['ENGINE'], "
    "'debug': settings.DEBUG, "
    "'cors': settings.CORS_ALLOW_ALL_ORIGINS, "
    "'key_length': len(settings.SECRET_KEY)}))"
)


def _probe_settings(variables=None, *, deploy_check=False):
    """Import settings in a subprocess to verify true initialization order."""
    env = os.environ.copy()
    for name in (
        "CROWN_ENV",
        "DJANGO_ENV",
        "ENVIRONMENT",
        "AZURE_ENVIRONMENT",
        "WEBSITE_HOSTNAME",
        "WEBSITE_INSTANCE_ID",
        "CROWN_DEPLOY_SECURITY",
        "DATABASE_URL",
        "DJANGO_SECRET_KEY",
        "SECRET_KEY",
        "DJANGO_DEBUG",
        "DEBUG",
        "CORS_ALLOW_ALL_ORIGINS",
        "CROWN_DEMO_MODE",
        "DJANGO_SETTINGS_MODULE",
    ):
        env.pop(name, None)
    env.update(DJANGO_SETTINGS_MODULE="crown_api.settings")
    env.update(variables or {})
    cmd = [sys.executable, "-c", _IMPORT_SETTINGS]
    if deploy_check:
        cmd.append("--deploy")
    return subprocess.run(
        cmd,
        cwd=_BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _assert_import_succeeds(result, engine):
    assert result.returncode == 0, result.stderr
    line = next(
        line for line in result.stdout.splitlines()
        if line.startswith("CROWN_SETTINGS_MATRIX=")
    )
    config = json.loads(line.removeprefix("CROWN_SETTINGS_MATRIX="))
    assert config["engine"] == engine
    assert config["debug"] is False
    assert config["cors"] is False
    return config


def test_settings_local_development_retains_implicit_sqlite():
    result = _probe_settings()
    assert result.returncode == 0, result.stderr
    assert '"engine": "django.db.backends.sqlite3"' in result.stdout


@pytest.mark.parametrize("flags", [{}, {"CROWN_DEPLOY_SECURITY": "true"}], ids=["deploy-arg", "hardening-flag"])
def test_settings_isolated_ci_retains_explicit_sqlite_and_deploy_checks(flags):
    result = _probe_settings(
        {"DATABASE_URL": "sqlite:///./ci.sqlite3",
         "DJANGO_SECRET_KEY": _STRONG_TEST_KEY,
         "DJANGO_DEBUG": "false",
         **flags},
        deploy_check=True,
    )
    _assert_import_succeeds(result, "django.db.backends.sqlite3")


@pytest.mark.parametrize("marker", _HOSTED_MARKERS)
def test_settings_hosted_external_database_can_initialize(marker):
    result = _probe_settings({
        **marker,
        "DATABASE_URL": "postgresql://db.example.invalid/crown",
        "DJANGO_SECRET_KEY": _STRONG_TEST_KEY,
        "DJANGO_DEBUG": "false",
    })
    _assert_import_succeeds(result, "django.db.backends.postgresql")


@pytest.mark.parametrize("marker", _HOSTED_MARKERS)
def test_settings_hosted_missing_database_fails_before_sqlite_fallback(marker):
    result = _probe_settings({
        **marker, "DJANGO_SECRET_KEY": _STRONG_TEST_KEY,
        "DJANGO_DEBUG": "false",
    })
    assert result.returncode != 0
    assert "DATABASE_URL is required in hardened environments." in result.stderr


@pytest.mark.parametrize("marker", _HOSTED_MARKERS)
def test_settings_hosted_explicit_sqlite_fails_closed(marker):
    result = _probe_settings({
        **marker, "DJANGO_SECRET_KEY": _STRONG_TEST_KEY,
        "DATABASE_URL": "sqlite:///./unsafe.sqlite3",
        "DJANGO_DEBUG": "false",
    })
    assert result.returncode != 0
    assert "Hosted and staging/production database must not use SQLite." in result.stderr


@pytest.mark.parametrize("key", [None, "short", "django-insecure-" + ("x" * 64), "a" * 64],
                         ids=["missing", "short", "insecure-prefix", "low-entropy"])
def test_settings_hardened_missing_or_weak_secrets_fail_closed(key):
    vars = {"CROWN_ENV": "production", "DATABASE_URL": "postgresql://db.example.invalid/crown"}
    if key is not None:
        vars["DJANGO_SECRET_KEY"] = key
    result = _probe_settings(vars)
    assert result.returncode != 0
    assert "SECRET_KEY" in result.stderr or "strong" in result.stderr


@pytest.mark.parametrize("debug_flags", [
    {"DJANGO_DEBUG": "true"},
    {"DEBUG": "true"},
    {"DJANGO_DEBUG": "false", "DEBUG": "true"},
    {"DJANGO_DEBUG": "true", "DEBUG": "false"},
], ids=["django-true", "debug-true", "conflicting-debug-true", "conflicting-django-true"])
def test_settings_rejects_unsafe_debug_before_cors_bypass(debug_flags):
    result = _probe_settings({
        "CROWN_ENV": "staging",
        "DATABASE_URL": "postgresql://db.example.invalid/crown",
        "DJANGO_SECRET_KEY": _STRONG_TEST_KEY,
        "CORS_ALLOW_ALL_ORIGINS": "true",
        **debug_flags,
    })
    assert result.returncode != 0
    assert "DEBUG=True is forbidden in hardened environments." in result.stderr


def test_settings_hardened_secret_key_alias_remains_compatible():
    result = _probe_settings({
        "CROWN_ENV": "production",
        "DATABASE_URL": "postgresql://db.example.invalid/crown",
        "SECRET_KEY": _STRONG_TEST_KEY,
    })
    _assert_import_succeeds(result, "django.db.backends.postgresql")
