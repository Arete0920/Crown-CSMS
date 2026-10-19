"""Regression controls for demonstration credentials and tenant-safe reset."""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.demo_credentials import configured_demo_password
from core.management.commands.seed_demo_school import Command as SeedDemoSchool
from core.models import School, UserAccount


STRONG_DEMO_PASSWORD = "Fixture-only--Crown--2026-strong"


@pytest.fixture(autouse=True)
def local_demo_test_runtime(monkeypatch):
    """Supply explicit local isolation to positive demo command test cases."""
    monkeypatch.setenv("CROWN_ENV", "test")
    for key in ("WEBSITE_HOSTNAME", "WEBSITE_INSTANCE_ID", "AZURE_ENVIRONMENT"):
        monkeypatch.delenv(key, raising=False)


def test_demo_seed_requires_explicit_local_environment(monkeypatch):
    from core.demo_seed_safety import require_local_demo_seed

    monkeypatch.delenv("CROWN_ENV", raising=False)
    with pytest.raises(CommandError, match="CROWN_ENV=local or test"):
        require_local_demo_seed(operation="school seeding")


def test_demo_password_reset_requires_sqlite_before_writes(monkeypatch, settings):
    from core.demo_seed_safety import require_local_demo_seed

    current = settings.DATABASES["default"]
    settings.DATABASES = {
        "default": {**current, "ENGINE": "django.db.backends.postgresql"}
    }
    with pytest.raises(CommandError, match="SQLite"):
        require_local_demo_seed(operation="password reset")


def test_missing_demo_password_disables_password_login(monkeypatch):
    monkeypatch.delenv("CROWN_DEMO_PASSWORD", raising=False)
    assert configured_demo_password() is None


@pytest.mark.parametrize("candidate", [
    "demo1234", "short", " password-that-is-long ", "long-password-with-newline\n",
])
def test_demo_password_rejects_known_weak_or_malformed_values(monkeypatch, candidate):
    monkeypatch.setenv("CROWN_DEMO_PASSWORD", candidate)
    with pytest.raises(CommandError):
        configured_demo_password()


@pytest.mark.django_db
def test_seed_creates_least_privilege_accounts_without_shared_password(monkeypatch):
    monkeypatch.delenv("CROWN_DEMO_PASSWORD", raising=False)
    school = School.objects.create(name="Heritage Christian Academy")
    users = SeedDemoSchool()._ensure_directors(school)
    assert len(users) == 4
    for user in users.values():
        user.refresh_from_db()
        assert user.school_id == school.pk
        assert user.is_superuser is False
        assert user.has_usable_password() is False

    # Reseeding retires legacy overprivileged accounts and known shared passwords.
    head = users["head_user"]
    head.is_superuser = True
    head.set_password("demo1234")
    head.save(update_fields=["is_superuser", "password"])
    SeedDemoSchool()._ensure_directors(school)
    head.refresh_from_db()
    assert head.is_superuser is False
    assert head.has_usable_password() is False


@pytest.mark.django_db
def test_seed_strong_password_is_explicit_and_roles_remain_scoped(monkeypatch):
    monkeypatch.setenv("CROWN_DEMO_PASSWORD", STRONG_DEMO_PASSWORD)
    school = School.objects.create(name="Heritage Christian Academy")
    users = SeedDemoSchool()._ensure_directors(school)
    for user in users.values():
        user.refresh_from_db()
        assert user.check_password(STRONG_DEMO_PASSWORD)
        assert not user.is_superuser
    monkeypatch.delenv("CROWN_DEMO_PASSWORD", raising=False)
    SeedDemoSchool()._ensure_directors(school)
    for user in users.values():
        user.refresh_from_db()
        assert not user.has_usable_password()


