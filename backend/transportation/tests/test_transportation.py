# backend/transportation/tests/test_transportation.py
"""
Phase 14.0 – Transportation module test suite.

Coverage:
  - URL routing (vehicles, drivers, routes, stops, riders, assignments, events, dispatch)
  - Permission enforcement (unauthenticated, read-only role, transport director/admin)
  - Soft-delete on Vehicle and Driver
  - CRUD for every resource type
  - Cross-tenant isolation
  - Route stops custom action
  - Student rider filters (school_year, route_id)
  - RideEvent date filter
  - Dispatch run-sheet: success, missing params, route not found
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School
from transportation.models import (
    Assignment,
    Driver,
    RideEvent,
    Route,
    Stop,
    StudentRider,
    Vehicle,
)

User = get_user_model()

# ---------------------------------------------------------------------------
# Helpers / factories
# ---------------------------------------------------------------------------

def _school(name: str = "Crown Academy") -> School:
    return School.objects.create(name=name)


def _user(username: str, is_staff: bool = False) -> User:
    return User.objects.create_user(username=username, password="testpass", is_staff=is_staff)


def _client(user, school: School, role: str = "transportation_director") -> APIClient:
    c = APIClient()
    c.force_authenticate(user=user)
    c.credentials(HTTP_X_SCHOOL_ID=str(school.id), HTTP_X_ROLE=role)
    return c


def _anon_client(school: School) -> APIClient:
    c = APIClient()
    c.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return c


def _vehicle(school: School, name: str = "Bus 1", vtype: str = "BUS") -> Vehicle:
    return Vehicle.objects.create(school=school, name=name, vehicle_type=vtype, capacity=40)


def _driver(school: School, full_name: str = "Jane Driver") -> Driver:
    return Driver.objects.create(school=school, full_name=full_name)


def _route(school: School, name: str = "Route A", direction: str = "AM") -> Route:
    return Route.objects.create(school=school, name=name, direction=direction)


def _stop(school: School, route: Route, label: str = "Stop 1", order: int = 1) -> Stop:
    return Stop.objects.create(school=school, route=route, label=label, order=order)


def _rider(school: School, stop: Stop | None = None, year: str = "2025-2026") -> StudentRider:
    return StudentRider.objects.create(
        school=school,
        student_id=uuid.uuid4(),
        school_year=year,
        pickup_stop=stop,
    )


# ---------------------------------------------------------------------------
# Vehicle tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestVehicles:
    URL = "/api/transportation/vehicles/"

    def test_list_returns_200(self):
        s = _school()
        u = _user("vl_user", is_staff=True)
        _vehicle(s, "Bus A")
        resp = _client(u, s).get(self.URL)
        assert resp.status_code == 200
        assert any(v["name"] == "Bus A" for v in resp.json())

    def test_create_as_transport_director(self):
        s = _school("Veh Create")
        u = _user("veh_creator", is_staff=True)
        resp = _client(u, s).post(self.URL, {"name": "Van 1", "vehicle_type": "VAN", "capacity": 12}, format="json")
        assert resp.status_code == 201
        assert resp.json()["name"] == "Van 1"

    def test_create_denied_for_readonly_role(self):
        s = _school("Veh RO")
        u = _user("veh_ro", is_staff=False)
        resp = _client(u, s, role="teacher").post(self.URL, {"name": "X", "vehicle_type": "BUS"}, format="json")
        assert resp.status_code == 403

    def test_soft_delete(self):
        s = _school("Veh Del")
        u = _user("veh_del", is_staff=True)
        v = _vehicle(s, "Soft Bus")
        resp = _client(u, s).delete(f"{self.URL}{v.id}/")
        assert resp.status_code == 204
        v.refresh_from_db()
        assert v.is_deleted is True
        # Should not appear in list
        resp2 = _client(u, s).get(self.URL)
        names = [x["name"] for x in resp2.json()]
        assert "Soft Bus" not in names

    def test_patch_vehicle(self):
        s = _school("Veh Patch")
        u = _user("veh_patch", is_staff=True)
        v = _vehicle(s, "Old Bus")
        resp = _client(u, s).patch(f"{self.URL}{v.id}/", {"name": "New Bus"}, format="json")
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Bus"

    def test_cross_tenant_isolation(self):
        s1 = _school("Veh T1")
        s2 = _school("Veh T2")
        u1 = _user("vt1", is_staff=True)
        _vehicle(s1, "T1 Bus")
        _vehicle(s2, "T2 Bus")
        names = [v["name"] for v in _client(u1, s1).get(self.URL).json()]
        assert "T1 Bus" in names
        assert "T2 Bus" not in names

    def test_unauthenticated_denied(self):
        s = _school("Veh Anon")
        resp = _anon_client(s).get(self.URL)
        assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Driver tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDrivers:
    URL = "/api/transportation/drivers/"

    def test_list(self):
        s = _school("Driver School")
        u = _user("dr_list", is_staff=True)
        _driver(s, "John Driver")
        resp = _client(u, s).get(self.URL)
        assert resp.status_code == 200
        assert any(d["full_name"] == "John Driver" for d in resp.json())

    def test_create(self):
        s = _school("Driver Create")
        u = _user("dr_create", is_staff=True)
        resp = _client(u, s).post(self.URL, {"full_name": "Mary Wheels", "is_contractor": True}, format="json")
        assert resp.status_code == 201
        assert resp.json()["full_name"] == "Mary Wheels"

    def test_soft_delete(self):
        s = _school("Driver Del")
        u = _user("dr_del", is_staff=True)
        d = _driver(s, "Temp Driver")
        _client(u, s).delete(f"{self.URL}{d.id}/")
        d.refresh_from_db()
        assert d.is_deleted is True

    def test_cross_tenant(self):
        s1 = _school("Dr T1")
        s2 = _school("Dr T2")
        u1 = _user("drt1", is_staff=True)
        _driver(s1, "T1 Driver")
        _driver(s2, "T2 Driver")
        names = [d["full_name"] for d in _client(u1, s1).get(self.URL).json()]
        assert "T1 Driver" in names
        assert "T2 Driver" not in names

    def test_readonly_role_can_list(self):
        s = _school("Dr RO List")
        u = _user("dr_ro_list", is_staff=False)
        _driver(s, "Visible Driver")
        resp = _client(u, s, role="teacher").get(self.URL)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRoutes:
    URL = "/api/transportation/routes/"

    def test_list(self):
        s = _school("Route School")
        u = _user("rt_list", is_staff=True)
        _route(s, "East AM")
        resp = _client(u, s).get(self.URL)
        assert resp.status_code == 200
        assert any(r["name"] == "East AM" for r in resp.json())

    def test_create(self):
        s = _school("Route Create")
        u = _user("rt_create", is_staff=True)
        resp = _client(u, s).post(self.URL, {"name": "West PM", "direction": "PM"}, format="json")
        assert resp.status_code == 201
        assert resp.json()["direction"] == "PM"

    def test_stops_action(self):
        s = _school("Route Stops")
        u = _user("rt_stops", is_staff=True)
        r = _route(s, "Stops Route")
        _stop(s, r, "First Stop", order=1)
        _stop(s, r, "Second Stop", order=2)
        resp = _client(u, s).get(f"{self.URL}{r.id}/stops/")
        assert resp.status_code == 200
        labels = [st["label"] for st in resp.json()]
        assert "First Stop" in labels
        assert "Second Stop" in labels
        # Ensure order
        assert resp.json()[0]["order"] <= resp.json()[1]["order"]

    def test_stops_action_cross_tenant_denied(self):
        s1 = _school("RT stops T1")
        s2 = _school("RT stops T2")
        u2 = _user("rt_st_t2", is_staff=True)
        r1 = _route(s1, "S1 Route")
        resp = _client(u2, s2).get(f"{self.URL}{r1.id}/stops/")
        assert resp.status_code == 404

    def test_cross_tenant(self):
        s1 = _school("Rt T1")
        s2 = _school("Rt T2")
        u1 = _user("rtt1", is_staff=True)
        _route(s1, "S1 Route")
        _route(s2, "S2 Route")
        names = [r["name"] for r in _client(u1, s1).get(self.URL).json()]
        assert "S1 Route" in names
        assert "S2 Route" not in names


# ---------------------------------------------------------------------------
# Stop tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestStops:
    URL = "/api/transportation/stops/"

    def test_list(self):
        s = _school("Stop School")
        u = _user("st_list", is_staff=True)
        r = _route(s)
        _stop(s, r, "Elm & 1st")
        resp = _client(u, s).get(self.URL)
        assert resp.status_code == 200
        assert any(st["label"] == "Elm & 1st" for st in resp.json())

    def test_create(self):
        s = _school("Stop Create")
        u = _user("st_create", is_staff=True)
        r = _route(s)
        resp = _client(u, s).post(
            self.URL,
            {"route": r.id, "label": "Oak & 2nd", "order": 1},
            format="json",
        )
        assert resp.status_code == 201

    def test_cross_tenant(self):
        s1 = _school("St T1")
        s2 = _school("St T2")
        u1 = _user("stt1", is_staff=True)
        r1 = _route(s1, "R1")
        r2 = _route(s2, "R2")
        _stop(s1, r1, "T1 Stop")
        _stop(s2, r2, "T2 Stop")
        labels = [st["label"] for st in _client(u1, s1).get(self.URL).json()]
        assert "T1 Stop" in labels
        assert "T2 Stop" not in labels


# ---------------------------------------------------------------------------
# StudentRider tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestStudentRiders:
    URL = "/api/transportation/riders/"

    def test_list(self):
        s = _school("Rider School")
        u = _user("rid_list", is_staff=True)
        _rider(s, year="2025-2026")
        resp = _client(u, s).get(self.URL)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_create(self):
        s = _school("Rider Create")
        u = _user("rid_create", is_staff=True)
        sid = str(uuid.uuid4())
        resp = _client(u, s).post(
            self.URL,
            {"student_id": sid, "school_year": "2025-2026"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["student_id"] == sid

    def test_filter_by_school_year(self):
        s = _school("Rider Year")
        u = _user("rid_year", is_staff=True)
        _rider(s, year="2025-2026")
        _rider(s, year="2024-2025")
        resp = _client(u, s).get(self.URL + "?school_year=2025-2026")
        assert resp.status_code == 200
        years = {r["school_year"] for r in resp.json()}
        assert years == {"2025-2026"}

    def test_cross_tenant(self):
        s1 = _school("Rid T1")
        s2 = _school("Rid T2")
        u1 = _user("ridt1", is_staff=True)
        r1 = StudentRider.objects.create(school=s1, student_id=uuid.uuid4(), school_year="2025-2026")
        r2 = StudentRider.objects.create(school=s2, student_id=uuid.uuid4(), school_year="2025-2026")
        ids = [str(r["student_id"]) for r in _client(u1, s1).get(self.URL).json()]
        assert str(r1.student_id) in ids
        assert str(r2.student_id) not in ids


# ---------------------------------------------------------------------------
# Assignment tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAssignments:
    URL = "/api/transportation/assignments/"

    def test_list(self):
        s = _school("Assign School")
        u = _user("asgn_list", is_staff=True)
        r = _route(s)
        Assignment.objects.create(school=s, route=r, start_date=date.today())
        resp = _client(u, s).get(self.URL)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_create(self):
        s = _school("Assign Create")
        u = _user("asgn_create", is_staff=True)
        r = _route(s)
        d = _driver(s)
        v = _vehicle(s)
        resp = _client(u, s).post(
            self.URL,
            {
                "route": r.id,
                "driver": d.id,
                "vehicle": v.id,
                "start_date": str(date.today()),
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_cross_tenant(self):
        s1 = _school("Asgn T1")
        s2 = _school("Asgn T2")
        u1 = _user("asgt1", is_staff=True)
        r1 = _route(s1)
        r2 = _route(s2)
        Assignment.objects.create(school=s1, route=r1, start_date=date.today())
        Assignment.objects.create(school=s2, route=r2, start_date=date.today())
        resp = _client(u1, s1).get(self.URL)
        route_ids = {str(a["route"]) for a in resp.json()}
        assert str(r1.id) in route_ids
        assert str(r2.id) not in route_ids


# ---------------------------------------------------------------------------
# RideEvent tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRideEvents:
    URL = "/api/transportation/events/"

    def test_list(self):
        s = _school("Event School")
        u = _user("ev_list", is_staff=True)
        r = _route(s)
        RideEvent.objects.create(school=s, route=r, service_date=date.today(), student_id=uuid.uuid4(), event_type="BOARDED")
        resp = _client(u, s).get(self.URL)
        assert resp.status_code == 200

    def test_create(self):
        s = _school("Event Create")
        u = _user("ev_create", is_staff=True)
        r = _route(s)
        resp = _client(u, s).post(
            self.URL,
            {
                "route": r.id,
                "service_date": str(date.today()),
                "student_id": str(uuid.uuid4()),
                "event_type": "NO_SHOW",
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_filter_by_date(self):
        s = _school("Event Date")
        u = _user("ev_date", is_staff=True)
        r = _route(s)
        today = date.today()
        yesterday = today - timedelta(days=1)
        RideEvent.objects.create(school=s, route=r, service_date=today, student_id=uuid.uuid4(), event_type="BOARDED")
        RideEvent.objects.create(school=s, route=r, service_date=yesterday, student_id=uuid.uuid4(), event_type="LATE")
        resp = _client(u, s).get(self.URL + f"?date={today.isoformat()}")
        dates = {e["service_date"] for e in resp.json()}
        assert all(d == today.isoformat() for d in dates)

    def test_cross_tenant(self):
        s1 = _school("Ev T1")
        s2 = _school("Ev T2")
        u1 = _user("evt1", is_staff=True)
        r1 = _route(s1)
        r2 = _route(s2)
        RideEvent.objects.create(school=s1, route=r1, service_date=date.today(), student_id=uuid.uuid4(), event_type="BOARDED")
        RideEvent.objects.create(school=s2, route=r2, service_date=date.today(), student_id=uuid.uuid4(), event_type="BOARDED")
        route_ids = {str(e["route"]) for e in _client(u1, s1).get(self.URL).json()}
        assert str(r1.id) in route_ids
        assert str(r2.id) not in route_ids


# ---------------------------------------------------------------------------
# Dispatch run-sheet tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDispatchRunSheet:
    URL = "/api/transportation/dispatch/run-sheet/"

    def test_run_sheet_success(self):
        s = _school("Dispatch School")
        u = _user("disp_user", is_staff=True)
        r = _route(s, "AM Route", direction="AM")
        st1 = _stop(s, r, "First Stop", order=1)
        st2 = _stop(s, r, "Second Stop", order=2)
        _rider(s, stop=st1, year="2025-2026")
        _rider(s, stop=st2, year="2025-2026")
        resp = _client(u, s).get(self.URL + f"?date={date.today().isoformat()}&route_id={r.id}&school_year=2025-2026")
        assert resp.status_code == 200
        data = resp.json()
        assert data["route"]["id"] == str(r.id)
        assert len(data["stops"]) == 2
        assert len(data["riders"]) == 2

    def test_run_sheet_missing_params(self):
        s = _school("Dispatch Missing")
        u = _user("disp_miss", is_staff=True)
        resp = _client(u, s).get(self.URL)
        assert resp.status_code == 400
        assert "date" in resp.json().get("detail", "")

    def test_run_sheet_route_not_found(self):
        s = _school("Dispatch 404")
        u = _user("disp_404", is_staff=True)
        fake_id = 99999999
        resp = _client(u, s).get(self.URL + f"?date={date.today().isoformat()}&route_id={fake_id}")
        assert resp.status_code == 404

    def test_run_sheet_cross_tenant(self):
        s1 = _school("Disp T1")
        s2 = _school("Disp T2")
        u2 = _user("disp_t2", is_staff=True)
        r1 = _route(s1, "S1 Route")
        resp = _client(u2, s2).get(self.URL + f"?date={date.today().isoformat()}&route_id={r1.id}")
        assert resp.status_code == 404

    def test_run_sheet_pm_uses_dropoff(self):
        s = _school("Dispatch PM")
        u = _user("disp_pm", is_staff=True)
        r = _route(s, "PM Route", direction="PM")
        st = _stop(s, r, "PM Stop", order=1)
        # PM rider: has dropoff stop, not pickup
        StudentRider.objects.create(
            school=s,
            student_id=uuid.uuid4(),
            school_year="2025-2026",
            dropoff_stop=st,
        )
        resp = _client(u, s).get(self.URL + f"?date={date.today().isoformat()}&route_id={r.id}&school_year=2025-2026")
        assert resp.status_code == 200
        assert len(resp.json()["riders"]) == 1

    def test_run_sheet_unauthenticated_denied(self):
        s = _school("Disp Anon")
        resp = _anon_client(s).get(self.URL + "?date=2026-01-01&route_id=1")
        assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Permission edge cases
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPermissions:
    def test_non_transport_role_cannot_create_vehicle(self):
        s = _school("Perm School")
        u = _user("perm_user", is_staff=False)
        c = _client(u, s, role="counselor")
        resp = c.post("/api/transportation/vehicles/", {"name": "X", "vehicle_type": "BUS"}, format="json")
        assert resp.status_code == 403

    def test_admin_role_can_create_vehicle(self):
        s = _school("Admin Perm")
        u = _user("admin_perm", is_staff=False)
        resp = _client(u, s, role="admin").post(
            "/api/transportation/vehicles/",
            {"name": "Admin Bus", "vehicle_type": "BUS", "capacity": 20},
            format="json",
        )
        assert resp.status_code == 201

    def test_ops_role_can_create_driver(self):
        s = _school("Ops Perm")
        u = _user("ops_perm", is_staff=False)
        resp = _client(u, s, role="ops").post(
            "/api/transportation/drivers/",
            {"full_name": "Ops Driver"},
            format="json",
        )
        assert resp.status_code == 201

    def test_teacher_can_read_routes(self):
        s = _school("Teacher Read")
        u = _user("teacher_r", is_staff=False)
        resp = _client(u, s, role="teacher").get("/api/transportation/routes/")
        assert resp.status_code == 200
