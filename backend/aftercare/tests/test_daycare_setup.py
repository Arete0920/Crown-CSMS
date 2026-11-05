"""Synthetic director setup; proposals never activate child custody or licensing."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.db import connection, connections
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from aftercare.models import DaycareSite, DaycareRoom, DaycareAttendance, DaycareRelease
from aftercare.daycare_setup import create_configuration
from audit.models import AuditLog
from core.models import School, UserAccount, UserRole, CrownPermission, RolePermission
from subscriptions.models import Feature, Plan, TenantSubscription, EntitlementOverride
from tenants.models import TenantProfile

pytestmark = pytest.mark.django_db
BASE = "/api/v1/aftercare/daycare/setup/sites/"
SITE = {"code": "north", "name": "Synthetic North", "operating_mode": "STANDALONE", "jurisdiction": "US-DE"}
ROOM = {"code": "toddler", "name": "Synthetic Toddler", "licensed_capacity": 12,
        "max_children_per_staff": 6, "policy_source": "Proposed synthetic policy; unverified",
        "proposed_min_age_months": 12, "proposed_max_age_months": 23,
        "proposed_policy_from": "2026-11-01", "proposed_policy_until": "2027-10-31"}


def tenant():
    key = uuid4().hex
    school = School.objects.create(name=f"Synthetic center {key}", timezone="America/New_York")
    actor = UserAccount.objects.create_user(username=key, school=school)
    UserRole.objects.create(user=actor, school=school, role_code="DAYCARE_DIRECTOR")
    permission, _ = CrownPermission.objects.get_or_create(code="diadem.daycare.configure")
    RolePermission.objects.get_or_create(role_code="DAYCARE_DIRECTOR", permission=permission)
    profile = TenantProfile.objects.create(school=school, slug=key, status="active")
    plan = Plan.objects.create(code=key, name="Synthetic care")
    TenantSubscription.objects.create(school_id=school.pk, plan=plan)
    feature, _ = Feature.objects.get_or_create(key="diadem.daycare", defaults={"name": "Daycare"})
    entitlement = EntitlementOverride.objects.create(school_id=school.pk, feature=feature, enabled=True)
    token = AccessToken.for_user(actor)
    token["school_id"] = str(school.pk)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_SCHOOL_ID=str(school.pk))
    return school, actor, client, profile, entitlement


def post_site(client, **changes):
    return client.post(BASE, {**SITE, **changes}, format="json")


def room_url(site):
    return f"{BASE}{site}/rooms/"


def test_director_creates_standalone_center_room_and_authoritative_readback():
    school, actor, client, _, _ = tenant()
    result = post_site(client)
    assert result.status_code == 201, result.content
    site = DaycareSite.objects.get(pk=result.data["site_id"])
    assert site.school_id == school.pk and not site.is_active
    assert site.jurisdiction == "US-DE" and site.operating_mode == "STANDALONE"
    result = client.post(room_url(site.pk), ROOM, format="json")
    assert result.status_code == 201, result.data
    room = DaycareRoom.objects.get(pk=result.data["room_id"])
    assert room.proposed_policy_from == date(2026, 11, 1)
    assert not room.is_active and room.policy_verified_by_id is None and room.policy_verified_at is None
    read = client.get(room_url(site.pk))
    assert read.status_code == 200 and read.data["school_id"] == str(school.pk)
    assert read.data["site_id"] == str(site.pk) and read.data["rooms"][0]["room_id"] == str(room.pk)
    assert read.data["rooms"][0]["proposed_max_age_months"] == 23
    assert read.data["as_of"] and read.data["source"] == "aftercare.DaycareRoom"
    sites = client.get(BASE).data
    assert sites["sites"][0]["site_id"] == str(site.pk)
    events = AuditLog.objects.filter(action="diadem.daycare.configuration.created")
    assert events.count() == 2 and set(events.values_list("user_id", flat=True)) == {actor.pk}
    assert all(e.metadata["school_id"] == str(school.pk) and not e.metadata["is_active"] for e in events)
    assert DaycareAttendance.objects.count() == DaycareRelease.objects.count() == 0


def test_identical_retries_return_same_records_and_conflicting_reuse_is_409():
    _, _, client, _, _ = tenant()
    first = post_site(client, operating_mode="INTEGRATED")
    repeat = post_site(client, operating_mode="INTEGRATED")
    assert first.status_code == 201 and repeat.status_code == 200 and first.data == repeat.data
    assert post_site(client, name="Changed").status_code == 409
    url = room_url(first.data["site_id"])
    first_room = client.post(url, ROOM, format="json")
    repeated_room = client.post(url, ROOM, format="json")
    assert first_room.status_code == 201 and repeated_room.status_code == 200
    assert first_room.data == repeated_room.data
    assert client.post(url, {**ROOM, "licensed_capacity": 13}, format="json").status_code == 409
    assert DaycareSite.objects.count() == DaycareRoom.objects.count() == 1
    assert AuditLog.objects.filter(action="diadem.daycare.configuration.created").count() == 2


@pytest.mark.parametrize("role", ["DAYCARE_STAFF", "PARENT", "HEAD_OF_SCHOOL"])
def test_other_roles_cannot_configure_even_with_accidental_permission_grant(role):
    school, actor, client, _, _ = tenant()
    UserRole.objects.filter(user=actor).delete()
    UserRole.objects.create(user=actor, school=school, role_code=role)
    RolePermission.objects.get_or_create(role_code=role, permission=CrownPermission.objects.get(code="diadem.daycare.configure"))
    assert client.get(BASE).status_code == 403
    assert post_site(client).status_code == 403
    assert not DaycareSite.objects.exists()


@pytest.mark.parametrize("denial", ["no_role", "revoked_permission", "unlicensed", "inactive_tenant", "inactive_school", "inactive_user"])
def test_revoked_or_inactive_authority_and_entitlement_fail_closed(denial):
    school, actor, client, profile, entitlement = tenant()
    if denial == "no_role": UserRole.objects.filter(user=actor).delete()
    if denial == "revoked_permission": RolePermission.objects.filter(permission__code="diadem.daycare.configure").delete()
    if denial == "unlicensed": entitlement.enabled = False; entitlement.save()
    if denial == "inactive_tenant": profile.status = "suspended"; profile.save()
    if denial == "inactive_school": school.is_active = False; school.save(update_fields=["is_active"])
    if denial == "inactive_user": actor.is_active = False; actor.save(update_fields=["is_active"])
    assert post_site(client).status_code in (401, 403, 404)
    assert client.get(BASE).status_code in (401, 403, 404)
    assert not DaycareSite.objects.exists()


def test_two_tenants_cannot_select_or_discover_foreign_configuration():
    school_a, _, client_a, _, _ = tenant()
    school_b, _, client_b, _, _ = tenant()
    a, b = post_site(client_a).data, post_site(client_b).data
    assert a["site_id"] != b["site_id"]
    assert [s["site_id"] for s in client_a.get(BASE).data["sites"]] == [a["site_id"]]
    assert client_a.get(room_url(b["site_id"])).status_code == 404
    assert client_a.post(room_url(b["site_id"]), ROOM, format="json").status_code == 404
    assert post_site(client_a, school_id=str(school_b.pk)).status_code == 400
    # APIClient.credentials overrides per-request extras: change the actual
    # transport headers so these exercise foreign/conflicting selectors.
    own_headers = client_a._credentials.copy()
    client_a.credentials(**{**own_headers, "HTTP_X_SCHOOL_ID": str(school_b.pk)})
    assert client_a.get(BASE).status_code in (400, 403, 404)
    client_a.credentials(**{**own_headers, "HTTP_X_CROWN_SCHOOL_ID": str(school_b.pk)})
    assert client_a.get(BASE).status_code in (400, 403, 404)
    assert DaycareSite.objects.filter(school=school_a).count() == 1 and not DaycareRoom.objects.exists()


def test_anonymous_and_expired_token_cannot_read_or_create():
    school, actor, _, _, _ = tenant()
    client = APIClient()
    client.credentials(HTTP_X_SCHOOL_ID=str(school.pk))
    assert client.get(BASE).status_code in (401, 403, 404)
    token = AccessToken.for_user(actor)
    from datetime import timedelta
    token.set_exp(from_time=timezone.now() - timedelta(hours=1), lifetime=timedelta(seconds=1))
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_SCHOOL_ID=str(school.pk))
    assert post_site(client).status_code == 401
    assert not DaycareSite.objects.exists()


@pytest.mark.parametrize("change", [{"is_active": True}, {"policy_verified_by": str(uuid4())},
    {"policy_verified_at": "2026-11-01T12:00:00Z"}, {"licensed_capacity": 0},
    {"max_children_per_staff": -1}, {"proposed_min_age_months": 30},
    {"proposed_max_age_months": None}, {"proposed_policy_until": "2026-10-01"}])
def test_invalid_or_client_approved_room_is_denied_without_partial_write(change):
    _, _, client, _, _ = tenant()
    site = post_site(client).data
    assert client.post(room_url(site["site_id"]), {**ROOM, **change}, format="json").status_code == 400
    assert not DaycareRoom.objects.exists()
    assert AuditLog.objects.filter(action="diadem.daycare.configuration.created").count() == 1


def test_audit_failure_rolls_back_configuration():
    _, _, client, _, _ = tenant()
    client.raise_request_exception = False
    with patch("aftercare.daycare_setup.AuditLog.objects.create", side_effect=RuntimeError("synthetic audit failure")):
        assert post_site(client).status_code == 500
    assert not DaycareSite.objects.exists()
    assert not AuditLog.objects.filter(action="diadem.daycare.configuration.created").exists()


@pytest.mark.django_db(transaction=True)
def test_postgresql_concurrent_configuration_retry_has_one_record_and_audit():
    if connection.vendor != "postgresql": pytest.skip("Real PostgreSQL configuration locking only.")
    school, actor, _, _, _ = tenant()
    barrier = Barrier(2)
    def worker():
        connections.close_all()
        try:
            barrier.wait(timeout=20)
            record, created = create_configuration(school_id=school.pk, actor_id=actor.pk, values=SITE)
            return record.pk, created
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: worker(), range(2)))
    assert len({pk for pk, _ in results}) == 1 and sum(created for _, created in results) == 1
    assert DaycareSite.objects.filter(school=school, code=SITE["code"]).count() == 1
    assert AuditLog.objects.filter(action="diadem.daycare.configuration.created").count() == 1
