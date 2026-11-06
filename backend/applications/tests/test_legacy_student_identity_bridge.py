"""Database regressions for the fail-closed legacy admissions identity bridge."""
from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError

from admissions.models import AdmissionsApplication
from applications.models import Application, Applicant
from applications.views_admissions import _upsert_legacy_admissions_applications
from core.models import (
    AcademicYear, Family, HouseholdFamilyLink, School,
    Student as CoreStudent, StudentIdentityLink,
)
from households.models import Household, Student as CompatibilityStudent

pytestmark = pytest.mark.django_db


@pytest.fixture
def case():
    school = School.objects.create(name=f"Legacy Identity {uuid4().hex[:8]}")
    year = AcademicYear.objects.create(
        school=school, name="2026-2027", start_date=date(2026, 8, 1),
        end_date=date(2027, 6, 30), is_current=True,
    )
    household = Household.objects.create(school_id=school.id, name="Bridge Household")
    family = Family.objects.create(school=school, family_name="Bridge Family")
    HouseholdFamilyLink.objects.create(
        school=school, household_id=household.pk, family=family,
        source=HouseholdFamilyLink.SOURCE_ADMISSIONS,
    )
    app = Application.objects.create(school_id=school.id, household=household, status="DECIDED")
    applicant = Applicant.objects.create(
        school_id=school.id, application=app, first_name="Alex", last_name="Student",
        dob=date(2014, 4, 9), grade_applying_for="5",
    )
    compatibility = CompatibilityStudent.objects.create(
        school_id=school.id, household=household, first_name="Alex",
        last_name="Student", grade_level="5", is_active=True,
    )
    applicant.student = compatibility
    applicant.save(update_fields=["student", "updated_at"])
    core = CoreStudent.objects.create(
        school=school, family=family, student_number=f"REAL-{uuid4().hex[:9]}",
        first_name="Alex", last_name="Student", dob=applicant.dob, status="ACTIVE",
    )
    identity = StudentIdentityLink.objects.create(
        school=school, core_student=core, compatibility_student=compatibility,
        source=StudentIdentityLink.SOURCE_ADMISSIONS,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
        evidence_reference=f"application:{app.id}:applicant:{applicant.id}",
    )
    return SimpleNamespace(
        school=school, year=year, household=household, family=family,
        application=app, applicant=applicant, compatibility=compatibility,
        core=core, identity=identity,
    )


def bridge(case, status="ACCEPTED"):
    return _upsert_legacy_admissions_applications(
        app=case.application, actor_user=None, target_status=status,
    )


def rejected(case, count=1):
    result = bridge(case)
    assert result["state"] == "identity_verification_required", result
    assert result["count"] == 0
    assert AdmissionsApplication.objects.filter(school=case.school).count() == 0
    assert CoreStudent.objects.filter(school=case.school).count() == count


def test_same_name_different_student_is_not_reused(case):
    sibling = CoreStudent.objects.create(
        school=case.school, family=case.family,
        student_number=f"REAL-{uuid4().hex[:9]}",
        first_name="Alex", last_name="Student", dob=case.applicant.dob, status="ACTIVE",
    )
    result = bridge(case)
    assert result["state"] == "accepted"
    assert result["count"] == 1
    assert AdmissionsApplication.objects.get(pk=result["application_ids"][0]).student_id == case.core.id
    sibling.refresh_from_db()
    assert not sibling.admissions_applications.exists()


def test_missing_dob_rejects_without_substituting_current_date(case):
    original = case.core.dob
    case.applicant.dob = None
    case.applicant.save(update_fields=["dob", "updated_at"])
    rejected(case)
    case.core.refresh_from_db()
    assert case.core.dob == original


def test_no_verified_link_cannot_use_name_only(case):
    case.identity.delete()
    rejected(case)
    assert not CoreStudent.objects.filter(
        school=case.school, student_number__startswith="APP-"
    ).exists()


def test_different_application_provenance_rejected(case):
    case.identity.evidence_reference = f"application:{case.application.id}:applicant:{uuid4()}"
    case.identity.save(update_fields=["evidence_reference", "updated_at"])
    rejected(case)


def test_wrong_core_family_rejected(case):
    other = Family.objects.create(school=case.school, family_name="Other Family")
    case.core.family = other
    case.core.save(update_fields=["family", "updated_at"])
    rejected(case)


def test_wrong_household_student_rejected(case):
    household = Household.objects.create(school_id=case.school.pk, name="Other Household")
    student = CompatibilityStudent.objects.create(
        school_id=case.school.pk, household=household,
        first_name="Alex", last_name="Student", grade_level="5",
    )
    case.applicant.student = student
    case.applicant.save(update_fields=["student", "updated_at"])
    rejected(case)


def test_cross_school_reuse_rejected(case):
    school = School.objects.create(name=f"Foreign School {uuid4().hex[:8]}")
    household = Household.objects.create(school_id=school.pk, name="Foreign Household")
    student = CompatibilityStudent.objects.create(
        school_id=school.pk, household=household,
        first_name="Alex", last_name="Student", grade_level="5",
    )
    case.applicant.student = student
    # Normal writes must reject a cross-school applicant relation.
    with pytest.raises(ValidationError, match="same school"):
        case.applicant.save(update_fields=["student", "updated_at"])
    # An older imported row could already have a corrupt FK: bypass model save
    # *only in this synthetic test* to verify the conversion bridge fails closed.
    Applicant.objects.filter(pk=case.applicant.pk).update(student=student)
    rejected(case)


def test_ambiguous_family_links_rejected(case):
    other = Family.objects.create(school=case.school, family_name="Second Family")
    HouseholdFamilyLink.objects.create(
        school=case.school, household_id=case.household.pk, family=other,
        source=HouseholdFamilyLink.SOURCE_MANUAL,
    )
    rejected(case)


def test_repeated_submissions_create_one_legacy_row(case):
    first, second = bridge(case), bridge(case)
    assert first["state"] == second["state"] == "accepted"
    assert first["application_ids"] == second["application_ids"]
    assert AdmissionsApplication.objects.filter(school=case.school).count() == 1
    assert CoreStudent.objects.filter(school=case.school).count() == 1


def test_second_applicant_failure_rolls_back_first_write(case):
    Applicant.objects.create(
        school_id=case.school.pk, application=case.application,
        first_name="Missing", last_name="DOB", dob=None,
    )
    rejected(case)
    assert not case.core.admissions_applications.exists()


def test_unrelated_historical_admissions_record_preserved(case):
    legacy = AdmissionsApplication.objects.create(
        school=case.school, academic_year=case.year, family=case.family,
        student=case.core, status=AdmissionsApplication.STATUS_ENROLLED,
        notes_internal=f"canonical_application_id={uuid4()}",
    )
    result = bridge(case)
    assert result["state"] == "identity_verification_required"
    legacy.refresh_from_db()
    assert legacy.status == AdmissionsApplication.STATUS_ENROLLED
    assert legacy.notes_internal != f"canonical_application_id={case.application.id}"
    assert AdmissionsApplication.objects.filter(school=case.school).count() == 1


def test_enrolled_historical_record_not_downgraded(case):
    legacy = AdmissionsApplication.objects.create(
        school=case.school, academic_year=case.year, family=case.family,
        student=case.core, status=AdmissionsApplication.STATUS_ENROLLED,
        notes_internal=f"canonical_application_id={case.application.id}",
    )
    assert bridge(case)["state"] == "identity_verification_required"
    legacy.refresh_from_db()
    assert legacy.status == AdmissionsApplication.STATUS_ENROLLED