@pytest.mark.django_db
def test_seed_does_not_claim_a_username_owned_by_another_school(monkeypatch):
    monkeypatch.delenv("CROWN_DEMO_PASSWORD", raising=False)
    real_school = School.objects.create(name="Customer Academy")
    demo_school = School.objects.create(name="Heritage Christian Academy")
    original = UserAccount.objects.create_user(
        username="head@crown-demo.local",
        email="head@crown-demo.local",
        school=real_school,
        password=STRONG_DEMO_PASSWORD,
    )
    with pytest.raises(CommandError, match="cross-school"):
        SeedDemoSchool()._ensure_directors(demo_school)
    original.refresh_from_db()
    assert original.school_id == real_school.pk
    assert original.check_password(STRONG_DEMO_PASSWORD)


@pytest.mark.django_db
def test_explicit_reset_does_not_select_an_arbitrary_school(monkeypatch):
    monkeypatch.setenv("CROWN_DEMO_PASSWORD", STRONG_DEMO_PASSWORD)
    monkeypatch.delenv("CROWN_DEMO_SCHOOL_ID", raising=False)
    School.objects.create(name="Customer Academy")
    with pytest.raises(CommandError, match="school-id"):
        call_command("reset_demo_passwords")


@pytest.mark.django_db
def test_explicit_reset_rejects_nonheritage_tenant(monkeypatch):
    monkeypatch.setenv("CROWN_DEMO_PASSWORD", STRONG_DEMO_PASSWORD)
    customer = School.objects.create(name="Customer Academy")
    with pytest.raises(CommandError, match="Heritage Christian Academy"):
        call_command("reset_demo_passwords", school_id=str(customer.pk))


@pytest.mark.django_db
def test_explicit_reset_rejects_cross_school_user_before_any_write(monkeypatch):
    monkeypatch.setenv("CROWN_DEMO_PASSWORD", STRONG_DEMO_PASSWORD)
    demo = School.objects.create(name="Heritage Christian Academy")
    customer = School.objects.create(name="Customer Academy")
    owner = UserAccount.objects.create_user(
        username="teacher",
        email="teacher@customer.invalid",
        school=customer,
        password="customer-owned-password--2026",
    )
    with pytest.raises(CommandError, match="another school"):
        call_command("reset_demo_passwords", school_id=str(demo.pk))
    owner.refresh_from_db()
    assert owner.school_id == customer.pk
    assert owner.check_password("customer-owned-password--2026")


@pytest.mark.django_db
def test_explicit_reset_scopes_accounts_and_removes_superuser_grant(monkeypatch):
    monkeypatch.setenv("CROWN_DEMO_PASSWORD", STRONG_DEMO_PASSWORD)
    school = School.objects.create(name="Heritage Christian Academy")
    head = UserAccount.objects.create_user(
        username="head@crown-demo.local",
        email="head@crown-demo.local",
        school=school,
        password="demo1234",
        is_superuser=True,
    )
    call_command("reset_demo_passwords", school_id=str(school.pk))
    head.refresh_from_db()
    assert head.is_superuser is False
    assert head.check_password(STRONG_DEMO_PASSWORD)
    teacher = UserAccount.objects.get(username="teacher")
    assert teacher.school_id == school.pk
    assert teacher.is_superuser is False
    assert teacher.check_password(STRONG_DEMO_PASSWORD)


def test_local_demo_seed_safety_rejects_production_environment(monkeypatch):
    from core.demo_seed_safety import require_local_demo_seed

    monkeypatch.setenv("CROWN_ENV", "production")
    with pytest.raises(CommandError, match="production"):
        require_local_demo_seed(operation="school seeding")


def test_local_demo_seed_safety_rejects_any_hosted_runtime(monkeypatch):
    from core.demo_seed_safety import require_local_demo_seed

    monkeypatch.setenv("CROWN_ENV", "development")
    monkeypatch.setenv("WEBSITE_HOSTNAME", "dev.example.invalid")
    with pytest.raises(CommandError, match="hosted"):
        require_local_demo_seed(operation="password reset")


