"""Fictional Camp must be isolated, idempotent, and noncash."""
from datetime import date
from uuid import UUID

import pytest
from django.core.management.base import CommandError
from django.test import override_settings

from core.models import Family, School, Student as CoreStudent, StudentIdentityLink
from households.models import Household, Student as HouseholdStudent
from subscriptions.models import SchoolModule
from summer_camp.models import SummerCampEnrollment, SummerCampProgram, SummerCampProgramConfig, SummerCampSession
from sandbox_demo.catalog import SANDBOX_SCHOOLS
from sandbox_demo.services import seed_local_heritage_camp

pytestmark = pytest.mark.django_db


def _fictional_heritage_identity():
    spec = SANDBOX_SCHOOLS["heritage-core"]
    school = School.objects.create(id=UUID(spec.id), name=spec.name)
    family = Family.objects.create(school=school, family_name="Fictional Camp Test Family")
    core = CoreStudent.objects.create(
        school=school, family=family, student_number="HCA-PARENT-JORDAN",
        first_name="Jordan", last_name="Reed", dob=date(2013, 2, 15),
    )
    household = Household.objects.create(school_id=school.id, name="Fictional Camp Test Household")
    compatibility = HouseholdStudent.objects.create(
        school_id=school.id, household=household, first_name="Jordan",
        last_name="Reed", grade_level="7",
    )
    StudentIdentityLink.objects.create(
        school=school, core_student=core, compatibility_student=compatibility,
        source=StudentIdentityLink.SOURCE_RECONCILIATION,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
        evidence_reference="synthetic-local-camp-fixture-test",
    )
    return school, compatibility


@override_settings(DEBUG=True, CROWN_ENV="local", CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_camp_local_seed_is_idempotent_and_does_not_claim_cash(monkeypatch):
    from sandbox_demo.management.commands import five_module_demo_preflight
    monkeypatch.setattr(five_module_demo_preflight, "_require_isolated_local_database", lambda: None)
    school, camper = _fictional_heritage_identity()
    SummerCampProgramConfig.objects.create(school=school, camp_name="Operator configuration untouched")

    assert seed_local_heritage_camp()["fictional_camp_registrations"] == 1
    assert seed_local_heritage_camp()["fictional_camp_sessions"] == 1

    assert SchoolModule.objects.filter(school=school, module_key="little_lambs", status="active").count() == 1
    assert SummerCampProgram.objects.filter(school=school).count() == 1
    session = SummerCampSession.objects.get(school=school)
    assert session.status == "PUBLISHED"
    registration = SummerCampEnrollment.objects.get(school=school, session=session, student=camper)
    assert registration.status == "REGISTERED"
    assert registration.payment_status == "NOT_BILLED"
    assert registration.balance_due_cents == 0
    assert registration.readiness_status == "BLOCKED"
    assert SummerCampProgramConfig.objects.get(school=school).camp_name == "Operator configuration untouched"


@override_settings(DEBUG=False, CROWN_ENV="production", CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_camp_local_seed_refuses_a_nonlocal_database_without_writes():
    school, _ = _fictional_heritage_identity()
    with pytest.raises(CommandError):
        seed_local_heritage_camp()
    assert not SchoolModule.objects.filter(school=school).exists()
    assert not SummerCampSession.objects.filter(school=school).exists()

@override_settings(DEBUG=True, CROWN_ENV="local", CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
@pytest.mark.parametrize("state", ["inactive", "suspended", "expired"])
def test_camp_seed_does_not_reactivate_existing_disabled_entitlement(monkeypatch, state):
    from sandbox_demo.management.commands import five_module_demo_preflight
    monkeypatch.setattr(five_module_demo_preflight, "_require_isolated_local_database", lambda: None)
    school, _ = _fictional_heritage_identity()
    license = SchoolModule.objects.create(school=school, module_key="little_lambs", status=state)
    with pytest.raises(RuntimeError, match="entitlement is inactive or expired"):
        seed_local_heritage_camp()
    license.refresh_from_db()
    assert license.status == state
    assert not SummerCampSession.objects.filter(school=school).exists()


@override_settings(DEBUG=True, CROWN_ENV="local", CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
@pytest.mark.parametrize("changed_state", ["session_draft", "registration_waitlisted", "registration_cancelled"])
def test_camp_seed_refuses_modified_operator_state_without_rewriting(monkeypatch, changed_state):
    from sandbox_demo.management.commands import five_module_demo_preflight
    monkeypatch.setattr(five_module_demo_preflight, "_require_isolated_local_database", lambda: None)
    school, camper = _fictional_heritage_identity()
    seed_local_heritage_camp()
    session = SummerCampSession.objects.get(school=school)
    registration = SummerCampEnrollment.objects.get(school=school, session=session, student=camper)
    if changed_state == "session_draft":
        session.status = "DRAFT"
        session.save(update_fields=["status"])
    else:
        registration.status = "WAITLISTED" if changed_state == "registration_waitlisted" else "CANCELLED"
        registration.save(update_fields=["status"])
    with pytest.raises(RuntimeError, match="not published|registration is not active"):
        seed_local_heritage_camp()
    session.refresh_from_db()
    registration.refresh_from_db()
    assert session.status == ("DRAFT" if changed_state == "session_draft" else "PUBLISHED")
    assert registration.status == (
        "WAITLISTED" if changed_state == "registration_waitlisted"
        else "CANCELLED" if changed_state == "registration_cancelled" else "REGISTERED"
    )
    assert SummerCampSession.objects.filter(school=school).count() == 1
    assert SummerCampEnrollment.objects.filter(school=school).count() == 1
