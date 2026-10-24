"""Negative campus-operation authorization tests with synthetic tenants."""
import uuid

import pytest
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from facops.models import Location, WorkOrder

pytestmark = pytest.mark.django_db


@pytest.fixture
def subjects():
    a = School.objects.create(name="Synthetic Campus A")
    b = School.objects.create(name="Synthetic Campus B")
    def actor(label, school, staff=False):
        suffix = uuid.uuid4().hex[:12]
        return UserAccount.objects.create_user(
            username=f"{label}-{suffix}", email=f"{label}-{suffix}@example.invalid",
            school=school, is_staff=staff,
        )
    requester = actor("requester", a)
    staff = actor("staff-no-grant", a, True)
    facilities = actor("facilities-authorized", a, True)
    safety = actor("safety-authorized", a, True)
    other_school_staff = actor("other-school", b, True)
    for user, school, role, code in (
        (facilities, a, "facilities_manager", "facilities.edit"),
        (safety, a, "safety_manager", "safety.edit"),
        (other_school_staff, b, "facilities_manager", "facilities.edit"),
    ):
        UserRole.objects.create(user=user, school=school, role_code=role)
        perm, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code=role, permission=perm)
    order = WorkOrder.objects.create(school=a, title="Synthetic Repair", requested_by=requester)
    return locals()


def client(user, school):
    c = APIClient()
    c.force_authenticate(user=user)
    c.credentials(HTTP_X_SCHOOL_ID=str(school.pk), HTTP_X_ROLE="admin")
    return c


def test_client_role_hint_and_staff_bit_cannot_authorize_write(subjects):
    f = subjects
    for actor in (f["requester"], f["staff"]):
        c = client(actor, f["a"])
        assert c.post("/api/facilities/locations/", {"name": "Denied"}, format="json").status_code == 403
        assert c.post("/api/security/incidents/", {"title": "Denied"}, format="json").status_code == 403
        assert c.post("/api/security/alerts/emit/", {"title": "Denied"}, format="json").status_code == 403
        assert c.post(
            f"/api/facilities/work-orders/{f['order'].pk}/transition/",
            {"status": "DONE"}, format="json",
        ).status_code == 403
    f["order"].refresh_from_db()
    assert f["order"].status == WorkOrder.STATUS_NEW
    assert not Location.objects.filter(name="Denied").exists()


def test_reporter_can_create_work_order_but_not_edit_or_delete(subjects):
    f = subjects
    c = client(f["requester"], f["a"])
    assert c.post("/api/facilities/work-orders/", {"title": "Broken Door"}, format="json").status_code == 201
    assert c.patch(
        f"/api/facilities/work-orders/{f['order'].pk}/",
        {"status": "DONE"}, format="json",
    ).status_code == 403
    assert c.delete(f"/api/facilities/work-orders/{f['order'].pk}/").status_code == 403


def test_verified_grants_are_domain_separated(subjects):
    f = subjects
    facility = client(f["facilities"], f["a"])
    assert facility.post("/api/facilities/locations/", {"name": "Authorized"}, format="json").status_code == 201
    assert facility.post(
        f"/api/facilities/work-orders/{f['order'].pk}/transition/",
        {"status": "IN_PROGRESS"}, format="json",
    ).status_code == 200
    assert facility.post("/api/security/incidents/", {"title": "Not Authorized"}, format="json").status_code == 403
    safety = client(f["safety"], f["a"])
    assert safety.post("/api/security/incidents/", {"title": "Authorized"}, format="json").status_code == 201
    assert safety.post("/api/facilities/locations/", {"name": "Not Authorized"}, format="json").status_code == 403


def test_cross_school_selector_cannot_grant_facilities_access(subjects):
    f = subjects
    foreign = client(f["other_school_staff"], f["a"])
    assert foreign.get("/api/facilities/locations/").status_code in (403, 404)
    assert foreign.post(
        "/api/facilities/locations/", {"name": "Wrong School"}, format="json",
    ).status_code in (403, 404)
    assert not Location.objects.filter(name="Wrong School").exists()
