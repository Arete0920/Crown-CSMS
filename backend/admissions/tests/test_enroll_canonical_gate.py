from __future__ import annotations

import uuid
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework.test import APIClient

from admissions.models import AdmissionsApplication
from applications.models import Application, ApplicationEvent, ApplicationStatus
from applications.views_admissions import CONTRACT_COUNTERSIGNED, DEPOSIT_PAID, ENROLLMENT_CONFIRMED_EVENT_TYPE, ENROLLMENT_STATE_EVENT_TYPE
from core.models import (
    AcademicYear, CrownPermission, Enrollment as CoreEnrollment, Family,
    GradeLevel, HouseholdFamilyLink, RolePermission, School,
    Student as CoreStudent, StudentIdentityLink, UserRole,
)
from households.models import Household, Student as CompatibilityStudent

pytestmark = pytest.mark.django_db
User = get_user_model()


def _school() -> School:
    return School.objects.create(name=f"Canonical Enrollment {uuid.uuid4().hex[:8]}", timezone="America/New_York", is_active=True)


def _year(school: School) -> AcademicYear:
    return AcademicYear.objects.create(school=school, name="2026-2027", start_date=date(2026, 8, 15), end_date=date(2027, 6, 15), is_current=True)


def _editor(school: School):
    user = User.objects.create_user(username=f"registrar-{uuid.uuid4().hex[:8]}@example.test", password="CanonicalEnrollmentTestOnly!")
    UserRole.objects.create(user=user, school=school, role_code="REGISTRAR")
    permission, _ = CrownPermission.objects.get_or_create(code="admissions.edit", defaults={"description": "admissions.edit"})
    RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=permission)
    return user


def _client(user, school: School) -> APIClient:
    client = APIClient(); client.force_authenticate(user=user); client.credentials(HTTP_X_SCHOOL_ID=str(school.id)); return client


def _legacy_application(school: School, year: AcademicYear, *, status="ACCEPTED") -> AdmissionsApplication:
    family = Family.objects.create(school=school, family_name=f"Family {uuid.uuid4().hex[:6]}")
    return AdmissionsApplication.objects.create(school=school, academic_year=year, family=family, status=status)


def _link_canonical(legacy: AdmissionsApplication, *, ready: bool) -> Application:
    household = Household.objects.create(school_id=legacy.school_id, name=f"Canonical Family {uuid.uuid4().hex[:6]}")
    canonical = Application.objects.create(school_id=legacy.school_id, household=household, status=ApplicationStatus.DECIDED)
    ApplicationEvent.objects.create(school_id=legacy.school_id, application=canonical, event_type="decision_made", payload={"decision": "accepted"})
    if ready:
        ApplicationEvent.objects.create(school_id=legacy.school_id, application=canonical, event_type=ENROLLMENT_STATE_EVENT_TYPE, payload={"contract_status": CONTRACT_COUNTERSIGNED, "deposit_status": DEPOSIT_PAID})
    legacy.notes_internal = f"canonical_application_id={canonical.id}"
    legacy.save(update_fields=["notes_internal", "updated_at"])
    return canonical


def test_enroll_rejects_missing_application_id():
    school = _school(); response = _client(_editor(school), school).post("/api/admissions/enroll/", {}, format="json")
    assert response.status_code == 400; assert response.data["detail"] == "application_id is required."


def test_enroll_rejects_wrong_legacy_stage():
    school = _school(); year = _year(school); legacy = _legacy_application(school, year, status=AdmissionsApplication.STATUS_UNDER_REVIEW)
    response = _client(_editor(school), school).post("/api/admissions/enroll/", {"application_id": legacy.id}, format="json")
    assert response.status_code == 409; assert response.data["current_status"] == AdmissionsApplication.STATUS_UNDER_REVIEW


def test_enroll_rejects_unlinked_accepted_legacy_application():
    school = _school(); year = _year(school); legacy = _legacy_application(school, year)
    response = _client(_editor(school), school).post("/api/admissions/enroll/", {"application_id": legacy.id}, format="json")
    assert response.status_code == 409; assert response.data["detail"] == "Enrollment requires a linked canonical admissions application."


