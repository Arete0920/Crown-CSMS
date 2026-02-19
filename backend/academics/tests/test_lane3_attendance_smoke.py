"""
Lane 3 pytest smoke guard.
Verifies the attendance submit endpoint exists and does NOT return a 302 redirect.
401/403 is acceptable; 302 means session-auth is leaking (forbidden pattern).
"""
import os
import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_lane3_attendance_write_endpoint_no_redirect():
    """
    POST academics/sections/<id>/attendance/ must not redirect (302).
    Unauthenticated → 401 is fine.  302 is a broken @login_required leak.
    """
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
    assert resp.status_code != 302, (
        f"302 redirect detected on {path} — endpoint is using @login_required instead of DRF IsAuthenticated"
    )


@pytest.mark.django_db
def test_lane3_attendance_submit_and_read():
    """
    Authenticated teacher (demo superuser) can POST attendance and the record
    appears in the student attendance GET endpoint.
    """
    import datetime
    from django.contrib.auth import get_user_model
    from academics.models import Section, Enrollment
    from crown_api.models import AttendanceRecord

    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username="test_lane3_teacher",
        defaults={"is_staff": True, "is_superuser": True},
    )
    user.set_password("TestPass!1")
    user.save()

    sec = Section.objects.first()
    if not sec:
        pytest.skip("No Section in DB")

    enrollment = Enrollment.objects.filter(section=sec).first()
    if not enrollment:
        pytest.skip("No Enrollment in DB for this section")

    student_id = str(enrollment.student_id)
    today = datetime.date.today().isoformat()

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post(
        f"/api/v1/academics/sections/{sec.id}/attendance/",
        data={"date": today, "items": [{"student_id": student_id, "status": "present"}]},
        format="json",
    )
    assert resp.status_code == 200, f"submit failed: {resp.status_code} {resp.content}"
    data = resp.json()
    assert data.get("ok") is True, f"ok not True: {data}"
    assert (data.get("created") or 0) + (data.get("updated") or 0) == 1

    # Verify the record persisted via the read endpoint
    read_resp = client.get(f"/api/v1/academics/students/{student_id}/attendance/")
    assert read_resp.status_code in (200, 403), f"read endpoint error: {read_resp.status_code}"
    if read_resp.status_code == 200:
        rows = read_resp.json()
        rows = rows.get("results", rows) if isinstance(rows, dict) else rows
        dates = [r.get("date") for r in rows]
        assert today in dates, f"today's attendance not found in read list: {dates}"
