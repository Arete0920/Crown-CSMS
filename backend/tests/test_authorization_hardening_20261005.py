from datetime import date
import uuid

import pytest
from rest_framework.test import APIClient

from core.models import (
    CrownPermission,
    Family,
    RolePermission,
    School,
    Student,
    StudentIdentityLink,
    UserAccount,
    UserRole,
)
from households.models import Household, Student as CompatibilityStudent
from servicehours.models import ServiceEntry

pytestmark = pytest.mark.django_db


def _user(*, school, prefix):
    return UserAccount.objects.create_user(
        username=f"{prefix}-{uuid.uuid4().hex[:8]}",
        email=f"{prefix}-{uuid.uuid4().hex[:8]}@example.org",
        password="test-only-password",
        school=school,
    )


def _grant(*, user, school, role_code, permissions):
    UserRole.objects.create(user=user, school=school, role_code=role_code)
    for code in permissions:
        perm, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code=role_code, permission=perm)


def _student_identity(*, school, account, number):
    family = Family.objects.create(school=school, family_name=f"Family {number}")
    core_student = Student.objects.create(
        school=school,
        family=family,
        student_number=number,
        first_name="Student",
        last_name=number,
        dob=date(2012, 1, 1),
        status="ACTIVE",
    )
    household = Household.objects.create(school_id=school.id, name=f"Household {number}")
    compatibility = CompatibilityStudent.objects.create(
        school_id=school.id,
        household=household,
        account=account,
        first_name="Student",
        last_name=number,
        grade_level="8",
    )
    StudentIdentityLink.objects.create(
        school=school,
        core_student=core_student,
        compatibility_student=compatibility,
        source=StudentIdentityLink.SOURCE_RECONCILIATION,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
        evidence_reference=f"test:{number}",
    )
    return core_student


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_executive360_requires_admin_view():
    school = School.objects.create(name="Executive Permission School")
    user = _user(school=school, prefix="executive")
    _grant(user=user, school=school, role_code="exec_no_permission", permissions=[])

    response = _client(user).get(
        "/api/executive360/me/overview/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 403

    perm, _ = CrownPermission.objects.get_or_create(code="admin.view")
    RolePermission.objects.get_or_create(role_code="exec_no_permission", permission=perm)
    response = _client(user).get(
        "/api/executive360/me/overview/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 200


def test_executive360_admin_grant_is_tenant_scoped():
    school_a = School.objects.create(name="Executive School A")
    school_b = School.objects.create(name="Executive School B")
    user = _user(school=school_a, prefix="executive-tenant")
    _grant(user=user, school=school_a, role_code="exec_tenant_admin", permissions=["admin.view"])

    response = _client(user).get(
        "/api/executive360/me/overview/",
        HTTP_X_SCHOOL_ID=str(school_b.id),
    )
    assert response.status_code in {400, 403, 404}


def test_service_self_scope_returns_only_authenticated_student_records():
    school = School.objects.create(name="Service Self School")
    student_user = _user(school=school, prefix="service-student")
    other_user = _user(school=school, prefix="service-other")
    _grant(user=student_user, school=school, role_code="service_student", permissions=["service.self"])
    _grant(user=other_user, school=school, role_code="service_other_student", permissions=["service.self"])
    own_student = _student_identity(school=school, account=student_user, number="SELF-1")
    other_student = _student_identity(school=school, account=other_user, number="SELF-2")
    ServiceEntry.objects.create(school=school, student=own_student, date=date.today(), hours="2.00")
    ServiceEntry.objects.create(school=school, student=other_student, date=date.today(), hours="3.00")

    response = _client(student_user).get(
        "/api/service/entries/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["student"] == str(own_student.id)

    forbidden = _client(student_user).get(
        f"/api/service/students/{other_student.id}/summary/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert forbidden.status_code == 403


def test_service_self_scope_cannot_submit_for_another_student():
    school = School.objects.create(name="Service Submit School")
    student_user = _user(school=school, prefix="service-submit")
    other_user = _user(school=school, prefix="service-submit-other")
    _grant(user=student_user, school=school, role_code="service_submit_student", permissions=["service.self"])
    own_student = _student_identity(school=school, account=student_user, number="SUBMIT-1")
    other_student = _student_identity(school=school, account=other_user, number="SUBMIT-2")

    response = _client(student_user).post(
        "/api/service/entries/",
        {
            "student": str(other_student.id),
            "date": date.today().isoformat(),
            "hours": "1.50",
            "category": "Community Service",
        },
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert response.status_code == 403
    assert not ServiceEntry.objects.filter(student=other_student).exists()

    allowed = _client(student_user).post(
        "/api/service/entries/",
        {
            "student": str(own_student.id),
            "date": date.today().isoformat(),
            "hours": "1.50",
            "category": "Community Service",
        },
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert allowed.status_code == 201


def test_service_approval_requires_explicit_approval_permission():
    school = School.objects.create(name="Service Approval School")
    student_user = _user(school=school, prefix="service-approval-student")
    coordinator = _user(school=school, prefix="service-coordinator")
    _grant(user=student_user, school=school, role_code="service_approval_student", permissions=["service.self"])
    _grant(
        user=coordinator,
        school=school,
        role_code="service_learning_coordinator",
        permissions=["service.manage", "service.approve"],
    )
    student = _student_identity(school=school, account=student_user, number="APPROVE-1")
    entry = ServiceEntry.objects.create(
        school=school,
        student=student,
        date=date.today(),
        hours="2.00",
        status="pending",
    )

    denied = _client(student_user).post(
        f"/api/service/approvals/{entry.id}/",
        {"status": "approved"},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert denied.status_code == 403

    approved = _client(coordinator).post(
        f"/api/service/approvals/{entry.id}/",
        {"status": "approved"},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert approved.status_code == 200
    entry.refresh_from_db()
    assert entry.status == "approved"
    assert entry.approved_by_id == coordinator.id


def test_integration_preview_requires_integrations_run():
    school = School.objects.create(name="Integration Permission School")
    user = _user(school=school, prefix="integration-user")
    _grant(user=user, school=school, role_code="integration_no_permission", permissions=[])

    denied = _client(user).post(
        "/api/integrations/teams/preview/",
        {"event_type": "test", "title": "Test", "text": "No outbound call"},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert denied.status_code == 403

    perm, _ = CrownPermission.objects.get_or_create(code="integrations.run")
    RolePermission.objects.get_or_create(role_code="integration_no_permission", permission=perm)
    allowed = _client(user).post(
        "/api/integrations/teams/preview/",
        {"event_type": "test", "title": "Test", "text": "No outbound call"},
        format="json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert allowed.status_code == 200
    assert allowed.json()["payload"]["demo_mode"] is True
