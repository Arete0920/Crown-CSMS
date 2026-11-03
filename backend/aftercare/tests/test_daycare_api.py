"""Synthetic API contract: tenant, staff RBAC and custody service are not client-controlled."""
from uuid import uuid4

import pytest
from rest_framework.test import APIClient
from core.models import School, UserAccount, UserRole
from aftercare.models import DaycareAttendance, DaycareRelease, DaycareSite, DaycareRoomStaffCoverage
from audit.models import AuditLog
from aftercare.tests.test_daycare_checkin import setup

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _bearer_client(user, *, school_id=None, expired=False):
    from datetime import timedelta
    from django.utils import timezone
    from rest_framework_simplejwt.tokens import AccessToken

    token = AccessToken.for_user(user)
    token["school_id"] = str(user.school_id)
    if expired:
        token.set_exp(from_time=timezone.now() - timedelta(hours=1), lifetime=timedelta(seconds=1))
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_X_SCHOOL_ID=str(school_id or user.school_id),
    )
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
        # Either pre-auth tenant validation or authentication may reject
        # first, depending on middleware ordering in the full suite.
        # Neither response may grant access or mutate custody records.
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


@pytest.mark.parametrize("read", ["directory", "roster"])
def test_real_bearer_reaches_inactive_school_open_custody_reads(read):
    d = setup()
    client = _bearer_client(d["actor"])
    admitted = _checkin(d, client)
    assert admitted.status_code == 201, admitted.data
    d["school"].is_active = False
    d["school"].save(update_fields=["is_active"])
    url = "/api/v1/aftercare/daycare/sites/"
    if read == "roster":
        url += f'{d["site"].pk}/roster/'

    response = client.get(url)
    assert response.status_code == 200, getattr(response, "data", response.content)
    if read == "directory":
        assert [site["site_id"] for site in response.data["sites"]] == [str(d["site"].pk)]
    else:
        assert response.data["children_present"] == 1
        assert response.data["rows"][0]["attendance_id"] == admitted.data["attendance_id"]
    assert DaycareAttendance.objects.count() == 1
    assert not DaycareRelease.objects.exists()
    assert AuditLog.objects.filter(action="diadem.daycare.checkin").count() == 1


def test_real_bearer_can_release_inactive_custody_without_reopening_school_operations():
    d = setup()
    client = _bearer_client(d["actor"])
    admitted = _checkin(d, client)
    assert admitted.status_code == 201, admitted.data
    d["school"].is_active = False
    d["school"].save(update_fields=["is_active"])

    # Inactive-school general navigation must remain inaccessible. The
    # request-layer guard may fail closed with 400 or inactive-tenant 404.
    nav = client.get("/api/v1/nav/")
    assert nav.status_code in (400, 404)
    assert "detail" in nav.json()
    assert client.get("/api/v1/aftercare/roster/today/").status_code == 404
    assert _checkin(d, client).status_code == 404
    released = _release(d, admitted.data["attendance_id"], client)
    assert released.status_code == 201, getattr(released, "data", released.content)
    assert DaycareAttendance.objects.count() == 1
    assert DaycareRelease.objects.count() == 1
    assert AuditLog.objects.filter(action="diadem.daycare.release").count() == 1
    assert client.get("/api/v1/aftercare/daycare/sites/").data["sites"] == []


@pytest.mark.parametrize("denial", ["expired", "invalid", "role_revoked", "permission_revoked"])
def test_inactive_custody_bearer_deferral_does_not_grant_authority(denial):
    from core.models import RolePermission

    d = setup()
    assert _checkin(d).status_code == 201
    d["school"].is_active = False
    d["school"].save(update_fields=["is_active"])
    client = _bearer_client(d["actor"], expired=denial == "expired")
    if denial == "invalid":
        client.credentials(
            HTTP_AUTHORIZATION="Bearer invalid.signature.token",
            HTTP_X_SCHOOL_ID=str(d["school"].pk),
        )
    elif denial == "role_revoked":
        d["actor"].roles.all().delete()
    elif denial == "permission_revoked":
        RolePermission.objects.filter(
            role_code="DAYCARE_STAFF", permission__code="diadem.daycare.view",
        ).delete()

    response = client.get("/api/v1/aftercare/daycare/sites/")
    assert response.status_code == (401 if denial in {"expired", "invalid"} else 403)
    assert "sites" not in response.data
    assert DaycareAttendance.objects.count() == 1
    assert not DaycareRelease.objects.exists()
    assert AuditLog.objects.filter(action="diadem.daycare.checkin").count() == 1


