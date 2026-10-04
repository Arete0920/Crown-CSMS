import uuid

import pytest
from django.test import Client
from django.utils import timezone

from core.models import (
    AcademicYear,
    CrownPermission,
    Enrollment,
    Family,
    GradeLevel,
    Guardian,
    RolePermission,
    School,
    Student,
    StudentIdentityLink,
    UserAccount,
    UserRole,
)
from households.models import Household, Student as CompatibilityStudent


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _enable_tenant_middleware(settings):
    settings.TENANT_HEADER_REQUIRED = True


def _school(label):
    return School.objects.create(name=f"{label}-{uuid.uuid4()}")


def _grant_integrity(user, school):
    UserRole.objects.create(user=user, school=school, role_code="HEAD_OF_SCHOOL")
    permission, _ = CrownPermission.objects.get_or_create(
        code="integrity.view",
        defaults={"description": "View integrity dashboard"},
    )
    RolePermission.objects.get_or_create(
        role_code="HEAD_OF_SCHOOL",
        permission=permission,
    )


def _client_for(user):
    client = Client()
    client.force_login(user)
    return client


def _baseline_school(label="Quality"):
    school = _school(label)
    academic_year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date=timezone.datetime(2026, 8, 1).date(),
        end_date=timezone.datetime(2027, 6, 30).date(),
        is_current=True,
    )
    grade = GradeLevel.objects.create(
        school=school,
        code="5",
        label="Grade 5",
        sort_order=5,
    )
    family = Family.objects.create(
        school=school,
        family_name=f"{label} Family",
        status="ACTIVE",
    )
    guardian = Guardian.objects.create(
        school=school,
        family=family,
        first_name="Parent",
        last_name=label,
        email=f"{label.lower()}@example.test",
        relationship="GUARDIAN",
        portal_access=True,
    )
    user = UserAccount.objects.create_user(
        username=f"{label.lower()}-head",
        email=f"head-{label.lower()}@example.test",
        password="Passw0rd!",
        school=school,
    )
    _grant_integrity(user, school)
    UserAccount.objects.create_user(
        username=f"{label.lower()}-guardian",
        email=guardian.email,
        password="Passw0rd!",
        school=school,
        guardian=guardian,
    )
    student = Student.objects.create(
        school=school,
        family=family,
        student_number=f"{label[:2].upper()}-001",
        first_name="Student",
        last_name=label,
        dob=timezone.datetime(2015, 1, 1).date(),
        status="ACTIVE",
        current_grade_level=grade,
    )
    Enrollment.objects.create(
        school=school,
        student=student,
        academic_year=academic_year,
        grade_level=grade,
        start_date=academic_year.start_date,
        status="ENROLLED",
    )
    household = Household.objects.create(
        school_id=school.id,
        name=f"{label} Compatibility Household",
    )
    compatibility_student = CompatibilityStudent.objects.create(
        school_id=school.id,
        household=household,
        first_name=student.first_name,
        last_name=student.last_name,
        grade_level=grade.code,
        is_active=True,
    )
    StudentIdentityLink.objects.create(
        school=school,
        core_student=student,
        compatibility_student=compatibility_student,
        source=StudentIdentityLink.SOURCE_MANUAL,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
        evidence_reference="test-fixture",
    )
    return school, user, family, guardian, student


class TestSchoolDataQualityApi:
    def test_requires_authenticated_integrity_permission(self):
        school = _school("No Permission")
        user = UserAccount.objects.create_user(
            username="no-permission",
            password="Passw0rd!",
            school=school,
        )
        response = _client_for(user).get(
            "/api/v1/integrity/data-quality/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert response.status_code == 403

    def test_healthy_baseline_returns_no_findings(self):
        school, user, *_ = _baseline_school("Healthy")
        response = _client_for(user).get(
            "/api/v1/integrity/data-quality/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["mode"] == "read_only"
        assert payload["automatic_remediation"] is False
        assert payload["school_id"] == str(school.id)
        assert payload["status"] == "healthy"
        assert payload["summary"]["findings_count"] == 0
        assert all(check["status"] == "pass" for check in payload["checks"])

    def test_reports_school_scoped_data_quality_findings(self):
        school, user, family, guardian, student = _baseline_school("Finding")
        student.current_grade_level = None
        student.save(update_fields=["current_grade_level"])

        Enrollment.objects.filter(student=student).delete()
        StudentIdentityLink.objects.filter(core_student=student).delete()
        UserAccount.objects.filter(guardian=guardian).delete()

        response = _client_for(user).get(
            "/api/v1/integrity/data-quality/",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        assert response.status_code == 200
        checks = {row["id"]: row for row in response.json()["checks"]}
        assert checks["active_student_grade_assignment"]["count"] == 1
        assert checks["active_student_current_enrollment"]["count"] == 1
        assert checks["canonical_student_identity_bridge"]["count"] == 1
        assert checks["portal_guardian_account_readiness"]["count"] == 1
        assert response.json()["status"] in {"action_required", "needs_review"}

    def test_other_school_data_does_not_leak_into_counts(self):
        school_a, user_a, *_ = _baseline_school("TenantA")
        school_b, _, family_b, _, student_b = _baseline_school("TenantB")
        student_b.current_grade_level = None
        student_b.save(update_fields=["current_grade_level"])
        Enrollment.objects.filter(student=student_b).delete()
        Family.objects.filter(pk=family_b.pk).update(status="ACTIVE")

        response = _client_for(user_a).get(
            "/api/v1/integrity/data-quality/",
            HTTP_X_SCHOOL_ID=str(school_a.id),
        )
        assert response.status_code == 200
        checks = {row["id"]: row for row in response.json()["checks"]}
        assert checks["active_student_grade_assignment"]["count"] == 0
        assert checks["active_student_current_enrollment"]["count"] == 0

    def test_cross_tenant_header_is_denied_before_data_is_returned(self):
        school_a, user_a, *_ = _baseline_school("ScopeA")
        school_b, *_ = _baseline_school("ScopeB")

        response = _client_for(user_a).get(
            "/api/v1/integrity/data-quality/",
            HTTP_X_SCHOOL_ID=str(school_b.id),
        )
        assert response.status_code in {403, 404}
        assert str(school_b.id) not in response.content.decode("utf-8")
