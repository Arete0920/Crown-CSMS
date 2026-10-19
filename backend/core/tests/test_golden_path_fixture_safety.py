"""Tenant safety and business-realism regressions for Golden Path fixtures."""

from __future__ import annotations

import uuid

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from applications.models import Application, Applicant, ApplicationEvent
from core.golden_path_fixture_profiles import (
    GOLDEN_PATH_FUNNEL_SIZE,
    applicant_identity,
    fixture_uuid,
)
from core.management.commands.golden_path_bootstrap import seed_admissions_funnel
from core.models import School, UserAccount
from households.models import Household


def test_fictional_applicant_profiles_are_distinct_and_repeatable():
    profiles = [applicant_identity(index) for index in range(GOLDEN_PATH_FUNNEL_SIZE)]
    assert len(profiles) == 94
    assert len(set(profiles)) == 94
    assert all(first and last and first != "Student" and last != "Applicant" for first, last in profiles)
    assert profiles[0] == applicant_identity(0)
    with pytest.raises(ValueError):
        applicant_identity(GOLDEN_PATH_FUNNEL_SIZE)


def test_fixture_ids_are_deterministic_and_tenant_scoped():
    school_a, school_b = uuid.uuid4(), uuid.uuid4()
    assert fixture_uuid(school_a, "aid-award", 1) == fixture_uuid(school_a, "aid-award", 1)
    assert fixture_uuid(school_a, "aid-award", 1) != fixture_uuid(school_b, "aid-award", 1)
    assert fixture_uuid(school_a, "aid-award", 1) != fixture_uuid(school_a, "aid-event", 1)


@pytest.mark.django_db
def test_admissions_seed_creates_separate_fictional_households():
    school = School.objects.create(name="Crown Demo School")
    result = seed_admissions_funnel(school_id=school.id)
    assert result == {"skipped": False, "pipeline_total": 94}
    applicants = Applicant.objects.filter(school_id=school.id).select_related("application__household")
    assert applicants.count() == GOLDEN_PATH_FUNNEL_SIZE
    assert applicants.values("application__household_id").distinct().count() == 94
    assert all(a.first_name != "Student" and a.last_name != "Applicant" for a in applicants)
    assert all(a.application.household.school_id == school.id for a in applicants)


@pytest.mark.django_db
def test_force_seed_does_not_delete_existing_application_or_events():
    school = School.objects.create(name="Crown Demo School")
    household = Household.objects.create(school_id=school.id, name="Existing Family")
    application = Application.objects.create(school_id=school.id, household=household)
    Applicant.objects.create(
        school_id=school.id, application=application,
        first_name="Abigail", last_name="Existing",
    )
    event = ApplicationEvent.objects.create(
        school_id=school.id, application=application,
        event_type="application_submitted", payload={"source": "existing"},
    )
    result = seed_admissions_funnel(school_id=school.id, force=True)
    assert result["skipped"] is True
    assert Application.objects.filter(pk=application.pk).exists()
    assert Applicant.objects.filter(application=application).count() == 1
    assert ApplicationEvent.objects.filter(pk=event.pk).exists()


@pytest.mark.django_db
def test_seed_preserves_applications_in_another_tenant():
    school_a = School.objects.create(name="Crown Demo School")
    school_b = School.objects.create(name="Customer Academy")
    household = Household.objects.create(school_id=school_b.id, name="Customer Family")
    application = Application.objects.create(school_id=school_b.id, household=household)
    Applicant.objects.create(
        school_id=school_b.id, application=application,
        first_name="Rachel", last_name="Wright",
    )
    assert seed_admissions_funnel(school_id=school_a.id, force=True)["pipeline_total"] == 94
    assert Application.objects.filter(school_id=school_b.id).count() == 1
    assert Applicant.objects.filter(school_id=school_b.id).count() == 1


@pytest.mark.django_db
def test_bootstrap_rejects_existing_foreign_admin_without_escalation(monkeypatch):
    monkeypatch.setenv("CROWN_ENV", "local")
    monkeypatch.setenv("CROWN_DEMO_PASSWORD", "A-very-long-only-local-2026-secret")
    target = School.objects.create(name="Crown Demo School")
    other = School.objects.create(name="Customer Academy")
    original = UserAccount.objects.create_user(
        username="admin", email="admin@local.test", school=other,
        password="original-customer-password-2026", is_superuser=False,
    )
    with pytest.raises(CommandError, match="unrelated administrator"):
        call_command("golden_path_bootstrap", school_id=str(target.id), force=True)
    original.refresh_from_db()
    assert original.school_id == other.id
    assert original.check_password("original-customer-password-2026")
    assert not original.is_superuser


@pytest.mark.django_db
def test_bootstrap_rejects_non_demo_school_before_account_changes(monkeypatch):
    monkeypatch.setenv("CROWN_ENV", "local")
    monkeypatch.setenv("CROWN_DEMO_PASSWORD", "A-very-long-only-local-2026-secret")
    other = School.objects.create(name="Actual Customer School")
    with pytest.raises(CommandError, match="non-demo school"):
        call_command("golden_path_bootstrap", school_id=str(other.id), force=True)
    assert not UserAccount.objects.filter(username="admin").exists()


@pytest.mark.django_db
def test_bootstrap_rejects_production_even_with_demo_password(monkeypatch):
    monkeypatch.setenv("CROWN_ENV", "production")
    monkeypatch.setenv("CROWN_DEMO_PASSWORD", "A-very-long-only-local-2026-secret")
    school = School.objects.create(name="Crown Demo School")
    with pytest.raises(CommandError, match="prohibited in production"):
        call_command("golden_path_bootstrap", school_id=str(school.pk))
    assert not UserAccount.objects.filter(username="admin").exists()
