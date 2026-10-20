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
from core.management.commands.golden_path_bootstrap import (
    _verify_golden_path_runtime,
    seed_admissions_funnel,
)
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
def test_bootstrap_rejects_existing_foreign_admin_without_escalation(
    local_golden_path_environment,
):
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
def test_bootstrap_rejects_non_demo_school_before_account_changes(
    local_golden_path_environment,
):
    other = School.objects.create(name="Actual Customer School")
    with pytest.raises(CommandError, match="non-demo school"):
        call_command("golden_path_bootstrap", school_id=str(other.id), force=True)
    assert not UserAccount.objects.filter(username="admin").exists()


@pytest.mark.django_db
def test_bootstrap_rejects_production_even_with_demo_password(
    local_golden_path_environment, monkeypatch,
):
    monkeypatch.setenv("CROWN_ENV", "production")
    school = School.objects.create(name="Crown Demo School")
    with pytest.raises(CommandError, match="prohibited in production"):
        call_command("golden_path_bootstrap", school_id=str(school.pk))
    assert not UserAccount.objects.filter(username="admin").exists()



@pytest.fixture
def local_golden_path_environment(monkeypatch, settings):
    """Isolate safety tests from the test runner's ambient environment."""
    for key in (
        "CROWN_ENV", "DJANGO_ENV", "ENVIRONMENT", "APP_ENV",
        "AZURE_ENVIRONMENT", "WEBSITE_HOSTNAME", "WEBSITE_INSTANCE_ID",
        "CROWN_GOLDEN_PATH_SCHOOL_ID",
    ):
        monkeypatch.delenv(key, raising=False)
    for key in ("CROWN_ENV", "DJANGO_ENV", "ENVIRONMENT", "APP_ENV", "AZURE_ENVIRONMENT"):
        setattr(settings, key, "")
    monkeypatch.setenv("CROWN_ENV", "local")
    monkeypatch.setenv("CROWN_DEMO_PASSWORD", "A-very-long-only-local-2026-secret")


@pytest.mark.parametrize("label", ["staging", "sandbox", "ci"])
@pytest.mark.parametrize(
    "source,key",
    [
        ("env", "CROWN_ENV"),
        ("env", "DJANGO_ENV"),
        ("env", "APP_ENV"),
        ("env", "AZURE_ENVIRONMENT"),
        ("settings", "DJANGO_ENV"),
        ("settings", "APP_ENV"),
    ],
)
@pytest.mark.django_db
def test_bootstrap_rejects_unsupported_labels_before_any_writes(
    local_golden_path_environment, monkeypatch, settings, source, key, label,
):
    if source == "env":
        monkeypatch.setenv(key, label)
    else:
        setattr(settings, key, label)
    with pytest.raises(CommandError, match="unsupported environment label"):
        call_command("golden_path_bootstrap", school_id=str(uuid.uuid4()))
    assert not UserAccount.objects.filter(username="admin").exists()
    assert not School.objects.exists()
    from core.models_seed import SeedRun
    assert not SeedRun.objects.exists()


@pytest.mark.parametrize("production_source", ["DJANGO_ENV", "settings.DJANGO_ENV"])
@pytest.mark.django_db
def test_bootstrap_rejects_production_marker_from_all_sources(
    local_golden_path_environment, monkeypatch, settings, production_source,
):
    if production_source.startswith("settings."):
        settings.DJANGO_ENV = "production"
    else:
        monkeypatch.setenv("DJANGO_ENV", "production")
    with pytest.raises(CommandError, match="prohibited in production"):
        call_command("golden_path_bootstrap", school_id=str(uuid.uuid4()))
    assert not UserAccount.objects.filter(username="admin").exists()
    from core.models_seed import SeedRun
    assert not SeedRun.objects.exists()


def test_bootstrap_rejects_conflicting_local_and_dev_labels(
    local_golden_path_environment, monkeypatch,
):
    monkeypatch.setenv("DJANGO_ENV", "development")
    with pytest.raises(CommandError, match="conflicting local and DEV"):
        _verify_golden_path_runtime()


