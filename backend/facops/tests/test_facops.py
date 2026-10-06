# backend/facops/tests/test_facops.py
"""
Phase 13.0 – Facilities, Maintenance & Security (facops) test suite.

Coverage:
  - URL routing (all 7 resource types + 2 summary endpoints)
  - Permission enforcement (unauthenticated, authenticated read-only, write roles)
  - CRUD for every resource type
  - Cross-tenant isolation
  - WorkOrder.transition custom action
  - Alert.emit custom action
  - facilities_summary / security_summary function views
"""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import School
from facops.models import (
    Alert,
    Asset,
    Drill,
    Location,
    SafetyIncident,
    VisitorLog,
    WorkOrder,
    WorkOrderComment,
)

User = get_user_model()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _school(name: str = "Crown Academy") -> School:
    return School.objects.create(name=name)


def _user(username: str, is_staff: bool = False):
    return User.objects.create_user(
        username=username,
        password="testpass",
        is_staff=is_staff,
    )


def _client(user, school: School, role: str = "admin") -> APIClient:
    c = APIClient()
    c.force_authenticate(user=user)
    c.credentials(
        HTTP_X_SCHOOL_ID=str(school.id),
        HTTP_X_ROLE=role,
    )
    return c


def _anon_client(school: School) -> APIClient:
    c = APIClient()
    c.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return c


def _loc(school: School, name: str = "Main Hall") -> Location:
    return Location.objects.create(school=school, name=name, kind="building")


def _asset(school: School, location: Location | None = None, name: str = "Boiler") -> Asset:
    return Asset.objects.create(school=school, name=name, category="HVAC", location=location)


def _work_order(school: School, user, location: Location | None = None) -> WorkOrder:
    return WorkOrder.objects.create(
        school=school,
        title="Fix leak",
        status=WorkOrder.STATUS_NEW,
        priority=WorkOrder.PRIORITY_NORMAL,
        requested_by=user,
    )


# ---------------------------------------------------------------------------
# Location tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLocations:
    URL = "/api/facilities/locations/"

    def test_list_authenticated(self):
        s = _school()
        u = _user("locuser", is_staff=True)
        c = _client(u, s)
        _loc(s, "Room A")
        resp = c.get(self.URL)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_list_unauthenticated_denied(self):
        s = _school("Anon School")
        c = _anon_client(s)
        resp = c.get(self.URL)
        assert resp.status_code in (401, 403)

    def test_create_as_staff(self):
        s = _school("Loc School")
        u = _user("locstaff", is_staff=True)
        c = _client(u, s)
        resp = c.post(self.URL, {"name": "Room 101", "kind": "room"}, format="json")
        assert resp.status_code == 201
        assert resp.json()["name"] == "Room 101"

    def test_create_denied_for_readonly_role(self):
        s = _school("RO School")
        u = _user("roreader", is_staff=False)
        c = _client(u, s, role="teacher")
        resp = c.post(self.URL, {"name": "Hidden Room", "kind": "room"}, format="json")
        assert resp.status_code == 403

    def test_cross_tenant_isolation(self):
        s1 = _school("School A")
        s2 = _school("School B")
        u1 = _user("user_a", is_staff=True)
        u2 = _user("user_b", is_staff=True)
        _loc(s1, "A Room")
        _loc(s2, "B Room")
        c1 = _client(u1, s1)
        resp = c1.get(self.URL)
        names = [r["name"] for r in resp.json()]
        assert "A Room" in names
        assert "B Room" not in names

    def test_patch_location(self):
        s = _school("Patch School")
        u = _user("patcher", is_staff=True)
        loc = _loc(s, "Old Name")
        c = _client(u, s)
        resp = c.patch(f"{self.URL}{loc.id}/", {"name": "New Name"}, format="json")
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_delete_location(self):
        s = _school("Del School")
        u = _user("deleter_loc", is_staff=True)
        loc = _loc(s, "Temp Room")
        c = _client(u, s)
        resp = c.delete(f"{self.URL}{loc.id}/")
        assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Asset tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAssets:
    URL = "/api/facilities/assets/"

    def test_list_authenticated(self):
        s = _school("Asset School")
        u = _user("assetuser", is_staff=True)
        _asset(s, name="HVAC Unit")
        c = _client(u, s)
        resp = c.get(self.URL)
        assert resp.status_code == 200
        assert any(a["name"] == "HVAC Unit" for a in resp.json())

    def test_create_asset(self):
        s = _school("Asset Create")
        u = _user("assetcreator", is_staff=True)
        c = _client(u, s)
        resp = c.post(self.URL, {"name": "Projector", "category": "AV"}, format="json")
        assert resp.status_code == 201

    def test_asset_cross_tenant(self):
        s1 = _school("Asset Tenant 1")
        s2 = _school("Asset Tenant 2")
        u1 = _user("at1", is_staff=True)
        _asset(s1, name="Asset S1")
        _asset(s2, name="Asset S2")
        c = _client(u1, s1)
        names = [a["name"] for a in c.get(self.URL).json()]
        assert "Asset S1" in names
        assert "Asset S2" not in names