def test_enroll_rejects_canonical_application_without_contract_deposit_readiness():
    school = _school()
    year = _year(school)
    legacy = _legacy_application(school, year)
    canonical = _link_canonical(legacy, ready=False)
    # This must reach the contract/deposit check, not fail earlier on identity.
    _verified_enrollment(legacy, canonical, year)
    response = _client(_editor(school), school).post(
        "/api/admissions/enroll/", {"application_id": legacy.id}, format="json",
    )
    assert response.status_code == 409
    assert response.data["canonical_application_id"] == str(canonical.id)
    assert response.data["detail"] == "Canonical enrollment readiness is incomplete."
    legacy.refresh_from_db()
    assert legacy.status == AdmissionsApplication.STATUS_ACCEPTED
    assert not ApplicationEvent.objects.filter(
        application=canonical, event_type=ENROLLMENT_CONFIRMED_EVENT_TYPE,
    ).exists()


def _verified_enrollment(legacy, canonical, year, *, add_enrollment=True):
    school, family, household = legacy.school, legacy.family, canonical.household
    HouseholdFamilyLink.objects.create(
        school=school, household_id=household.id, family=family,
        source=HouseholdFamilyLink.SOURCE_ADMISSIONS,
    )
    grade = GradeLevel.objects.create(
        school=school, code="5", label="Grade 5", sort_order=5,
    )
    compatibility = CompatibilityStudent.objects.create(
        school_id=school.id, household=household, first_name="Ada",
        last_name="Lovelace", grade_level="5", is_active=True,
    )
    applicant = canonical.applicants.create(
        school_id=school.id, student=compatibility, first_name="Ada",
        last_name="Lovelace", grade_applying_for="5", dob=date(2015, 3, 10),
    )
    core = CoreStudent.objects.create(
        school=school, family=family, student_number="S-1001",
        first_name="Ada", last_name="Lovelace", dob=applicant.dob,
        status="ACTIVE", current_grade_level=grade,
    )
    StudentIdentityLink.objects.create(
        school=school, core_student=core, compatibility_student=compatibility,
        source=StudentIdentityLink.SOURCE_ADMISSIONS,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
        evidence_reference=f"application:{canonical.id}:applicant:{applicant.id}",
    )
    legacy.student = core
    legacy.save(update_fields=["student", "updated_at"])
    if add_enrollment:
        CoreEnrollment.objects.create(
            school=school, student=core, academic_year=year,
            grade_level=grade, start_date=year.start_date, status="ENROLLED",
        )
    return applicant, core


def test_enroll_ready_canonical_application_persists_enrollment():
    school = _school()
    year = _year(school)
    legacy = _legacy_application(school, year)
    canonical = _link_canonical(legacy, ready=True)
    _, core = _verified_enrollment(legacy, canonical, year)
    client = _client(_editor(school), school)
    response = client.post(
        "/api/admissions/enroll/", {"application_id": legacy.id}, format="json",
    )
    assert response.status_code == 200, response.data
    assert response.data["ok"] is True
    assert response.data["already_enrolled"] is False
    assert response.data["canonical_application_id"] == str(canonical.id)
    assert response.data["canonical_gate"] == "verified_identity_and_core_enrollment"
    assert response.data["student_id"] == str(core.id)
    legacy.refresh_from_db()
    assert legacy.status == AdmissionsApplication.STATUS_ENROLLED
    assert CoreEnrollment.objects.filter(
        school=school, student=core, academic_year=year, status="ENROLLED",
    ).count() == 1
    assert ApplicationEvent.objects.filter(
        application=canonical, event_type=ENROLLMENT_CONFIRMED_EVENT_TYPE,
    ).count() == 1

    repeated = client.post(
        "/api/admissions/enroll/", {"application_id": legacy.id}, format="json",
    )
    assert repeated.status_code == 200, repeated.data
    assert repeated.data["already_enrolled"] is True
    assert CoreEnrollment.objects.filter(
        school=school, student=core, academic_year=year,
    ).count() == 1
    assert ApplicationEvent.objects.filter(
        application=canonical, event_type=ENROLLMENT_CONFIRMED_EVENT_TYPE,
    ).count() == 1


