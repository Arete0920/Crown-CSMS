from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section
from core.models import Family, School, Student as CoreStudent, StudentIdentityLink, UserRole
from crown_api.models import AttendanceRecord
from households.models import Household, Student as CompatibilityStudent


pytestmark = pytest.mark.django_db


def _make_student_identity(school, suffix, *, verified=True):
    family = Family.objects.create(school=school, family_name=f"Family {suffix}")
    core_student = CoreStudent.objects.create(
        school=school,
        family=family,
        student_number=f"S-{suffix}",
        first_name=f"Student{suffix}",
        last_name="Test",
        dob=date(2012, 1, 1),
        status="ACTIVE",
    )
    household = Household.objects.create(
        school_id=school.id,
        name=f"Household {suffix}",
    )
    compatibility_student = CompatibilityStudent.objects.create(
        school_id=school.id,
        household=household,
        first_name=f"Student{suffix}",
        last_name="Test",
        is_active=True,
    )
    link = StudentIdentityLink.objects.create(
        school=school,
        core_student=core_student,
        compatibility_student=compatibility_student,
        source=StudentIdentityLink.SOURCE_MANUAL,
        verification_status=(
            StudentIdentityLink.STATUS_VERIFIED if verified else "pending"
        ),
        evidence_reference=(f"test:attendance:{suffix}" if verified else ""),
    )
    return core_student, compatibility_student, link


@pytest.fixture
def attendance_context():
    school = School.objects.create(name="Attendance Test School")
    course = Course.objects.create(
        school_id=school.id,
        code="ATT-101",
        name="Attendance Course",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term="2026-FALL",
    )
    core_student, compatibility_student, link = _make_student_identity(
        school, "100"
    )
    Enrollment.objects.create(
        school_id=school.id,
        section=section,
        student=compatibility_student,
    )

    User = get_user_model()
    registrar = User.objects.create_user(
        username="attendance_registrar",
        email="attendance_registrar@test.invalid",
        password="TestPass!1",
        school=school,
        is_staff=True,
    )
    UserRole.objects.create(
        school=school,
        user=registrar,
        role_code="REGISTRAR",
    )

    client = APIClient()
    client.force_authenticate(user=registrar)
    return {
        "school": school,
        "section": section,
        "core_student": core_student,
        "compatibility_student": compatibility_student,
        "link": link,
        "registrar": registrar,
        "client": client,
    }


def _post(ctx, student_id, status="PRESENT"):
    return ctx["client"].post(
        f"/api/v1/academics/sections/{ctx['section'].id}/attendance/",
        {
            "date": "2026-08-14",
            "items": [{"student_id": str(student_id), "status": status}],
        },
        format="json",
        HTTP_X_SCHOOL_ID=str(ctx["school"].id),
    )


def test_submit_persists_canonical_section_and_is_idempotent(attendance_context):
    ctx = attendance_context

    first = _post(ctx, ctx["core_student"].id, "ABSENT")
    assert first.status_code == 200
    assert first.json()["created"] == 1
    assert first.json()["updated"] == 0

    second = _post(ctx, ctx["core_student"].id, "TARDY")
    assert second.status_code == 200
    assert second.json()["created"] == 0
    assert second.json()["updated"] == 1

    rows = AttendanceRecord.objects.filter(
        student=ctx["core_student"],
        section=ctx["section"],
        date=date(2026, 8, 14),
    )
    assert rows.count() == 1
    row = rows.get()
    assert row.status == "TARDY"
    assert row.section_id == ctx["section"].id
    assert row.course_id is None


def test_compatibility_student_id_resolves_through_verified_bridge(attendance_context):
    ctx = attendance_context
    response = _post(ctx, ctx["compatibility_student"].id)
    assert response.status_code == 200
    assert AttendanceRecord.objects.filter(
        student=ctx["core_student"],
        section=ctx["section"],
        date=date(2026, 8, 14),
    ).count() == 1


def test_invalid_status_is_rejected_without_write(attendance_context):
    ctx = attendance_context
    response = _post(ctx, ctx["core_student"].id, "NOT_A_STATUS")
    assert response.status_code == 400
    assert AttendanceRecord.objects.count() == 0


def test_verified_identity_without_section_membership_fails_closed(attendance_context):
    ctx = attendance_context
    other_core, _other_compat, _link = _make_student_identity(ctx["school"], "200")
    response = _post(ctx, other_core.id)
    assert response.status_code == 404
    assert AttendanceRecord.objects.count() == 0


def test_pending_identity_link_fails_closed(attendance_context):
    ctx = attendance_context
    pending_core, pending_compat, _link = _make_student_identity(
        ctx["school"], "300", verified=False
    )
    Enrollment.objects.create(
        school_id=ctx["school"].id,
        section=ctx["section"],
        student=pending_compat,
    )
    response = _post(ctx, pending_core.id)
    assert response.status_code == 404
    assert AttendanceRecord.objects.count() == 0


def test_teacher_requires_explicit_section_assignment(attendance_context):
    ctx = attendance_context
    User = get_user_model()
    teacher = User.objects.create_user(
        username="attendance_teacher",
        email="attendance_teacher@test.invalid",
        password="TestPass!1",
        school=ctx["school"],
        is_staff=True,
    )
    UserRole.objects.create(
        school=ctx["school"],
        user=teacher,
        role_code="TEACHER",
    )
    client = APIClient()
    client.force_authenticate(user=teacher)
    response = client.post(
        f"/api/v1/academics/sections/{ctx['section'].id}/attendance/",
        {
            "date": "2026-08-14",
            "items": [
                {
                    "student_id": str(ctx["core_student"].id),
                    "status": "PRESENT",
                }
            ],
        },
        format="json",
        HTTP_X_SCHOOL_ID=str(ctx["school"].id),
    )
    assert response.status_code == 403
    assert AttendanceRecord.objects.count() == 0


def test_read_serializer_exposes_canonical_section_id(attendance_context):
    ctx = attendance_context
    response = _post(ctx, ctx["core_student"].id)
    assert response.status_code == 200

    row = AttendanceRecord.objects.get(
        student=ctx["core_student"],
        section=ctx["section"],
        date=date(2026, 8, 14),
    )
    from crown_api.serializers_academics import AttendanceRecordReadSerializer

    payload = AttendanceRecordReadSerializer(row).data
    assert str(payload["section_id"]) == str(ctx["section"].id)