# ---------------------------------------------------------------------------
# Work Order tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestWorkOrders:
    URL = "/api/facilities/work-orders/"

    def test_list(self):
        s = _school("WO School")
        u = _user("wouser", is_staff=True)
        _work_order(s, u)
        c = _client(u, s)
        resp = c.get(self.URL)
        assert resp.status_code == 200

    def test_create_by_any_authenticated(self):
        s = _school("WO Create")
        u = _user("teacher1", is_staff=False)
        c = _client(u, s, role="teacher")
        resp = c.post(self.URL, {"title": "Broken door", "priority": "NORMAL"}, format="json")
        assert resp.status_code == 201

    def test_filter_by_status(self):
        s = _school("WO Filter")
        u = _user("wofilter", is_staff=True)
        WorkOrder.objects.create(school=s, title="Open WO", status="NEW", priority="NORMAL", requested_by=u)
        WorkOrder.objects.create(school=s, title="Done WO", status="DONE", priority="LOW", requested_by=u)
        c = _client(u, s)
        resp = c.get(self.URL + "?status=NEW")
        titles = [r["title"] for r in resp.json()]
        assert "Open WO" in titles
        assert "Done WO" not in titles

    def test_transition_action(self):
        s = _school("WO Transition")
        u = _user("wotrans", is_staff=True)
        wo = _work_order(s, u)
        c = _client(u, s)
        resp = c.post(f"{self.URL}{wo.id}/transition/", {"status": "IN_PROGRESS"}, format="json")
        assert resp.status_code == 200
        assert resp.json()["status"] == "IN_PROGRESS"

    def test_transition_to_done_sets_closed_at(self):
        s = _school("WO Done")
        u = _user("wodone", is_staff=True)
        wo = _work_order(s, u)
        c = _client(u, s)
        resp = c.post(f"{self.URL}{wo.id}/transition/", {"status": "DONE"}, format="json")
        assert resp.status_code == 200
        assert resp.json()["closed_at"] is not None

    def test_transition_invalid_status(self):
        s = _school("WO Bad Trans")
        u = _user("wobad", is_staff=True)
        wo = _work_order(s, u)
        c = _client(u, s)
        resp = c.post(f"{self.URL}{wo.id}/transition/", {"status": "NONEXISTENT"}, format="json")
        assert resp.status_code == 400

    def test_cross_tenant_work_orders(self):
        s1 = _school("WO Tenant 1")
        s2 = _school("WO Tenant 2")
        u1 = _user("wot1", is_staff=True)
        u2 = _user("wot2", is_staff=True)
        WorkOrder.objects.create(school=s1, title="WO T1", status="NEW", priority="NORMAL", requested_by=u1)
        WorkOrder.objects.create(school=s2, title="WO T2", status="NEW", priority="NORMAL", requested_by=u2)
        c = _client(u1, s1)
        titles = [r["title"] for r in c.get(self.URL).json()]
        assert "WO T1" in titles
        assert "WO T2" not in titles

    def test_unauthenticated_cannot_list(self):
        s = _school("WO Anon")
        c = _anon_client(s)
        resp = c.get(self.URL)
        assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Safety Incident tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSafetyIncidents:
    URL = "/api/security/incidents/"

    def test_list(self):
        s = _school("Incident School")
        u = _user("inciuser", is_staff=True)
        SafetyIncident.objects.create(school=s, title="Broken glass", severity="LOW")
        c = _client(u, s, role="safety_officer")
        resp = c.get(self.URL)
        assert resp.status_code == 200

    def test_create(self):
        s = _school("Incident Create")
        u = _user("inci_creator", is_staff=True)
        c = _client(u, s, role="safety_officer")
        resp = c.post(self.URL, {"title": "Slip hazard", "severity": "MEDIUM"}, format="json")
        assert resp.status_code == 201

    def test_readonly_cannot_create(self):
        s = _school("Incident RO")
        u = _user("inci_ro", is_staff=False)
        c = _client(u, s, role="teacher")
        resp = c.post(self.URL, {"title": "Should fail", "severity": "LOW"}, format="json")
        assert resp.status_code == 403

    def test_cross_tenant(self):
        s1 = _school("Inci T1")
        s2 = _school("Inci T2")
        u1 = _user("inci_t1", is_staff=True)
        u2 = _user("inci_t2", is_staff=True)
        SafetyIncident.objects.create(school=s1, title="Inc S1", severity="LOW")
        SafetyIncident.objects.create(school=s2, title="Inc S2", severity="LOW")
        c = _client(u1, s1, role="safety_officer")
        titles = [r["title"] for r in c.get(self.URL).json()]
        assert "Inc S1" in titles
        assert "Inc S2" not in titles


