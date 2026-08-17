from __future__ import annotations

import uuid
from datetime import date

import pytest
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from transportation.models import Driver, Route, Stop, Vehicle


pytestmark = pytest.mark.django_db


def _school(name: str) -> School:
    return School.objects.create(name=name)


def _authorized_client(school: School) -> APIClient:
    user = UserAccount.objects.create_user(
        username=f"transport-integrity-{uuid.uuid4()}",
        password="testpass",
        school=school,
    )
    role_code = "transportation_integrity_test"
    for code, description in (
        ("transportation.view", "View transportation dashboard"),
        ("transportation.edit", "Create or modify transportation operational records"),
    ):
        permission, _ = CrownPermission.objects.get_or_create(
            code=code, defaults={"description": description}
        )
        RolePermission.objects.get_or_create(role_code=role_code, permission=permission)
    UserRole.objects.get_or_create(user=user, school=school, role_code=role_code)
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return client


def test_route_rejects_foreign_default_vehicle_and_driver():
    school_a = _school("Transport relation A")
    school_b = _school("Transport relation B")
    vehicle_b = Vehicle.objects.create(school=school_b, name="Foreign Bus", vehicle_type="BUS")
    driver_b = Driver.objects.create(school=school_b, full_name="Foreign Driver")
    response = _authorized_client(school_a).post(
        "/api/transportation/routes/",
        {
            "name": "Unsafe Route",
            "direction": "AM",
            "default_vehicle": str(vehicle_b.id),
            "default_driver": str(driver_b.id),
        },
        format="json",
    )
    assert response.status_code == 400


def test_assignment_rejects_foreign_route_driver_and_vehicle():
    school_a = _school("Transport assignment A")
    school_b = _school("Transport assignment B")
    route_b = Route.objects.create(school=school_b, name="Foreign Route", direction="AM")
    driver_b = Driver.objects.create(school=school_b, full_name="Foreign Driver")
    vehicle_b = Vehicle.objects.create(school=school_b, name="Foreign Bus", vehicle_type="BUS")
    response = _authorized_client(school_a).post(
        "/api/transportation/assignments/",
        {
            "route": str(route_b.id),
            "driver": str(driver_b.id),
            "vehicle": str(vehicle_b.id),
            "start_date": str(date.today()),
        },
        format="json",
    )
    assert response.status_code == 400


def test_rider_rejects_foreign_stop():
    school_a = _school("Transport rider A")
    school_b = _school("Transport rider B")
    route_b = Route.objects.create(school=school_b, name="Foreign Route", direction="AM")
    stop_b = Stop.objects.create(school=school_b, route=route_b, order=1, label="Foreign Stop")
    response = _authorized_client(school_a).post(
        "/api/transportation/riders/",
        {
            "student_id": str(uuid.uuid4()),
            "school_year": "2026-2027",
            "pickup_stop": str(stop_b.id),
        },
        format="json",
    )
    assert response.status_code == 400


def test_ride_event_rejects_foreign_route():
    school_a = _school("Transport event A")
    school_b = _school("Transport event B")
    route_b = Route.objects.create(school=school_b, name="Foreign Route", direction="AM")
    response = _authorized_client(school_a).post(
        "/api/transportation/events/",
        {
            "route": str(route_b.id),
            "service_date": str(date.today()),
            "student_id": str(uuid.uuid4()),
            "event_type": "BOARDED",
        },
        format="json",
    )
    assert response.status_code == 400
