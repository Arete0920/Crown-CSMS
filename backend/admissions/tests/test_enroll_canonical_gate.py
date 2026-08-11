from __future__ import annotations

import uuid
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from admissions.models import AdmissionsApplication
from applications.models import Application, ApplicationEvent, ApplicationStatus
from applications.views_admissions import CONTRACT_COUNTERSIGNED, DEPOSIT_PAID, ENROLLMENT_CONFIRMED_EVENT_TYPE, ENROLLMENT_STATE_EVENT_TYPE
from core.models import AcademicYear, CrownPermission, Family, RolePermission, School, UserRole
from households.models import Household

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
    school = _school(); year = _year(school); legacy = _legacy_application(school, year); canonical = _link_canonical(legacy, ready=False)
    response = _client(_editor(school), school).post("/api/admissions/enroll/", {"application_id": legacy.id}, format="json")
    assert response.status_code == 409; assert response.data["canonical_application_id"] == str(canonical.id)
    legacy.refresh_from_db(); assert legacy.status == AdmissionsApplication.STATUS_ACCEPTED


def test_enroll_ready_canonical_application_persists_enrollment():
    school = _school(); year = _year(school); legacy = _legacy_application(school, year); canonical = _link_canonical(legacy, ready=True)
    response = _client(_editor(school), school).post("/api/admissions/enroll/", {"application_id": legacy.id}, format="json")
    assert response.status_code == 200, response.data; assert response.data["ok"] is True; assert response.data["already_enrolled"] is False
    assert response.data["canonical_application_id"] == str(canonical.id); assert response.data["canonical_gate"] == "contract_countersigned_and_deposit_paid_or_waived"
    legacy.refresh_from_db(); assert legacy.status == AdmissionsApplication.STATUS_ENROLLED
    assert ApplicationEvent.objects.filter(school_id=school.id, application=canonical, event_type=ENROLLMENT_CONFIRMED_EVENT_TYPE).exists()


def test_enroll_denies_user_without_admissions_edit_permission():
    school = _school(); year = _year(school); legacy = _legacy_application(school, year)
    user = User.objects.create_user(username=f"parent-{uuid.uuid4().hex[:8]}@example.test", password="CanonicalEnrollmentTestOnly!"); UserRole.objects.create(user=user, school=school, role_code="PARENT")
    response = _client(user, school).post("/api/admissions/enroll/", {"application_id": legacy.id}, format="json")
    assert response.status_code == 403; assert response.data["detail"] == "Permission denied."