def test_wipe_requires_local_confirmation_and_sqlite(monkeypatch, settings):
    from core.demo_seed_safety import require_local_demo_wipe

    monkeypatch.setenv("CROWN_ENV", "local")
    monkeypatch.delenv("WEBSITE_HOSTNAME", raising=False)
    monkeypatch.delenv("WEBSITE_INSTANCE_ID", raising=False)
    monkeypatch.delenv("AZURE_ENVIRONMENT", raising=False)
    monkeypatch.setenv("CROWN_ALLOW_DEMO_WIPE", "true")
    with pytest.raises(CommandError, match="--confirm-demo-wipe"):
        require_local_demo_wipe(school_name="Heritage Christian Academy", confirmed=False)
    with pytest.raises(CommandError, match="limited"):
        require_local_demo_wipe(school_name="Customer School", confirmed=True)
    previous = settings.DATABASES["default"]
    settings.DATABASES = {"default": {**previous, "ENGINE": "django.db.backends.postgresql"}}
    with pytest.raises(CommandError, match="SQLite"):
        require_local_demo_wipe(school_name="Heritage Christian Academy", confirmed=True)


@pytest.mark.django_db
def test_demo_wipe_denies_before_creating_a_school(monkeypatch):
    from core.models import School

    monkeypatch.setenv("CROWN_ENV", "local")
    monkeypatch.delenv("CROWN_ALLOW_DEMO_WIPE", raising=False)
    with pytest.raises(CommandError, match="--confirm-demo-wipe"):
        call_command("seed_demo_school", wipe=True)
    assert not School.objects.filter(name="Heritage Christian Academy").exists()


@pytest.mark.django_db
def test_reset_refuses_hosted_tenant_even_with_valid_secret(monkeypatch):
    monkeypatch.setenv("CROWN_ENV", "production")
    monkeypatch.setenv("CROWN_DEMO_PASSWORD", STRONG_DEMO_PASSWORD)
    school = School.objects.create(name="Heritage Christian Academy")
    with pytest.raises(CommandError, match="production"):
        call_command("reset_demo_passwords", school_id=str(school.pk))
    assert not UserAccount.objects.filter(school=school).exists()


def test_active_demo_diagnostics_have_no_default_secret_or_token_excerpt():
    """Prevent retired shared credentials and token excerpts in diagnostic files."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    for relative in (
        "scripts/demo-status.ps1",
        "scripts/manual_proof_check.py",
        "scripts/manual_batch_sanity.py",
    ):
        content = (root / relative).read_text(encoding="utf-8")
        assert "demo1234" not in content, relative
        assert "token[:30]" not in content, relative
    assert not (root / "frontend/dashboards/login_test.json").exists()

def test_realism_pack_rejects_missing_fixture_approval_before_school_creation(
    monkeypatch, settings
):
    """No school seeding may precede the legacy fixture safety preflight."""
    from unittest.mock import patch

    from core.management.commands.seed_heritage_realism_pack import (
        Command as HeritageRealismPack,
    )

    original = settings.DATABASES["default"]
    settings.DATABASES = {
        "default": {**original, "ENGINE": "django.db.backends.sqlite3"}
    }
    monkeypatch.delenv("CROWN_ALLOW_LEGACY_FIXTURE_SEED", raising=False)
    with patch(
        "core.management.commands.seed_heritage_realism_pack.call_command"
    ) as seed_school:
        with pytest.raises(
            CommandError, match="CROWN_ALLOW_LEGACY_FIXTURE_SEED=true is required"
        ):
            HeritageRealismPack().handle(no_comms=True, no_finance_scripts=True)
    seed_school.assert_not_called()


def test_realism_pack_refuses_scheduling_without_opt_in_before_school_creation(
    monkeypatch, settings
):
    """The orchestrator must not partially seed if scheduling is unauthorized."""
    from unittest.mock import patch

    from core.management.commands.seed_heritage_realism_pack import (
        Command as HeritageRealismPack,
    )

    original = settings.DATABASES["default"]
    settings.DATABASES = {
        "default": {**original, "ENGINE": "django.db.backends.sqlite3"}
    }
    monkeypatch.setenv("CROWN_ALLOW_LEGACY_FIXTURE_SEED", "true")
    monkeypatch.delenv("CROWN_ALLOW_LEGACY_SCHEDULING_SEED", raising=False)
    with patch(
        "core.management.commands.seed_heritage_realism_pack.call_command"
    ) as seed_school:
        with pytest.raises(
            CommandError, match="CROWN_ALLOW_LEGACY_SCHEDULING_SEED=true"
        ):
            HeritageRealismPack().handle(no_comms=True, no_finance_scripts=True)
    seed_school.assert_not_called()


def test_realism_pack_temporarily_binds_only_verified_heritage_school(monkeypatch):
    """The script's required explicit tenant selection must be restored."""
    import os

    from core.management.commands.seed_heritage_realism_pack import (
        _bound_scheduling_school_id,
    )

    school_id = "3a234a31-0a63-4e8a-8f0a-8128f7b2e2fa"
    monkeypatch.delenv("CROWN_LEGACY_SCHEDULING_SCHOOL_ID", raising=False)
    with _bound_scheduling_school_id(school_id):
        assert os.getenv("CROWN_LEGACY_SCHEDULING_SCHOOL_ID") == school_id
    assert "CROWN_LEGACY_SCHEDULING_SCHOOL_ID" not in os.environ

    monkeypatch.setenv(
        "CROWN_LEGACY_SCHEDULING_SCHOOL_ID",
        "26399875-730d-49af-8264-65e3c72f6c23",
    )
    with pytest.raises(CommandError, match="conflicts"):
        with _bound_scheduling_school_id(school_id):
            pass
    assert os.environ["CROWN_LEGACY_SCHEDULING_SCHOOL_ID"] != school_id