@pytest.mark.parametrize("superuser", [False, True])
def test_inactive_custody_bearer_never_accepts_foreign_school_override(superuser):
    d = setup()
    assert _checkin(d).status_code == 201
    d["actor"].is_superuser = superuser
    d["actor"].save(update_fields=["is_superuser"])
    foreign = School.objects.create(name="Foreign inactive childcare tenant", is_active=False)
    response = _bearer_client(d["actor"], school_id=foreign.pk).get(
        "/api/v1/aftercare/daycare/sites/",
    )
    assert response.status_code == 404
    assert DaycareAttendance.objects.count() == 1
    assert not DaycareRelease.objects.exists()


def test_inactive_school_allows_only_verified_open_custody_roster_and_release():
    d = setup()
    c = _client(d["actor"])
    admitted = _checkin(d, c)
    assert admitted.status_code == 201, admitted.data
    attendance = DaycareAttendance.objects.get(pk=admitted.data["attendance_id"])
    d["school"].is_active = False
    d["school"].save(update_fields=["is_active"])

    # Staff must be able to identify an already-admitted child for safe release,
    # even when ordinary school reads and new admissions have been disabled.
    roster_url = f'/api/v1/aftercare/daycare/sites/{d["site"].id}/roster/'
    roster = c.get(roster_url)
    assert roster.status_code == 200, getattr(roster, "data", None)
    assert roster.data["children_present"] == 1
    assert roster.data["rows"][0]["attendance_id"] == str(attendance.pk)
    assert c.get("/api/v1/aftercare/roster/today/").status_code == 404
    assert _checkin(d, c).status_code in (403, 404)

    finished = _release(d, attendance, c)
    assert finished.status_code == 201, getattr(finished, "data", None)
    after = c.get(roster_url)
    assert after.status_code == 200
    assert after.data["children_present"] == 0


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

def test_site_directory_restricts_school_and_current_staff_assignment():
    d = setup()
    foreign = School.objects.create(name="Foreign childcare center")
    DaycareSite.objects.create(school=foreign, code="foreign", name="Foreign Site")
    extra = DaycareSite.objects.create(
        school=d["school"], code="other", name="Other Same-School Site"
    )
    c = _client(d["actor"])
    directory = c.get("/api/v1/aftercare/daycare/sites/")
    assert directory.status_code == 200, getattr(directory, "data", None)
    assert directory.data == {"sites": [{
        "site_id": str(d["site"].id),
        "name": d["site"].name,
        "is_active": True,
    }]}
    # School ownership alone is insufficient for staff to read a different site.
    assert c.get(f"/api/v1/aftercare/daycare/sites/{extra.id}/roster/").status_code == 403
    assert c.get(
        "/api/v1/aftercare/daycare/sites/",
        HTTP_X_SCHOOL_ID=str(foreign.id),
    ).status_code == 404


def test_site_directory_denies_unverified_staff_and_legacy_school_grants():
    d = setup()
    c = _client(d["actor"])
    d["coverage"].is_active = False
    d["coverage"].save(update_fields=["is_active"])
    assert c.get("/api/v1/aftercare/daycare/sites/").status_code == 403
    assert c.get(
        f"/api/v1/aftercare/daycare/sites/{d['site'].id}/roster/"
    ).status_code == 403
    # Restoring a shift never grants access to a user without a Diadem role.
    d["coverage"].is_active = True
    d["coverage"].save(update_fields=["is_active"])
    UserRole.objects.filter(user=d["actor"]).delete()
    assert c.get("/api/v1/aftercare/daycare/sites/").status_code == 403


def test_site_directory_requires_authentication_and_does_not_write_custody():
    d = setup()
    unauthenticated = APIClient()
    response = unauthenticated.get("/api/v1/aftercare/daycare/sites/")
    assert response.status_code in (400, 401, 403)
    response = unauthenticated.get(
        "/api/v1/aftercare/daycare/sites/",
        HTTP_X_SCHOOL_ID=str(d["school"].id),
    )
    assert response.status_code in (401, 403)
    assert not DaycareAttendance.objects.exists()
    assert not DaycareRelease.objects.exists()


def test_director_directory_and_roster_do_not_require_classroom_shift():
    from core.models import CrownPermission, RolePermission
    d = setup()
    UserRole.objects.create(
        school=d["school"], user=d["director"], role_code="DAYCARE_DIRECTOR"
    )
    permission, _ = CrownPermission.objects.get_or_create(
        code="diadem.daycare.view",
        defaults={"description": "Synthetic Diadem view permission"},
    )
    RolePermission.objects.get_or_create(
        role_code="DAYCARE_DIRECTOR", permission=permission
    )
    c = _client(d["director"])
    sites = c.get("/api/v1/aftercare/daycare/sites/")
    assert sites.status_code == 200
    assert sites.data["sites"][0]["site_id"] == str(d["site"].id)
    roster = c.get(f"/api/v1/aftercare/daycare/sites/{d['site'].id}/roster/")
    assert roster.status_code == 200
    assert roster.data["children_present"] == 0