# ---------------------------------------------------------------------------
# Drill tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDrills:
    URL = "/api/security/drills/"

    def test_list(self):
        s = _school("Drill School")
        u = _user("drilluser", is_staff=True)
        from datetime import date
        Drill.objects.create(school=s, drill_type="FIRE", planned_for=timezone.now())
        c = _client(u, s, role="safety_officer")
        resp = c.get(self.URL)
        assert resp.status_code == 200

    def test_create(self):
        s = _school("Drill Create")
        u = _user("drill_creator", is_staff=True)
        c = _client(u, s, role="safety_officer")
        resp = c.post(self.URL, {"drill_type": "LOCKDOWN", "planned_for": "2026-06-01"}, format="json")
        assert resp.status_code == 201

    def test_readonly_cannot_create(self):
        s = _school("Drill RO")
        u = _user("drill_ro", is_staff=False)
        c = _client(u, s, role="teacher")
        resp = c.post(self.URL, {"drill_type": "FIRE", "planned_for": "2026-07-01"}, format="json")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Visitor Log tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestVisitorLogs:
    URL = "/api/security/visitor-logs/"

    def test_list(self):
        s = _school("Visitor School")
        u = _user("visuser", is_staff=True)
        VisitorLog.objects.create(school=s, name="John Doe", purpose="Meeting")
        c = _client(u, s, role="safety_officer")
        resp = c.get(self.URL)
        assert resp.status_code == 200
        assert any(r["name"] == "John Doe" for r in resp.json())

    def test_create(self):
        s = _school("Visitor Create")
        u = _user("viscreator", is_staff=True)
        c = _client(u, s, role="safety_officer")
        resp = c.post(self.URL, {"name": "Jane Smith", "purpose": "Pickup"}, format="json")
        assert resp.status_code == 201

    def test_cross_tenant(self):
        s1 = _school("Vis T1")
        s2 = _school("Vis T2")
        u1 = _user("vis_t1", is_staff=True)
        u2 = _user("vis_t2", is_staff=True)
        VisitorLog.objects.create(school=s1, name="Vis S1", purpose="x")
        VisitorLog.objects.create(school=s2, name="Vis S2", purpose="x")
        c = _client(u1, s1, role="safety_officer")
        names = [r["name"] for r in c.get(self.URL).json()]
        assert "Vis S1" in names
        assert "Vis S2" not in names


# ---------------------------------------------------------------------------
# Alert tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAlerts:
    URL = "/api/security/alerts/"

    def test_list(self):
        s = _school("Alert School")
        u = _user("alertuser", is_staff=True)
        Alert.objects.create(school=s, title="Test Alert", channel="TEAMS")
        c = _client(u, s, role="safety_officer")
        resp = c.get(self.URL)
        assert resp.status_code == 200

    def test_emit_action(self):
        s = _school("Alert Emit")
        u = _user("emitter", is_staff=True)
        c = _client(u, s, role="safety_officer")
        resp = c.post(
            f"{self.URL}emit/",
            {"title": "Lockdown Alert", "body": "Shelter in place", "channel": "SMS"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Lockdown Alert"

    def test_emit_requires_title(self):
        s = _school("Alert No Title")
        u = _user("emitter_bad", is_staff=True)
        c = _client(u, s, role="safety_officer")
        resp = c.post(f"{self.URL}emit/", {"body": "No title"}, format="json")
        assert resp.status_code == 400

    def test_readonly_cannot_emit(self):
        s = _school("Alert RO")
        u = _user("emit_ro", is_staff=False)
        c = _client(u, s, role="teacher")
        resp = c.post(f"{self.URL}emit/", {"title": "Denied", "channel": "TEAMS"}, format="json")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Summary endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFacilitiesSummary:
    URL = "/api/facilities/summary/"

    def test_returns_counts(self):
        s = _school("Summary School")
        u = _user("summaryuser", is_staff=True)
        WorkOrder.objects.create(school=s, title="WO1", status="NEW", priority="NORMAL", requested_by=u)
        WorkOrder.objects.create(school=s, title="WO2", status="DONE", priority="LOW", requested_by=u)
        c = _client(u, s)
        resp = c.get(self.URL)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_open_work_orders" in data
        assert data["total_open_work_orders"] == 1


@pytest.mark.django_db
class TestSecuritySummary:
    URL = "/api/security/summary/"

    def test_returns_counts(self):
        from datetime import date
        s = _school("Sec Summary School")
        u = _user("sec_summary", is_staff=True)
        SafetyIncident.objects.create(school=s, title="Inc", severity="LOW")
        Drill.objects.create(school=s, drill_type="FIRE", planned_for=date.today())
        VisitorLog.objects.create(school=s, name="Visitor", purpose="Visit")
        c = _client(u, s, role="safety_officer")
        resp = c.get(self.URL)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_incidents" in data
        assert data["total_incidents"] == 1
        assert data["drills_total"] == 1

    def test_unauthenticated_denied(self):
        s = _school("Sec Anon")
        c = _anon_client(s)
        resp = c.get(self.URL)
        assert resp.status_code in (401, 403)
