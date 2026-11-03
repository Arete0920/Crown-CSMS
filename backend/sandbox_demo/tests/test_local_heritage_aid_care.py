"""Fictional Heritage source fixtures must fail closed outside local scope."""
from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest
from django.core.management.base import CommandError
from django.test import override_settings

from aftercare.models import AftercareAttendance, AftercareEnrollment
from core.models import Family, School, Student as CoreStudent, StudentIdentityLink
from financial_aid.models import AidAward, FinancialAidApplication
from households.models import Household, Student as HouseholdStudent
from sandbox_demo.catalog import SANDBOX_SCHOOLS
from sandbox_demo.management.commands import seed_local_heritage_aid_care as fixture

pytestmark = pytest.mark.django_db


def _identity():
    spec = SANDBOX_SCHOOLS["heritage-core"]
    school = School.objects.create(id=UUID(spec.id), name=spec.name, is_active=True)
    family = Family.objects.create(school=school, family_name="Fictional Care/Aid Family")
    core = CoreStudent.objects.create(
        school=school, family=family, student_number="HCA-AID-CARE-TEST",
        first_name="Avery", last_name="Example", dob=date(2014, 5, 14),
    )
    household = Household.objects.create(
        school_id=school.pk, name="Fictional Aid/Care Household"
    )
    student = HouseholdStudent.objects.create(
        school_id=school.pk, household=household,
        first_name="Avery", last_name="Example", grade_level="6",
    )
    identity = StudentIdentityLink.objects.create(
        school=school, core_student=core, compatibility_student=student,
        source=StudentIdentityLink.SOURCE_RECONCILIATION,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
        evidence_reference="fictional-local-aid-care-test",
    )
    return school, household, student, identity


@override_settings(DEBUG=True, CROWN_ENV="local", CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_local_fixture_is_idempotent_and_never_creates_custody_attendance(monkeypatch):
    monkeypatch.setattr(fixture, "_require_isolated_local_database", lambda: None)
    school, household, student, _ = _identity()
    expected = {
        "aid_applications": 1,
        "fictional_nonposted_award_records": 1,
        "before_care_enrollments": 1,
        "after_care_enrollments": 1,
    }
    assert fixture.seed_heritage_aid_and_extended_care() == expected
    assert fixture.seed_heritage_aid_and_extended_care() == expected
    application = FinancialAidApplication.objects.get(
        school_id=school.pk, household_id=household.pk
    )
    award = AidAward.objects.get(school_id=school.pk, application=application)
    assert application.status == "in_review"
    assert award.approved_by_user_id is None
    assert "FICTIONAL" in award.rationale
    assert AftercareEnrollment.objects.filter(school_fk=school).count() == 2
    assert AftercareAttendance.objects.filter(school_fk=school).count() == 0


@override_settings(DEBUG=False, CROWN_ENV="production", CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_nonlocal_run_refuses_writes():
    school, _, _, _ = _identity()
    with pytest.raises(CommandError):
        fixture.seed_heritage_aid_and_extended_care()
    assert not FinancialAidApplication.objects.filter(school_id=school.pk).exists()
    assert not AftercareEnrollment.objects.filter(school_fk=school).exists()


@override_settings(DEBUG=True, CROWN_ENV="local", CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_unverified_identity_does_not_seed_records(monkeypatch):
    monkeypatch.setattr(fixture, "_require_isolated_local_database", lambda: None)
    school, _, _, identity = _identity()
    identity.verification_status = StudentIdentityLink.STATUS_PENDING
    identity.save(update_fields=["verification_status"])
    with pytest.raises(CommandError, match="Verified same-school"):
        fixture.seed_heritage_aid_and_extended_care()
    assert not FinancialAidApplication.objects.filter(school_id=school.pk).exists()
    assert not AftercareEnrollment.objects.filter(school_fk=school).exists()


@override_settings(DEBUG=True, CROWN_ENV="local", CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_disabled_enrollment_not_reactivated_or_operator_award_rewritten(monkeypatch):
    monkeypatch.setattr(fixture, "_require_isolated_local_database", lambda: None)
    school, household, student, _ = _identity()
    fixture.seed_heritage_aid_and_extended_care()
    enrollment = AftercareEnrollment.objects.get(
        school_fk=school, student_fk=student, care_session="AM"
    )
    enrollment.is_active = False
    enrollment.save(update_fields=["is_active"])
    award = AidAward.objects.get(school_id=school.pk, application__household_id=household.pk)
    award.amount = Decimal("2000.00")
    award.save(update_fields=["amount"])
    with pytest.raises(CommandError, match="disabled"):
        fixture.seed_heritage_aid_and_extended_care()
    enrollment.refresh_from_db()
    award.refresh_from_db()
    assert enrollment.is_active is False
    assert award.amount == Decimal("2000.00")
    assert AftercareEnrollment.objects.filter(school_fk=school).count() == 2