def test_deactivated_school_may_inspect_existing_custody_but_not_new_admit():
    d = setup()
    c = _client(d["actor"])
    attendance = _checkin(d, c)
    assert attendance.status_code == 201
    d["school"].is_active = False
    d["school"].save(update_fields=["is_active"])
    sites = c.get("/api/v1/aftercare/daycare/sites/")
    assert sites.status_code == 200, getattr(sites, "data", None)
    assert sites.data["sites"] == [{
        "site_id": str(d["site"].id),
        "name": d["site"].name,
        "is_active": True,
    }]
    roster = c.get(f"/api/v1/aftercare/daycare/sites/{d['site'].id}/roster/")
    assert roster.status_code == 200
    assert roster.data["children_present"] == 1
    assert _checkin(d, c).status_code in (403, 404)

def test_inactive_school_site_directory_lists_only_unresolved_custody():
    d = setup()
    c = _client(d["actor"])
    d["school"].is_active = False
    d["school"].save(update_fields=["is_active"])
    # An inactive organization with no open child custody has no visible sites.
    before = c.get("/api/v1/aftercare/daycare/sites/")
    assert before.status_code == 200
    assert before.data["sites"] == []
    # Restore activity solely to create a valid synthetic admission.
    d["school"].is_active = True
    d["school"].save(update_fields=["is_active"])
    checked = _checkin(d, c)
    assert checked.status_code == 201
    d["school"].is_active = False
    d["school"].save(update_fields=["is_active"])
    open_sites = c.get("/api/v1/aftercare/daycare/sites/")
    assert open_sites.status_code == 200
    assert [s["site_id"] for s in open_sites.data["sites"]] == [str(d["site"].id)]
    released = _release(d, checked.data["attendance_id"], c)
    assert released.status_code == 201
    finished = c.get("/api/v1/aftercare/daycare/sites/")
    assert finished.status_code == 200
    assert finished.data["sites"] == []
    # The emergency directory never expands normal school operations.
    assert _checkin(d, c).status_code in (403, 404)


def test_inactive_directory_denies_foreign_school_and_unauthenticated_users():
    d = setup()
    d["school"].is_active = False
    d["school"].save(update_fields=["is_active"])
    foreign = School.objects.create(name="Foreign childcare organization")
    staff = _client(d["actor"])
    denied = staff.get(
        "/api/v1/aftercare/daycare/sites/",
        HTTP_X_SCHOOL_ID=str(foreign.id),
    )
    assert denied.status_code in (403, 404)
    anonymous = APIClient().get(
        "/api/v1/aftercare/daycare/sites/",
        HTTP_X_SCHOOL_ID=str(d["school"].id),
    )
    assert anonymous.status_code in (401, 403, 404)
    assert not DaycareAttendance.objects.exists()


def test_directory_and_roster_reject_conflicting_live_staff_room_coverage():
    # A second simultaneous qualified room should be impossible through normal
    # model writes. Guard read authorization too, for legacy data anomalies.
    from unittest.mock import patch
    from aftercare.daycare_api import _visible_staff_room_ids
    d = setup()
    c = _client(d["actor"])
    # Force an anomalous second room ID in the qualified assignment query,
    # without injecting invalid childcare records into the DB.
    original_filter = DaycareRoomStaffCoverage.objects.filter

    def mock_filter(*args, **kwargs):
        qs = original_filter(*args, **kwargs)
        if kwargs.get("staff") == d["actor"] and kwargs.get("is_qualified") is True:
            return _DuplicateQualifiedRoomIds(qs)
        return qs

    class _DuplicateQualifiedRoomIds:
        def __init__(self, qs):
            self.qs = qs
        def exclude(self, **kwargs):
            return self
        def values_list(self, *args, **kwargs):
            return [d["room"].id, uuid4()]

    with patch.object(DaycareRoomStaffCoverage.objects, "filter", side_effect=mock_filter):
        response = c.get("/api/v1/aftercare/daycare/sites/")
    assert response.status_code == 403
    assert not DaycareAttendance.objects.exists()


def _release_authorities(d, attendance_id, client=None, *, site_id=None, **headers):
    return (client or _client(d["actor"])).get(
        "/api/v1/aftercare/daycare/sites/"
        f"{site_id or d['site'].id}/attendance/{attendance_id}/release-authorities/",
        **headers,
    )