def test_enroll_rejects_unverified_identity_without_writing_events():
    school = _school()
    year = _year(school)
    legacy = _legacy_application(school, year)
    canonical = _link_canonical(legacy, ready=True)
    response = _client(_editor(school), school).post(
        "/api/admissions/enroll/", {"application_id": legacy.id}, format="json",
    )
    assert response.status_code == 409
    legacy.refresh_from_db()
    assert legacy.status == AdmissionsApplication.STATUS_ACCEPTED
    assert not CoreStudent.objects.filter(school=school).exists()
    assert not ApplicationEvent.objects.filter(
        application=canonical, event_type=ENROLLMENT_CONFIRMED_EVENT_TYPE,
    ).exists()


def test_enroll_rejects_missing_core_enrollment():
    school = _school()
    year = _year(school)
    legacy = _legacy_application(school, year)
    canonical = _link_canonical(legacy, ready=True)
    _, core = _verified_enrollment(
        legacy, canonical, year, add_enrollment=False,
    )
    response = _client(_editor(school), school).post(
        "/api/admissions/enroll/", {"application_id": legacy.id}, format="json",
    )
    assert response.status_code == 409
    assert response.data["code"] == "canonical_enrollment_required"
    legacy.refresh_from_db()
    assert legacy.status == AdmissionsApplication.STATUS_ACCEPTED
    assert CoreStudent.objects.filter(pk=core.id).exists()
    assert not CoreEnrollment.objects.filter(school=school).exists()
    assert not ApplicationEvent.objects.filter(
        application=canonical, event_type=ENROLLMENT_CONFIRMED_EVENT_TYPE,
    ).exists()


def test_enroll_rejects_same_name_wrong_legacy_student():
    school = _school()
    year = _year(school)
    legacy = _legacy_application(school, year)
    canonical = _link_canonical(legacy, ready=True)
    _, correct = _verified_enrollment(legacy, canonical, year)
    wrong = CoreStudent.objects.create(
        school=school, family=legacy.family, student_number="S-WRONG",
        first_name=correct.first_name, last_name=correct.last_name,
        dob=correct.dob, status="ACTIVE",
    )
    legacy.student = wrong
    legacy.save(update_fields=["student", "updated_at"])
    response = _client(_editor(school), school).post(
        "/api/admissions/enroll/", {"application_id": legacy.id}, format="json",
    )
    assert response.status_code == 409
    assert response.data["code"] == "canonical_enrollment_identity_mismatch"
    legacy.refresh_from_db()
    assert legacy.status == AdmissionsApplication.STATUS_ACCEPTED
    assert not ApplicationEvent.objects.filter(
        application=canonical, event_type=ENROLLMENT_CONFIRMED_EVENT_TYPE,
    ).exists()


def test_enroll_valid_upcoming_year_without_switching_school_current_year():
    school = _school()
    current_year = _year(school)
    upcoming_year = AcademicYear.objects.create(
        school=school, name="2027-2028", start_date=date(2027, 8, 15),
        end_date=date(2028, 6, 15), is_current=False,
    )
    legacy = _legacy_application(school, upcoming_year)
    canonical = _link_canonical(legacy, ready=True)
    _, core = _verified_enrollment(legacy, canonical, upcoming_year)
    response = _client(_editor(school), school).post(
        "/api/admissions/enroll/", {"application_id": legacy.id}, format="json",
    )
    assert response.status_code == 200, response.data
    legacy.refresh_from_db()
    assert legacy.status == AdmissionsApplication.STATUS_ENROLLED
    assert CoreEnrollment.objects.filter(
        school=school, student=core, academic_year=upcoming_year,
        status="ENROLLED",
    ).exists()
    assert not CoreEnrollment.objects.filter(
        school=school, student=core, academic_year=current_year,
    ).exists()
    assert AdmissionsApplication.objects.filter(
        school=school, student=core, academic_year=upcoming_year,
        status=AdmissionsApplication.STATUS_ENROLLED,
    ).count() == 1
    assert not AdmissionsApplication.objects.filter(
        school=school, student=core, academic_year=current_year,
    ).exists()
    assert response.data["legacy_conversion_bridge"]["state"] == "enrolled"


