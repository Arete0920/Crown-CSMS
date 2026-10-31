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
        # Middleware-enabled tests deny missing context with 400; in the
        # coverage runner authentication can reject first with 401/403.
        # All configurations must be fail-closed with no attendance write.
        assert response.status_code in (400, 401, 403)
        if response.status_code == 400:
            assert response.json()["code"] == "missing_tenant"
    # With a valid school selector, tenant resolution succeeds but DRF must
    # independently reject the unauthenticated caller.
    header = {"HTTP_X_SCHOOL_ID": str(d["school"].id)}
    for response in (
        c.post("/api/v1/aftercare/daycare/attendance/checkin/",
            dict(site_id=str(d["site"].id),room_id=str(d["room"].id),
                 child_id=str(d["child"].id),program_code="DAYCARE",
                 request_key=str(uuid4())),format="json",**header),
        c.get(f'/api/v1/aftercare/daycare/sites/{d["site"].id}/roster/',**header),
        c.post("/api/v1/aftercare/daycare/attendance/release/",
            dict(site_id=str(d["site"].id),room_id=str(d["room"].id),
                 attendance_id=str(uuid4()),
                 guardian_authority_id=str(d["authority"].id),
                 request_key=str(uuid4()),identity_verified=True,
                 identity_method="GOVERNMENT_PHOTO_ID"),format="json",**header),
    ):
        assert response.status_code in (401,403)
    assert not DaycareAttendance.objects.exists()
    assert not DaycareRelease.objects.exists()


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

def test_site_directory_is_school_scoped_and_staff_visible():
    d = setup()
    c = _client(d["actor"])
    r = c.get("/api/v1/aftercare/daycare/sites/")
    assert r.status_code == 200, getattr(r, "data", None)
    assert r.data["sites"] == [{"site_id": str(d["site"].id), "name": d["site"].name, "is_active": True}]


def test_site_directory_denies_staff_without_current_verified_coverage():
    d = setup()
    d["coverage"].is_active = False
    d["coverage"].save()
    r = _client(d["actor"]).get("/api/v1/aftercare/daycare/sites/")
    assert r.status_code == 200
    assert r.data["sites"] == []


def test_site_directory_denies_foreign_tenant_selection():
    d = setup()
    foreign = School.objects.create(name="Foreign synthetic daycare")
    r = _client(d["actor"]).get("/api/v1/aftercare/daycare/sites/", HTTP_X_SCHOOL_ID=str(foreign.pk))
    assert r.status_code in (403, 404)

def test_scheduled_candidates_are_scoped_and_not_yet_attendance():
    d = setup()
    client = _client(d["actor"])
    response = client.get(f'/api/v1/aftercare/daycare/sites/{d["site"].id}/scheduled/')
    assert response.status_code == 200, getattr(response, "data", None)
    assert len(response.data["rows"]) == 1
    assert response.data["rows"][0]["child_id"] == str(d["child"].id)
    assert not DaycareAttendance.objects.exists()
    assert _checkin(d).status_code == 201
    after = client.get(f'/api/v1/aftercare/daycare/sites/{d["site"].id}/scheduled/')
    assert after.status_code == 200
    assert after.data["rows"] == []


def test_pickup_candidates_only_for_open_custody_and_verified_guardian():
    d = setup()
    admitted = _checkin(d)
    assert admitted.status_code == 201
    attendance_id = admitted.data["attendance_id"]
    client = _client(d["actor"])
    url = f'/api/v1/aftercare/daycare/attendance/{attendance_id}/pickup-authorities/'
    response = client.get(url)
    assert response.status_code == 200, getattr(response, "data", None)
    assert response.data["recipients"] == [{
        "guardian_authority_id": str(d["authority"].id),
        "guardian_name": "Synthetic Guardian",
    }]
    d["authority"].is_active = False
    d["authority"].save()
    assert client.get(url).data["recipients"] == []
    d["authority"].is_active = True
    d["authority"].save()
    assert _release(d, DaycareAttendance.objects.get(pk=attendance_id)).status_code == 201
    assert client.get(url).status_code == 404


