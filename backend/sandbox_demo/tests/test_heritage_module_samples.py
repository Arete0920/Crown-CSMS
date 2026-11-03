"""Local fictional fixture regression: persistence, replay, and fail-closed guards."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from django.core.management.base import CommandError
from django.core.management import call_command

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
    from aid.models import AidApplication as CanonicalAidApplication
    from aid.models import AidAward as CanonicalAidAward
    from aid.models import AidAuditEvent as CanonicalAidAuditEvent
    from aftercare.models import AftercareEnrollment
    from aftercare.daycare_models import (
        DaycareSite, DaycareRoom, DaycareEnrollment, DaycareGuardianAuthority,
    )
    with _setup_local(monkeypatch, settings):
        first = seed_heritage_module_samples()
        second = seed_heritage_module_samples()
    assert first == second
    assert all(value == 1 for value in first.values())
    canonical = CanonicalAidApplication.objects.get(
        school_id=HERITAGE_ID, family_id=fixed_id("canonical-aid-family"),
    )
    assert canonical.status == CanonicalAidApplication.STATUS_SUBMITTED
    offered = CanonicalAidAward.objects.get(
        school_id=HERITAGE_ID, aid_application=canonical,
        student_id=fixed_id("canonical-aid-student"),
    )
    assert offered.decision_status == CanonicalAidAward.DECISION_OFFERED
    assert offered.awarded_cents == 25000
    assert offered.ledger_entry_id is None
    assert offered.decided_by_id is None
    assert CanonicalAidAuditEvent.objects.filter(
        school_id=HERITAGE_ID,
        entity_type=CanonicalAidAuditEvent.ENTITY_AWARD,
        entity_id=str(offered.pk),
        action="AWARD_OFFERED",
    ).count() == 1
    assert CanonicalAidAuditEvent.objects.filter(
        school_id=HERITAGE_ID,
        entity_type=CanonicalAidAuditEvent.ENTITY_AWARD,
        entity_id=str(offered.pk),
        action__in=("AWARD_ACCEPTED", "LEDGER_POSTED"),
    ).count() == 0
    assert FinancialAidApplication.objects.filter(
        school_id=HERITAGE_ID, pk=fixed_id("aid-application")
    ).count() == 1
    application = FinancialAidApplication.objects.get(
        school_id=HERITAGE_ID, pk=fixed_id("aid-application")
    )
    assert application.status == "in_review"
    award = AidAward.objects.get(
        school_id=HERITAGE_ID, application=application
    )
    assert award.approved_by_user_id is None
    assert award.amount >= 0
    assert "Need Index" in award.rationale
    from financial_aid.models import AidAuditEvent
    assert AidAuditEvent.objects.filter(
        school_id=HERITAGE_ID,
        entity_id=application.pk,
        event_type="APPLICATION_READY_FOR_REVIEW",
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


@pytest.mark.parametrize("tamper", [
    "ready_enrollment", "cancelled_enrollment", "activated_room",
])
def test_diadem_blocked_sample_reseed_refuses_changed_custody_posture(
    monkeypatch, settings, tamper,
):
    """Do not silently accept a changed fictional daycare readiness state."""
    from aftercare.daycare_models import DaycareEnrollment, DaycareRoom

    with _setup_local(monkeypatch, settings):
        seed_heritage_module_samples()
        if tamper == "ready_enrollment":
            DaycareEnrollment.objects.filter(
                pk=fixed_id("daycare-blocked-enrollment"),
            ).update(readiness="READY")
        elif tamper == "cancelled_enrollment":
            DaycareEnrollment.objects.filter(
                pk=fixed_id("daycare-blocked-enrollment"),
            ).update(status="CANCELLED")
        else:
            DaycareRoom.objects.filter(
                pk=fixed_id("daycare-room-unapproved"),
            ).update(is_active=True)

        with pytest.raises(CommandError, match="Diadem blocked sample changed"):
            seed_heritage_module_samples()

    enrollment = DaycareEnrollment.objects.get(pk=fixed_id("daycare-blocked-enrollment"))
    room = DaycareRoom.objects.get(pk=fixed_id("daycare-room-unapproved"))
    if tamper == "ready_enrollment":
        assert enrollment.readiness == "READY"
    elif tamper == "cancelled_enrollment":
        assert enrollment.status == "CANCELLED"
    else:
        assert room.is_active


@pytest.mark.parametrize("next_state", ["UNDER_REVIEW", "NEEDS_INFO"])
def test_canonical_jireh_review_progress_preserves_offered_evidence(
    monkeypatch, settings, next_state,
):
    """Re-seeding a legitimate review state must not report zero canonical apps."""
    from aid.models import AidApplication, AidAward, AidAuditEvent

    with _setup_local(monkeypatch, settings):
        initial = seed_heritage_module_samples()
        app = AidApplication.objects.get(
            school_id=HERITAGE_ID, family_id=fixed_id("canonical-aid-family"),
        )
        app.set_status(next_state, details={"fictional_local_only": True})
        repeated = seed_heritage_module_samples()
        app.refresh_from_db()

    assert repeated == initial
    assert repeated["canonical_jireh_applications"] == 1
    assert app.status == next_state
    offered = AidAward.objects.get(school_id=HERITAGE_ID, aid_application=app)
    assert offered.decision_status == AidAward.DECISION_OFFERED
    assert offered.ledger_entry_id is None
    assert AidAuditEvent.objects.filter(
        school_id=HERITAGE_ID,
        entity_type=AidAuditEvent.ENTITY_AWARD,
        entity_id=str(offered.pk),
        action="AWARD_OFFERED",
    ).count() == 1


def test_canonical_jireh_award_tampering_aborts_reseed_and_rolls_back(
    monkeypatch, settings,
):
    from aid.models import AidAward as CanonicalAidAward
    from aid.models import AidAuditEvent as CanonicalAidAuditEvent

    with _setup_local(monkeypatch, settings):
        seed_heritage_module_samples()
        award = CanonicalAidAward.objects.get(
            school_id=HERITAGE_ID,
            student_id=fixed_id("canonical-aid-student"),
        )
        award.decision_status = CanonicalAidAward.DECISION_ACCEPTED
        award.save(update_fields=["decision_status"])
        with pytest.raises(CommandError, match="unposted offered award"):
            seed_heritage_module_samples()
    assert CanonicalAidAward.objects.filter(
        pk=award.pk, decision_status=CanonicalAidAward.DECISION_ACCEPTED,
    ).exists()
    assert CanonicalAidAuditEvent.objects.filter(
        school_id=HERITAGE_ID,
        entity_type=CanonicalAidAuditEvent.ENTITY_AWARD,
        entity_id=str(award.pk),
        action="AWARD_OFFERED",
    ).count() == 1


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


def test_direct_canonical_offer_entrypoint_enforces_local_boundary(monkeypatch, settings):
    from core.models import Family as CoreFamily, School
    from sandbox_demo import heritage_module_samples as samples

    with _setup_local(monkeypatch, settings):
        school = School.objects.get(pk=HERITAGE_ID)
        def deny_nonlocal():
            raise CommandError("Direct canonical offer forbidden outside isolated local SQLite")
        monkeypatch.setattr(samples, "_require_isolated_local_database", deny_nonlocal)
        with pytest.raises(CommandError, match="isolated local SQLite"):
            samples._seed_canonical_offered_jireh(school)
    assert not CoreFamily.objects.filter(pk=fixed_id("canonical-aid-family")).exists()


def test_direct_canonical_offer_rejects_foreign_school_before_write(monkeypatch, settings):
    from core.models import Family as CoreFamily, School
    from sandbox_demo.heritage_module_samples import _seed_canonical_offered_jireh

    with _setup_local(monkeypatch, settings):
        foreign = School.objects.create(name="Foreign Synthetic School")
        with pytest.raises(CommandError, match="active fictional Heritage school"):
            _seed_canonical_offered_jireh(foreign)
    assert not CoreFamily.objects.filter(pk=fixed_id("canonical-aid-family")).exists()
