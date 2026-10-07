"""Environment credentials are data; startup may not grant implicit authority."""
import io

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clean_bootstrap_environment(monkeypatch):
    for key in ("BOOTSTRAP_ADMIN", "DJANGO_SUPERUSER_USERNAME", "DJANGO_SUPERUSER_EMAIL",
                "DJANGO_SUPERUSER_PASSWORD", "CROWN_ENV", "DJANGO_ENV", "ENVIRONMENT",
                "AZURE_ENVIRONMENT", "WEBSITE_HOSTNAME"):
        monkeypatch.delenv(key, raising=False)


def configure(monkeypatch, password="test-only-'quoted-password"):
    monkeypatch.setenv("BOOTSTRAP_ADMIN", "true")
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "bootstrap-admin")
    monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", "bootstrap@example.test")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", password)


def test_quoted_password_is_literal_and_never_printed(monkeypatch):
    configure(monkeypatch)
    output = io.StringIO()
    call_command("bootstrap_runtime_admin", stdout=output)
    user = get_user_model().objects.get(username="bootstrap-admin")
    assert user.is_staff and user.is_superuser and user.is_active
    assert user.check_password("test-only-'quoted-password")
    assert "quoted-password" not in output.getvalue()


def test_unactivated_and_empty_password_bootstrap_denied(monkeypatch):
    with pytest.raises(CommandError):
        call_command("bootstrap_runtime_admin")
    configure(monkeypatch, password="")
    with pytest.raises(CommandError):
        call_command("bootstrap_runtime_admin")
    assert not get_user_model().objects.filter(username="bootstrap-admin").exists()


def test_production_requires_explicit_activation(monkeypatch):
    configure(monkeypatch)
    monkeypatch.delenv("BOOTSTRAP_ADMIN")
    monkeypatch.setenv("CROWN_ENV", "production")
    with pytest.raises(CommandError):
        call_command("bootstrap_runtime_admin")
    assert not get_user_model().objects.filter(username="bootstrap-admin").exists()


def test_existing_nonadministrator_cannot_be_promoted_or_reset(monkeypatch):
    user = get_user_model().objects.create_user(username="bootstrap-admin", password="original")
    configure(monkeypatch)
    with pytest.raises(CommandError):
        call_command("bootstrap_runtime_admin")
    user.refresh_from_db()
    assert not user.is_superuser and not user.is_staff
    assert user.check_password("original")


def test_existing_administrator_rotation_is_idempotent(monkeypatch):
    configure(monkeypatch)
    call_command("bootstrap_runtime_admin")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "second-test-only-password")
    call_command("bootstrap_runtime_admin")
    users = get_user_model().objects.filter(username="bootstrap-admin")
    assert users.count() == 1
    assert users.get().check_password("second-test-only-password")


def test_code_shaped_username_is_rejected_without_creating_an_account(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "admin');raise RuntimeError('injected")
    with pytest.raises(CommandError):
        call_command("bootstrap_runtime_admin")
    assert not get_user_model().objects.exists()


@pytest.mark.parametrize("key,value", [("SEED_DEMO", "true"), ("RUN_DEV_BOOTSTRAP", "1"),
                                       ("RUN_GOLDEN_PATH_BOOTSTRAP", "1"), ("CI_SMOKE_USERNAME", "test-user")])
def test_production_startup_rejects_development_actions(key, value):
    import subprocess
    import sys
    from pathlib import Path

    source = (Path(__file__).resolve().parents[3] / "entrypoint.sh").read_text()
    guard = source.split("python - <<'PYGUARD'\n", 1)[1].split("\nPYGUARD", 1)[0]
    result = subprocess.run([sys.executable, "-c", guard], env={"CROWN_ENV": "production", key: value},
                            capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert key in result.stderr


def test_normal_production_startup_passes_development_guard():
    import subprocess
    import sys
    from pathlib import Path

    source = (Path(__file__).resolve().parents[3] / "entrypoint.sh").read_text()
    guard = source.split("python - <<'PYGUARD'\n", 1)[1].split("\nPYGUARD", 1)[0]
    result = subprocess.run([sys.executable, "-c", guard], env={"CROWN_ENV": "production"},
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0


def test_weak_password_rejected_without_leaving_account(monkeypatch):
    configure(monkeypatch, password="123")
    with pytest.raises(CommandError, match="password does not satisfy policy"):
        call_command("bootstrap_runtime_admin")
    assert not get_user_model().objects.filter(username="bootstrap-admin").exists()
