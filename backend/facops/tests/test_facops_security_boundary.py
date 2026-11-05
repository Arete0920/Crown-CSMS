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


def test_requester_cannot_set_work_order_lifecycle_or_assignment(subjects):
    """Request creation must not be a substitute for facilities.write."""
    f = subjects
    c = client(f["requester"], f["a"])
    proposals = (
        ("status", "DONE"),
        ("priority", "URGENT"),
        ("assigned_to", str(f["facilities"].pk)),
        ("labor_minutes", 999),
        ("due_at", "2026-11-01T12:00:00Z"),
    )
    for field, value in proposals:
        response = c.post(
            "/api/facilities/work-orders/",
            {"title": f"Unauthorized {field}", field: value},
            format="json",
        )
        assert response.status_code == 400, (field, response.data)
        assert not WorkOrder.objects.filter(title=f"Unauthorized {field}").exists()

    clean = c.post(
        "/api/facilities/work-orders/", {"title": "Unprivileged legitimate request"},
        format="json",
    )
    assert clean.status_code == 201, clean.data
    order = WorkOrder.objects.get(pk=clean.data["id"])
    assert order.requested_by_id == f["requester"].pk
    assert order.status == WorkOrder.STATUS_NEW
    assert order.assigned_to_id is None
    assert order.labor_minutes == 0


def test_work_order_foreign_school_relationships_are_rejected(subjects):
    """Tenant-owned location, asset and assignee IDs cannot be forged."""
    from facops.models import Asset

    f = subjects
    foreign_location = Location.objects.create(
        school=f["b"], name="Foreign synthetic room"
    )
    foreign_asset = Asset.objects.create(
        school=f["b"], name="Foreign synthetic asset"
    )
    c = client(f["facilities"], f["a"])
    for field, foreign in (
        ("location", foreign_location.pk),
        ("asset", foreign_asset.pk),
        ("assigned_to", f["other_school_staff"].pk),
    ):
        response = c.post(
            "/api/facilities/work-orders/",
            {"title": f"Cross school {field}", field: str(foreign)},
            format="json",
        )
        assert response.status_code == 400, (field, response.data)
        assert not WorkOrder.objects.filter(title=f"Cross school {field}").exists()



def test_campus_relationship_fields_reject_foreign_school_references(subjects):
    """Every writable related ID must resolve inside the selected school."""
    from facops.models import Asset

    f = subjects
    foreign_location = Location.objects.create(
        school=f["b"], name="Foreign campus room",
    )
    foreign_asset = Asset.objects.create(
        school=f["b"], name="Foreign campus asset",
    )
    own_location = Location.objects.create(
        school=f["a"], name="Own campus room",
    )
    facility = client(f["facilities"], f["a"])
    safety = client(f["safety"], f["a"])

    proposals = (
        (facility, "/api/facilities/locations/", {"name": "Foreign location parent", "parent": str(foreign_location.pk)}),
        (facility, "/api/facilities/assets/", {"name": "Foreign asset location", "location": str(foreign_location.pk)}),
        (safety, "/api/security/incidents/", {"title": "Foreign incident location", "location": str(foreign_location.pk)}),
        (safety, "/api/security/incidents/", {"title": "Foreign related asset", "related_asset": str(foreign_asset.pk)}),
        (safety, "/api/security/incidents/", {"title": "Foreign incident assignee", "assigned_to": str(f["other_school_staff"].pk)}),
    )
    for actor, route, data in proposals:
        denied = actor.post(route, data, format="json")
        assert denied.status_code == 400, (route, data, denied.data)

    # Legitimate within-school references remain usable.
    assert facility.post(
        "/api/facilities/locations/",
        {"name": "Permitted child location", "parent": str(own_location.pk)},
        format="json",
    ).status_code == 201
    assert facility.post(
        "/api/facilities/assets/",
        {"name": "Permitted local asset", "location": str(own_location.pk)},
        format="json",
    ).status_code == 201
    assert safety.post(
        "/api/security/incidents/",
        {"title": "Permitted school incident", "location": str(own_location.pk)},
        format="json",
    ).status_code == 201


def test_openapi_fake_view_does_not_require_tenant_header():
    """Documentation introspection cannot dilute runtime school selection."""
    from types import SimpleNamespace

    from rest_framework.request import Request
    from rest_framework.test import APIRequestFactory

    from facops.api.serializers import (
        AssetSerializer, LocationSerializer, SafetyIncidentSerializer,
        WorkOrderSerializer,
    )
    from households.scoping import MissingSchoolContext

    unscoped_request = Request(APIRequestFactory().get("/api/facilities/work-orders/"))
    for serializer_class in (
        LocationSerializer, AssetSerializer, WorkOrderSerializer,
        SafetyIncidentSerializer,
    ):
        schema_serializer = serializer_class(context={
            "request": unscoped_request,
            "view": SimpleNamespace(swagger_fake_view=True),
        })
        assert schema_serializer.fields, serializer_class.__name__
        actual_serializer = serializer_class(context={
            "request": unscoped_request,
            "view": SimpleNamespace(swagger_fake_view=False),
        })
        with pytest.raises(MissingSchoolContext):
            _ = actual_serializer.fields


def test_work_order_summary_needs_facilities_read_or_edit_grant(subjects):
    f = subjects
    for actor in (f["requester"], f["staff"], f["safety"]):
        assert client(actor, f["a"]).get("/api/facilities/summary/").status_code == 403
    granted = client(f["facilities"], f["a"]).get("/api/facilities/summary/")
    assert granted.status_code == 200
    assert granted.json()["total_open_work_orders"] >= 1
    foreign = client(f["other_school_staff"], f["a"]).get("/api/facilities/summary/")
    assert foreign.status_code in (403, 404)
