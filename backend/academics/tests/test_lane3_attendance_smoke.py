"""Lane 3 attendance endpoint smoke and read-after-write proof."""

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_lane3_attendance_write_endpoint_no_redirect():
    from academics.models import Section

    sec = Section.objects.first()
    if not sec:
        pytest.skip("No academics.models.Section in DB — run seed first")

    client = APIClient()
    path = f"/api/v1/academics/sections/{sec.id}/attendance/"
    resp = client.post(
        path,
        data={"items": [{"student_id": "00000000-0000-0000-0000-000000000001", "status": "present"}]},
        format="json",
    )
    assert resp.status_code != 302


@pytest.mark.django_db
def test_lane3_attendance_submit_and_read():
    import datetime
    from django.contrib.auth import get_user_model

    from academics.models import Enrollment
    from core.models import StudentIdentityLink, UserRole
    from crown_api.models import AttendanceRecord

    enrollment = None
    link = None
    for candidate in Enrollment.objects.select_related("section", "student").all():
        candidate_link = StudentIdentityLink.objects.filter(
            compatibility_student_id=candidate.student_id,
            school_id=candidate.school_id,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
            core_student__school_id=candidate.school_id,
            compatibility_student__school_id=candidate.school_id,
        ).exclude(evidence_reference="").first()
        if candidate_link:
            enrollment = candidate
            link = candidate_link
            break

    if enrollment is None:
        pytest.skip("No verified student identity enrolled in a section")

    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username="test_lane3_teacher",
        defaults={"is_staff": True, "school": link.school},
    )
    if user.school_id != link.school_id:
        user.school = link.school
        user.is_staff = True
        user.save(update_fields=["school", "is_staff"])
    UserRole.objects.get_or_create(
        school=link.school,
        user=user,
        role_code="REGISTRAR",
    )

    today = datetime.date.today().isoformat()
    AttendanceRecord.objects.filter(
        student_id=link.core_student_id,
        section_id=enrollment.section_id,
        date=today,
    ).delete()

    client = APIClient()
    client.force_authenticate(user=user)
    headers = {"HTTP_X_SCHOOL_ID": str(link.school_id)}

    resp = client.post(
        f"/api/v1/academics/sections/{enrollment.section_id}/attendance/",
        data={
            "date": today,
            "items": [{"student_id": str(link.core_student_id), "status": "present"}],
        },
        format="json",
        **headers,
    )
    assert resp.status_code == 200, f"submit failed: {resp.status_code} {resp.content}"
    assert resp.json().get("ok") is True

    row = AttendanceRecord.objects.get(
        student_id=link.core_student_id,
        section_id=enrollment.section_id,
        date=today,
    )
    assert row.section_id == enrollment.section_id

    read_resp = client.get(
        f"/api/v1/academics/students/{link.core_student_id}/attendance/",
        **headers,
    )
    assert read_resp.status_code in (200, 403), f"read endpoint error: {read_resp.status_code}"
    if read_resp.status_code == 200:
        rows = read_resp.json()
        rows = rows.get("results", rows) if isinstance(rows, dict) else rows
        matching = [
            r
            for r in rows
            if r.get("date") == today
            and str(r.get("section_id")) == str(enrollment.section_id)
        ]
        assert matching, f"section-scoped attendance not found in read list: {rows}"
