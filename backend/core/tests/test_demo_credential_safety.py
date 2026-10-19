"""Regression controls for demonstration credentials and tenant-safe reset."""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.demo_credentials import configured_demo_password
from core.management.commands.seed_demo_school import Command as SeedDemoSchool
from core.models import School, UserAccount


STRONG_DEMO_PASSWORD = "Fixture-only--Crown--2026-strong"


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