def test_enroll_rejects_prior_year_enrollment():
    school = _school()
    year = _year(school)
    legacy = _legacy_application(school, year)
    canonical = _link_canonical(legacy, ready=True)
    _, core = _verified_enrollment(
        legacy, canonical, year, add_enrollment=False,
    )
    prior = AcademicYear.objects.create(
        school=school, name="2025-2026", start_date=date(2025, 8, 15),
        end_date=date(2026, 6, 15), is_current=False,
    )
    CoreEnrollment.objects.create(
        school=school, student=core, academic_year=prior,
        grade_level=core.current_grade_level,
        start_date=prior.start_date, status="ENROLLED",
    )
    response = _client(_editor(school), school).post(
        "/api/admissions/enroll/", {"application_id": legacy.id}, format="json",
    )
    assert response.status_code == 409
    assert response.data["code"] == "canonical_enrollment_required"
    assert not ApplicationEvent.objects.filter(
        application=canonical, event_type=ENROLLMENT_CONFIRMED_EVENT_TYPE,
    ).exists()


def test_enroll_retry_denied_after_sis_enrollment_removed():
    school = _school()
    year = _year(school)
    legacy = _legacy_application(school, year)
    canonical = _link_canonical(legacy, ready=True)
    _, core = _verified_enrollment(legacy, canonical, year)
    client = _client(_editor(school), school)
    first = client.post(
        "/api/admissions/enroll/", {"application_id": legacy.id}, format="json",
    )
    assert first.status_code == 200, first.data
    CoreEnrollment.objects.filter(
        school=school, student=core, academic_year=year,
    ).delete()
    retry = client.post(
        "/api/admissions/enroll/", {"application_id": legacy.id}, format="json",
    )
    assert retry.status_code == 409
    assert retry.data["code"] == "canonical_enrollment_required"


def test_enroll_denies_user_without_admissions_edit_permission():
    school = _school(); year = _year(school); legacy = _legacy_application(school, year)
    user = User.objects.create_user(username=f"parent-{uuid.uuid4().hex[:8]}@example.test", password="CanonicalEnrollmentTestOnly!"); UserRole.objects.create(user=user, school=school, role_code="PARENT")
    response = _client(user, school).post("/api/admissions/enroll/", {"application_id": legacy.id}, format="json")
    assert response.status_code == 403; assert response.data["detail"] == "Permission denied."



@pytest.mark.django_db(transaction=True)
def test_postgresql_nullable_student_join_preserves_identity_lock_and_denial():
    """PostgreSQL forbids FOR UPDATE on a nullable select_related join."""
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locking")
    school = _school()
    year = _year(school)
    legacy = _legacy_application(school, year)
    canonical = _link_canonical(legacy, ready=True)
    HouseholdFamilyLink.objects.create(
        school=school,
        household_id=canonical.household_id,
        family=legacy.family,
        source=HouseholdFamilyLink.SOURCE_ADMISSIONS,
    )
    canonical.applicants.create(
        school_id=school.id,
        first_name="Absent",
        last_name="Student",
        grade_applying_for="5",
        dob=date(2015, 3, 10),
    )
    response = _client(_editor(school), school).post(
        "/api/admissions/enroll/",
        {"application_id": legacy.id},
        format="json",
    )
    assert response.status_code == 409, response.data
    assert response.data["code"] == "student_identity_link_required"
    legacy.refresh_from_db()
    assert legacy.status == AdmissionsApplication.STATUS_ACCEPTED
    assert not ApplicationEvent.objects.filter(
        application=canonical, event_type=ENROLLMENT_CONFIRMED_EVENT_TYPE,
    ).exists()
