"""Attendance submit idempotency and canonical section persistence proof."""

import datetime

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Enrollment, Section
from core.models import StudentIdentityLink, UserRole
from crown_api.models import AttendanceRecord


pytestmark = pytest.mark.django_db

FAKE_UUID = "00000000-0000-0000-0000-000000000099"
URL_TMPL = "/api/v1/academics/sections/{section_id}/attendance/"


def _verified_enrollment():
    for enrollment in Enrollment.objects.select_related("section", "student").all():
        link = StudentIdentityLink.objects.filter(
            compatibility_student_id=enrollment.student_id,
            school_id=enrollment.school_id,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
            core_student__school_id=enrollment.school_id,
            compatibility_student__school_id=enrollment.school_id,
        ).exclude(evidence_reference="").first()
        if link:
            return enrollment, link
    return None, None


def _authorized_client(school):
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username="test_att_hard_v2",
        defaults={"is_staff": True, "school": school},
    )
    if user.school_id != school.id:
        user.school = school
        user.is_staff = True
        user.save(update_fields=["school", "is_staff"])
    UserRole.objects.get_or_create(
        school=school,
        user=user,
        role_code="REGISTRAR",
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_attendance_submit_unauthenticated_no_redirect():
    client = APIClient()
    resp = client.post(URL_TMPL.format(section_id=FAKE_UUID), {"items": []}, format="json")
    assert resp.status_code != 302
    assert resp.status_code in (400, 401, 403, 404)


def test_attendance_submit_idempotent_and_section_scoped():
    enrollment, link = _verified_enrollment()
    if not enrollment:
        pytest.skip("No verified student identity enrolled in a section")

    section = enrollment.section
    today = datetime.date.today().isoformat()
    AttendanceRecord.objects.filter(
        student_id=link.core_student_id,
        section_id=section.id,
        date=today,
    ).delete()

    client = _authorized_client(link.school)
    payload = {
        "date": today,
        "items": [{"student_id": str(link.core_student_id), "status": "PRESENT"}],
    }

    first = client.post(
        URL_TMPL.format(section_id=section.id),
        payload,
        format="json",
        HTTP_X_SCHOOL_ID=str(link.school_id),
    )
    assert first.status_code == 200, first.content
    assert first.json()["created"] == 1
    assert first.json()["updated"] == 0

    second = client.post(
        URL_TMPL.format(section_id=section.id),
        payload,
        format="json",
        HTTP_X_SCHOOL_ID=str(link.school_id),
    )
    assert second.status_code == 200, second.content
    assert second.json()["created"] == 0
    assert second.json()["updated"] == 1

    rows = AttendanceRecord.objects.filter(
        student_id=link.core_student_id,
        section_id=section.id,
        date=today,
    )
    assert rows.count() == 1
    assert rows.get().course_id is None


def test_attendance_submit_response_and_persistence_include_section_id():
    enrollment, link = _verified_enrollment()
    if not enrollment:
        pytest.skip("No verified student identity enrolled in a section")

    section = enrollment.section
    today = datetime.date.today().isoformat()
    AttendanceRecord.objects.filter(
        student_id=link.core_student_id,
        section_id=section.id,
        date=today,
    ).delete()

    client = _authorized_client(link.school)
    resp = client.post(
        URL_TMPL.format(section_id=section.id),
        {"date": today, "items": [{"student_id": str(link.core_student_id), "status": "ABSENT"}]},
        format="json",
        HTTP_X_SCHOOL_ID=str(link.school_id),
    )
    assert resp.status_code == 200, resp.content
    assert resp.json()["section_id"] == str(section.id)

    row = AttendanceRecord.objects.get(
        student_id=link.core_student_id,
        section_id=section.id,
        date=today,
    )
    assert row.section_id == section.id
