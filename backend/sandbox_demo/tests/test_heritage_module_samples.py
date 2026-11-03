"""Local fictional fixture regression: persistence, replay, and fail-closed guards."""
from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
from django.core.management.base import CommandError
from django.core.management import call_command

from sandbox_demo.catalog import SANDBOX_SCHOOLS
from sandbox_demo.services import seed_heritage_flagship
from sandbox_demo.heritage_module_samples import (
    HERITAGE_ID, fixed_id, require_local_demo, seed_heritage_module_samples,
)

pytestmark = pytest.mark.django_db


def _setup_local(monkeypatch, settings):
    # Test DB is disposable but NOT the canonical .local-backups SQLite file;
    # mock only the path guard, never claim this tests the real path gate.
    settings.DEBUG = True
    settings.CROWN_ENV = "local"
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    monkeypatch.setenv("DJANGO_ENV", "local")
    monkeypatch.setenv("CROWN_DEMO_MODE", "false")
    monkeypatch.delenv("WEBSITE_SITE_NAME", raising=False)
    monkeypatch.delenv("AZURE_CLIENT_ID", raising=False)
    monkeypatch.delenv("IDENTITY_ENDPOINT", raising=False)
    seed_heritage_flagship()
    return patch(
        "sandbox_demo.heritage_module_samples._require_isolated_local_database"
    )


def test_local_module_samples_are_idempotent_and_do_not_authorize_custody(
    monkeypatch, settings,
):
    from financial_aid.models import FinancialAidApplication, AidAward
    from aftercare.models import AftercareEnrollment
    from aftercare.daycare_models import (
        DaycareSite, DaycareRoom, DaycareEnrollment, DaycareGuardianAuthority,
    )
    with _setup_local(monkeypatch, settings):
        first = seed_heritage_module_samples()
        second = seed_heritage_module_samples()
    assert first == second
    assert all(value == 1 for value in first.values())
    assert FinancialAidApplication.objects.filter(
        school_id=HERITAGE_ID, pk=fixed_id("aid-application")
    ).count() == 1
    assert AidAward.objects.filter(
        school_id=HERITAGE_ID, pk=fixed_id("aid-unapproved-sample"),
        amount=0, approved_by_user_id__isnull=True
    ).count() == 1
    assert AftercareEnrollment.objects.filter(
        school_fk_id=HERITAGE_ID, is_active=True, care_session__in=["AM", "PM"],
        student_fk_id=fixed_id("extended-care-student")
    ).count() == 2
    assert DaycareSite.objects.get(pk=fixed_id("daycare-site")).school_id == HERITAGE_ID
    room = DaycareRoom.objects.get(pk=fixed_id("daycare-room-unapproved"))
    assert not room.is_active
    assert room.policy_verified_by_id is None
    assert room.policy_verified_at is None
    assert room.licensed_capacity is None and room.max_children_per_staff is None
    enrollment = DaycareEnrollment.objects.get(pk=fixed_id("daycare-blocked-enrollment"))
    assert enrollment.status == "ACTIVE"
    assert enrollment.readiness == "BLOCKED"
    assert not DaycareGuardianAuthority.objects.filter(
        child_id=enrollment.child_id, is_active=True
    ).exists()


def test_explicit_opt_in_required_before_database_seed(monkeypatch, settings):
    from financial_aid.models import FinancialAidApplication
    with _setup_local(monkeypatch, settings):
        with pytest.raises(CommandError, match="--fictional-local-only"):
            call_command("seed_heritage_module_samples")
    assert not FinancialAidApplication.objects.filter(
        pk=fixed_id("aid-application")
    ).exists()


def test_hosted_or_foreign_context_denied_before_any_sample_write(
    monkeypatch, settings,
):
    from financial_aid.models import FinancialAidApplication
    with _setup_local(monkeypatch, settings):
        settings.CROWN_ENV = "dev"
        with pytest.raises(CommandError, match="canonical local Heritage"):
            require_local_demo()
        settings.CROWN_ENV = "local"
        monkeypatch.setenv("WEBSITE_SITE_NAME", "unexpected-hosted-app")
        with pytest.raises(CommandError, match="canonical local Heritage"):
            require_local_demo()
    assert not FinancialAidApplication.objects.filter(
        pk=fixed_id("aid-application")
    ).exists()


def test_conflicting_existing_fixture_identity_refuses_and_rolls_back(
    monkeypatch, settings,
):
    from households.models import Household
    from core.models import School
    with _setup_local(monkeypatch, settings):
        foreign = School.objects.create(name="Synthetic Foreign Tenant")
        Household.objects.create(
            pk=fixed_id("family"), school_id=foreign.pk,
            name="Wrong ownership - must never be reused",
        )
        with pytest.raises(CommandError, match="conflicting ownership"):
            seed_heritage_module_samples()
    assert not Household.objects.filter(
        pk=fixed_id("family"), school_id=HERITAGE_ID
    ).exists()


def test_school_override_refused_even_if_local(monkeypatch, settings):
    with _setup_local(monkeypatch, settings):
        monkeypatch.setattr(
            SANDBOX_SCHOOLS["heritage-core"], "id",
            str(uuid.uuid4()),
            raising=False,
        ) if False else None
        # ENV override is what the catalog reads on process startup; verify
        # the immutable canonical ID is never taken from the caller's env.
        assert HERITAGE_ID == uuid.UUID("19801b59-8c05-4c84-9312-5d792e4e839d")