def test_lookup_endpoints_deny_foreign_school_selector():
    d = setup()
    foreign = School.objects.create(name="Foreign fictional center")
    client = _client(d["actor"])
    r = client.get(
        f'/api/v1/aftercare/daycare/sites/{d["site"].id}/scheduled/',
        HTTP_X_SCHOOL_ID=str(foreign.id),
    )
    assert r.status_code in (403, 404)
    admitted = _checkin(d)
    assert admitted.status_code == 201
    r = client.get(
        f'/api/v1/aftercare/daycare/attendance/{admitted.data["attendance_id"]}/pickup-authorities/',
        HTTP_X_SCHOOL_ID=str(foreign.id),
    )
    assert r.status_code in (403, 404)


def test_inactive_school_staff_can_identify_open_custody_but_cannot_admit():
    d = setup()
    admitted = _checkin(d)
    assert admitted.status_code == 201
    attendance_id = admitted.data["attendance_id"]
    d["school"].is_active = False
    d["school"].save(update_fields=["is_active"])
    client = _client(d["actor"])

    sites = client.get("/api/v1/aftercare/daycare/sites/")
    assert sites.status_code == 200, getattr(sites, "data", None)
    assert any(site["site_id"] == str(d["site"].id) for site in sites.data["sites"])
    roster = client.get(f'/api/v1/aftercare/daycare/sites/{d["site"].id}/roster/')
    assert roster.status_code == 200, getattr(roster, "data", None)
    assert roster.data["rows"][0]["attendance_id"] == attendance_id
    guardians = client.get(
        f"/api/v1/aftercare/daycare/attendance/{attendance_id}/pickup-authorities/"
    )
    assert guardians.status_code == 200, getattr(guardians, "data", None)
    assert guardians.data["recipients"][0]["guardian_authority_id"] == str(d["authority"].id)

    # Admission and the schedule are never reopened by the custody exit exception.
    assert client.get(
        f'/api/v1/aftercare/daycare/sites/{d["site"].id}/scheduled/'
    ).status_code in (403, 404)
    assert _checkin(d, client).status_code in (403, 404)
    assert DaycareAttendance.objects.count() == 1
    assert DaycareRelease.objects.count() == 0


def test_inactive_school_custody_reads_reject_cross_school_selector():
    d = setup()
    admitted = _checkin(d)
    assert admitted.status_code == 201
    d["school"].is_active = False
    d["school"].save(update_fields=["is_active"])
    foreign = School.objects.create(name="Foreign synthetic organization")
    client = _client(d["actor"])
    paths = [
        "/api/v1/aftercare/daycare/sites/",
        f'/api/v1/aftercare/daycare/sites/{d["site"].id}/roster/',
        f'/api/v1/aftercare/daycare/attendance/{admitted.data["attendance_id"]}/pickup-authorities/',
    ]
    for path in paths:
        response = client.get(path, HTTP_X_SCHOOL_ID=str(foreign.pk))
        assert response.status_code in (403, 404), (path, response.status_code)
    assert DaycareRelease.objects.count() == 0


def test_diadem_navigation_link_requires_explicit_school_scoped_role_grant():
    # nav_view is a plain Django view; DRF force_authenticate does not attach
    # request.user to it. Supply the authenticated principal and tenant via
    # RequestFactory to verify its actual permission-derived menu contract.
    import json
    from django.test import RequestFactory
    from core.views_nav import nav_view

    d = setup()
    request = RequestFactory().get("/api/v1/nav/")
    request.user = d["actor"]
    request.school = d["school"]

    response = nav_view(request)
    assert response.status_code == 200
    visible = [item["href"] for group in json.loads(response.content)["groups"]
               for item in group["items"]]
    assert "/diadem/daycare" in visible
    assert "/extended-care" not in visible

    UserRole.objects.filter(user=d["actor"], school=d["school"]).delete()
    response = nav_view(request)
    assert response.status_code == 200
    after = [item["href"] for group in json.loads(response.content)["groups"]
             for item in group["items"]]
    assert "/diadem/daycare" not in after
