"""Synthetic API contract: tenant, staff RBAC and custody service are not client-controlled."""
from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from core.models import School, UserAccount, UserRole
from aftercare.models import DaycareAttendance, DaycareRelease
from audit.models import AuditLog
from aftercare.tests.test_daycare_checkin import setup

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _checkin(d, client=None, **override):
    payload = dict(
        site_id=str(d["site"].id), room_id=str(d["room"].id),
        child_id=str(d["child"].id), program_code="DAYCARE", request_key=str(uuid4())
    )
    payload.update(override)
    return (client or _client(d["actor"])).post(
        "/api/v1/aftercare/daycare/attendance/checkin/", payload, format="json"
    )


def _release(d, attendance, client=None, **override):
    payload = dict(
        site_id=str(d["site"].id), room_id=str(d["room"].id),
        attendance_id=str(getattr(attendance, "id", attendance)), guardian_authority_id=str(d["authority"].id),
        request_key=str(uuid4()), identity_verified=True,
        identity_method="GOVERNMENT_PHOTO_ID",
    )
    payload.update(override)
    return (client or _client(d["actor"])).post(
        "/api/v1/aftercare/daycare/attendance/release/", payload, format="json"
    )


def test_authenticated_staff_checkin_roster_and_release():
    d = setup()
    c = _client(d["actor"])
    checkin = _checkin(d, c)
    assert checkin.status_code == 201, checkin.data
    attendance = DaycareAttendance.objects.get(pk=checkin.data["attendance_id"])
    roster = c.get(f'/api/v1/aftercare/daycare/sites/{d["site"].id}/roster/')
    assert roster.status_code == 200, getattr(roster, "data", None)
    assert roster.data["children_present"] == 1
    assert roster.data["rows"][0]["child_id"] == str(d["child"].id)
    released = _release(d, attendance, c)
    assert released.status_code == 201, released.data
    assert DaycareRelease.objects.filter(attendance=attendance).count() == 1
    after = c.get(f'/api/v1/aftercare/daycare/sites/{d["site"].id}/roster/')
    assert after.status_code == 200
    assert after.data["children_present"] == 0
    assert AuditLog.objects.filter(action="diadem.daycare.release").count() == 1


def test_unauthenticated_cannot_read_or_mutate():
    d = setup()
    c = APIClient()
    for response in (
        _checkin(d, c),
        c.get(f'/api/v1/aftercare/daycare/sites/{d["site"].id}/roster/'),
        _release(d, uuid4(), c),
    ):
        assert response.status_code in (401, 403)
    assert not DaycareAttendance.objects.exists()


def test_actor_impersonation_and_extra_fields_rejected():
    d = setup()
    response = _checkin(d, actor_id=str(d["director"].id))
    assert response.status_code == 400
    assert not DaycareAttendance.objects.exists()
    response = _checkin(d)
    assert response.status_code == 201
    attendance = DaycareAttendance.objects.get(pk=response.data["attendance_id"])
    response = _release(d, attendance, actor_id=str(d["director"].id))
    assert response.status_code == 400
    assert not DaycareRelease.objects.exists()


def test_foreign_school_header_never_overrides_staff_tenant():
    d = setup()
    foreign = School.objects.create(name="Other Center")
    c = _client(d["actor"])
    r = c.post(
        "/api/v1/aftercare/daycare/attendance/checkin/",
        dict(site_id=str(d["site"].id), room_id=str(d["room"].id),
             child_id=str(d["child"].id), program_code="DAYCARE",
             request_key=str(uuid4())),
        format="json", HTTP_X_SCHOOL_ID=str(foreign.id),
    )
    assert r.status_code in (403, 404)
    assert not DaycareAttendance.objects.exists()


def test_care_staff_has_no_legacy_school_role_bypass():
    d = setup()
    UserRole.objects.filter(user=d["actor"]).delete()
    assert _checkin(d).status_code == 403
    assert not DaycareAttendance.objects.exists()


def test_unassigned_staff_cannot_read_center_roster():
    d = setup()
    d["coverage"].is_active = False
    d["coverage"].save()
    c = _client(d["actor"])
    r = c.get(f'/api/v1/aftercare/daycare/sites/{d["site"].id}/roster/')
    assert r.status_code == 403


def test_failed_release_does_not_create_custody_event():
    d = setup()
    admitted = _checkin(d)
    assert admitted.status_code == 201, admitted.data
    attendance = DaycareAttendance.objects.get(pk=admitted.data["attendance_id"])
    r = _release(d, attendance, identity_verified=False)
    assert r.status_code in (400, 403)
    assert not DaycareRelease.objects.exists()


def test_inactive_school_may_release_existing_child_not_admit_another():
    d = setup()
    admitted = _checkin(d)
    assert admitted.status_code == 201, admitted.data
    attendance = DaycareAttendance.objects.get(pk=admitted.data["attendance_id"])
    d["school"].is_active = False
    d["school"].save(update_fields=["is_active"])
    released = _release(d, attendance)
    assert released.status_code == 201, getattr(released, "data", released.content)
    assert DaycareRelease.objects.filter(attendance=attendance).exists()
    assert _checkin(d).status_code in (403, 404)

def test_inactive_school_rejects_foreign_school_custody_header():
    d = setup()
    admitted = _checkin(d)
    assert admitted.status_code == 201
    attendance = DaycareAttendance.objects.get(pk=admitted.data["attendance_id"])
    d["school"].is_active = False
    d["school"].save(update_fields=["is_active"])
    foreign = School.objects.create(name="Other test organization")
    client = _client(d["actor"])
    response = client.post(
        "/api/v1/aftercare/daycare/attendance/release/",
        dict(site_id=str(d["site"].id), room_id=str(d["room"].id),
             attendance_id=str(attendance.id),
             guardian_authority_id=str(d["authority"].id),
             request_key=str(uuid4()), identity_verified=True,
             identity_method="GOVERNMENT_PHOTO_ID"),
        format="json", HTTP_X_SCHOOL_ID=str(foreign.pk))
    assert response.status_code in (403, 404)
    assert not DaycareRelease.objects.exists()