@pytest.mark.django_db
def test_seed_refuses_customer_school_before_writes(monkeypatch):
    School.objects.create(name="Customer Academy")
    with pytest.raises(CommandError, match="isolated single-school"):
        call_command("seed_demo_school", students=1)
    assert not School.objects.filter(name="Heritage Christian Academy").exists()


@pytest.mark.django_db
def test_seed_refuses_arbitrary_named_school(monkeypatch):
    with pytest.raises(CommandError, match="restricted to Heritage"):
        call_command("seed_demo_school", school_name="Customer Academy", students=1)
    assert not School.objects.exists()


@pytest.mark.django_db
def test_demo_wipe_requires_exact_existing_school_uuid(monkeypatch):
    monkeypatch.setenv("CROWN_ALLOW_DEMO_WIPE", "true")
    school = School.objects.create(name="Heritage Christian Academy")
    with pytest.raises(CommandError, match="--school-id"):
        call_command("seed_demo_school", wipe=True, confirm_demo_wipe=True)
    with pytest.raises(CommandError, match="exact existing Heritage"):
        call_command(
            "seed_demo_school", wipe=True, confirm_demo_wipe=True,
            school_id="00000000-0000-4000-8000-000000000000",
        )
    assert School.objects.filter(pk=school.pk).exists()


@pytest.mark.django_db
def test_demo_wipe_preserves_foreign_school_audit_events(monkeypatch):
    from financial_aid.models import AidAuditEvent

    monkeypatch.setenv("CROWN_ALLOW_DEMO_WIPE", "true")
    heritage = School.objects.create(name="Heritage Christian Academy")
    foreign = School.objects.create(name="Customer Academy")
    demo_user = UserAccount.objects.create_user(
        username="demo-only", email="demo-only@example.invalid",
        school=heritage, password="fixture-only-password",
    )
    event = AidAuditEvent.objects.create(
        school_id=foreign.pk, event_type="TEST", entity_type="TEST",
        entity_id=heritage.pk, actor_user_id=demo_user.pk,
    )
    from core.management.commands.seed_demo_school import Command as Seed
    with pytest.raises(CommandError, match="cross-school audit"):
        Seed()._wipe_school(heritage)
    assert AidAuditEvent.objects.filter(pk=event.pk).exists()
    assert UserAccount.objects.filter(pk=demo_user.pk).exists()
