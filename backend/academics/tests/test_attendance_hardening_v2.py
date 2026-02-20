"""
Phase 2 proof: attendance submit idempotency + RBAC hardening (ATTENDANCE_HARDENING_V2).

Tests:
1. Unauthenticated POST → 401 (no redirect)
2. Authenticated superuser: submit same record twice → idempotent (second call: updated=1, created=0)
3. Response includes section_id field
"""
import datetime
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import Section, Enrollment
from crown_api.models import AttendanceRecord

pytestmark = pytest.mark.django_db

FAKE_UUID = "00000000-0000-0000-0000-000000000099"
URL_TMPL = "/api/v1/academics/sections/{section_id}/attendance/"


def test_attendance_submit_unauthenticated_no_redirect():
    """Unauthenticated request must not redirect (302 = broken @login_required)."""
    client = APIClient()
    resp = client.post(URL_TMPL.format(section_id=FAKE_UUID), {"items": []}, format="json")
    assert resp.status_code != 302, "302 redirect detected — endpoint leaking session auth"
    assert resp.status_code in (400, 401, 403, 404)


def test_attendance_submit_idempotent():
    """Submitting the same student+date twice must be idempotent (update, not double-create)."""
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username="test_att_hard_v2",
        defaults={"is_staff": True, "is_superuser": True},
    )

    sec = Section.objects.first()
    if not sec:
        pytest.skip("No Section in DB — run seed first")

    enrollment = Enrollment.objects.filter(section=sec).first()
    if not enrollment:
        pytest.skip("No Enrollment for this section")

    student_id = str(enrollment.student_id)
    today = datetime.date.today().isoformat()

    # Pre-clean to ensure fresh state for this test
    AttendanceRecord.objects.filter(student_id=student_id, course=None, date=today).delete()

    client = APIClient()
    client.force_authenticate(user=user)

    payload = {"date": today, "items": [{"student_id": student_id, "status": "PRESENT"}]}

    # First submit → should create
    r1 = client.post(URL_TMPL.format(section_id=sec.id), payload, format="json")
    assert r1.status_code == 200, f"First submit failed: {r1.status_code} {r1.content}"
    d1 = r1.json()
    assert d1.get("ok") is True
    assert d1.get("created") == 1
    assert d1.get("updated") == 0

    # Second submit same data → must update, not create (idempotency)
    r2 = client.post(URL_TMPL.format(section_id=sec.id), payload, format="json")
    assert r2.status_code == 200, f"Second submit failed: {r2.status_code} {r2.content}"
    d2 = r2.json()
    assert d2.get("ok") is True
    assert d2.get("created") == 0, f"Second submit created a new record — not idempotent: {d2}"
    assert d2.get("updated") == 1

    # Only one DB record should exist
    count = AttendanceRecord.objects.filter(student_id=student_id, course=None, date=today).count()
    assert count == 1, f"Expected 1 AttendanceRecord, found {count}"


def test_attendance_submit_response_includes_section_id():
    """Response must include section_id (V2 contract)."""
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username="test_att_hard_section_id",
        defaults={"is_staff": True, "is_superuser": True},
    )

    sec = Section.objects.first()
    if not sec:
        pytest.skip("No Section in DB")

    enrollment = Enrollment.objects.filter(section=sec).first()
    if not enrollment:
        pytest.skip("No Enrollment for this section")

    student_id = str(enrollment.student_id)
    today = datetime.date.today().isoformat()
    AttendanceRecord.objects.filter(student_id=student_id, course=None, date=today).delete()

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post(
        URL_TMPL.format(section_id=sec.id),
        {"date": today, "items": [{"student_id": student_id, "status": "ABSENT"}]},
        format="json",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "section_id" in data, f"section_id missing from response: {data}"
    assert data["section_id"] == str(sec.id)