@pytest.mark.parametrize(
    "marker,value",
    [
        ("WEBSITE_INSTANCE_ID", "azure-instance-without-host"),
        ("AZURE_ENVIRONMENT", "dev"),
        ("WEBSITE_HOSTNAME", "crown-api-prod.azurewebsites.net"),
    ],
)
def test_bootstrap_requires_verified_host_for_hosted_runtimes(
    local_golden_path_environment, monkeypatch, marker, value,
):
    monkeypatch.setenv("CROWN_ENV", "dev")
    monkeypatch.setenv(marker, value)
    with pytest.raises(CommandError, match="verified DEV host"):
        _verify_golden_path_runtime()


def test_bootstrap_accepts_verified_hosted_dev_classifier(
    local_golden_path_environment, monkeypatch,
):
    monkeypatch.setenv("CROWN_ENV", "dev")
    monkeypatch.setenv("DJANGO_ENV", "development")
    monkeypatch.setenv("WEBSITE_HOSTNAME", "crown2026-api-dev.azurewebsites.net")
    monkeypatch.setenv("WEBSITE_INSTANCE_ID", "fictional-test-instance")
    assert _verify_golden_path_runtime() is False


@pytest.mark.django_db
def test_bootstrap_rejects_gp_school_uuid_on_hosted_dev(
    local_golden_path_environment, monkeypatch,
):
    # Only exercise this check against the ephemeral Django test database.
    school = School.objects.create(name="GP School")
    monkeypatch.setenv("CROWN_ENV", "dev")
    monkeypatch.setenv("WEBSITE_HOSTNAME", "crown2026-api-dev.azurewebsites.net")
    with pytest.raises(CommandError, match="non-demo school"):
        call_command("golden_path_bootstrap", school_id=str(school.id), verbosity=0)
    assert not UserAccount.objects.filter(username="admin").exists()


@pytest.mark.parametrize("school_selection", ["option", "environment"])
@pytest.mark.django_db
def test_local_gp_school_can_be_selected_for_subsequent_run(
    local_golden_path_environment, monkeypatch, settings, school_selection,
):
    if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
        pytest.skip("Golden Path local bootstraps require an isolated SQLite test DB")
    call_command("golden_path_bootstrap", verbosity=0)
    school = School.objects.get(name="GP School")
    if school_selection == "environment":
        monkeypatch.setenv("CROWN_GOLDEN_PATH_SCHOOL_ID", str(school.id))
        call_command("golden_path_bootstrap", verbosity=0)
    else:
        call_command("golden_path_bootstrap", school_id=str(school.id), verbosity=0)
    assert School.objects.filter(pk=school.id, name="GP School").count() == 1
    assert UserAccount.objects.filter(username="admin", school_id=school.id).count() == 1



@pytest.mark.django_db
def test_bootstrap_rejects_unlabelled_sqlite_before_writes(
    local_golden_path_environment, monkeypatch, settings,
):
    monkeypatch.delenv("CROWN_ENV", raising=False)
    assert not any(
        getattr(settings, key, "") for key in (
            "CROWN_ENV", "DJANGO_ENV", "ENVIRONMENT", "APP_ENV", "AZURE_ENVIRONMENT"
        )
    )
    with pytest.raises(CommandError, match="explicit local or DEV label"):
        call_command("golden_path_bootstrap", school_id=str(uuid.uuid4()))
    assert not UserAccount.objects.filter(username="admin").exists()
    from core.models_seed import SeedRun
    assert not SeedRun.objects.exists()


def test_bootstrap_rejects_nonlocal_db_without_verified_dev_host(
    local_golden_path_environment, monkeypatch, settings,
):
    monkeypatch.setitem(
        settings.DATABASES["default"], "ENGINE", "django.db.backends.postgresql"
    )
    with pytest.raises(CommandError, match="verified DEV or isolated local runtime"):
        _verify_golden_path_runtime()