def test_release_candidates_are_current_scoped_and_observational():
    d = setup()
    admitted = _checkin(d)
    assert admitted.status_code == 201, admitted.data
    attendance_id = admitted.data["attendance_id"]
    response = _release_authorities(d, attendance_id)
    assert response.status_code == 200, getattr(response, "data", None)
    assert response.data["site_id"] == str(d["site"].id)
    assert response.data["attendance_id"] == attendance_id
    assert response.data["status"] == "candidates_only"
    assert response.data["options"] == [{
        "authority_id": str(d["authority"].id),
        "guardian_name": "Synthetic Guardian",
    }]
    assert not DaycareRelease.objects.exists()
    assert not AuditLog.objects.filter(action="diadem.daycare.release").exists()
    assert _release(d, attendance_id).status_code == 201
    assert _release_authorities(d, attendance_id).status_code == 404


@pytest.mark.parametrize("restriction", [
    "revoked", "custody_restricted", "verification_revoked",
    "authority_expired", "authority_not_started",
])
def test_release_candidates_exclude_unverified_or_out_of_window_guardians(restriction):
    from datetime import timedelta
    from django.utils import timezone
    d = setup()
    admitted = _checkin(d)
    assert admitted.status_code == 201
    authority = d["authority"]
    if restriction == "revoked":
        authority.is_active = False
    elif restriction == "custody_restricted":
        authority.is_active = False
        authority.custody_status = "RESTRICTED"
    elif restriction == "verification_revoked":
        authority.is_active = False
        authority.verified_by = None
        authority.verified_at = None
    elif restriction == "authority_expired":
        authority.effective_until = timezone.now() - timedelta(seconds=1)
    else:
        authority.effective_from = timezone.now() + timedelta(hours=1)
    authority.save()
    response = _release_authorities(d, admitted.data["attendance_id"])
    assert response.status_code == 200
    assert response.data["options"] == []
    assert not DaycareRelease.objects.exists()


def test_release_candidates_require_release_grant_and_current_staff_assignment():
    from core.models import RolePermission
    d = setup()
    admitted = _checkin(d)
    assert admitted.status_code == 201
    row = admitted.data["attendance_id"]
    other_site = DaycareSite.objects.create(
        school=d["school"], name="Other center", code="other"
    )
    assert _release_authorities(d, row, site_id=other_site.id).status_code == 404
    assert _release_authorities(d, uuid4()).status_code == 404
    d["coverage"].is_active = False
    d["coverage"].save()
    assert _release_authorities(d, row).status_code == 403
    d["coverage"].is_active = True
    d["coverage"].save()
    RolePermission.objects.filter(
        role_code="DAYCARE_STAFF", permission__code="diadem.daycare.release"
    ).delete()
    assert _release_authorities(d, row).status_code == 403
    assert not DaycareRelease.objects.exists()


def test_release_candidates_preserve_inactive_school_custody_exit():
    d = setup()
    admitted = _checkin(d)
    assert admitted.status_code == 201
    d["school"].is_active = False
    d["school"].save(update_fields=["is_active"])
    response = _release_authorities(
        d, admitted.data["attendance_id"], _bearer_client(d["actor"])
    )
    assert response.status_code == 200, getattr(response, "data", None)
    assert [item["authority_id"] for item in response.data["options"]] == [
        str(d["authority"].id)
    ]
    assert not DaycareRelease.objects.exists()


def test_release_candidates_inactive_school_route_cannot_bypass_method_or_scope():
    d = setup()
    admitted = _checkin(d)
    assert admitted.status_code == 201
    row = admitted.data["attendance_id"]
    d["school"].is_active = False
    d["school"].save(update_fields=["is_active"])
    valid_url = (
        f"/api/v1/aftercare/daycare/sites/{d['site'].id}/"
        f"attendance/{row}/release-authorities/"
    )
    bearer = _bearer_client(d["actor"])
    # Only the exact candidate GET can reach its guarded view. A matching
    # prefix, a different verb, or a foreign school must fail closed.
    assert bearer.get(valid_url).status_code == 200
    assert bearer.post(valid_url, {}, format="json").status_code in (404, 405)
    assert bearer.get(valid_url + "extra/").status_code == 404
    assert bearer.get(
        valid_url,
        HTTP_X_SCHOOL_ID=str(School.objects.create(name="Foreign disabled scope").id),
    ).status_code == 404
    assert not DaycareRelease.objects.exists()


def test_release_candidates_deny_anonymous_and_foreign_school_context():
    d = setup()
    admitted = _checkin(d)
    assert admitted.status_code == 201
    row = admitted.data["attendance_id"]
    url = (f"/api/v1/aftercare/daycare/sites/{d['site'].id}/"
           f"attendance/{row}/release-authorities/")
    anonymous = APIClient().get(url, HTTP_X_SCHOOL_ID=str(d["school"].id))
    assert anonymous.status_code in (401, 403)
    foreign = School.objects.create(name="Foreign care organization")
    response = _release_authorities(
        d, row, _client(d["actor"]), HTTP_X_SCHOOL_ID=str(foreign.id)
    )
    assert response.status_code == 404
    assert not DaycareRelease.objects.exists()
