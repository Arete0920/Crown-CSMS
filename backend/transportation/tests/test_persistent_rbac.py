from __future__ import annotations

import uuid

import pytest
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole


pytestmark = pytest.mark.django_db
URL = "/api/transportation/vehicles/"


def _school(name: str) -> School:
    return School.objects.create(name=name)


def _user(school: School, *, is_staff: bool = False) -> UserAccount:
    return UserAccount.objects.create_user(
        username=f"transport-rbac-{uuid.uuid4()}",
        password="testpass",
        school=school,
        is_staff=is_staff,
    )


def _client(user: UserAccount, school: School, *, spoofed_role: str | None = None) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    headers = {"HTTP_X_SCHOOL_ID": str(school.id)}
    if spoofed_role:
        headers["HTTP_X_ROLE"] = spoofed_role
    client.credentials(**headers)
    return client


def _grant(user: UserAccount, school: School, code: str = "transportation.view") -> None:
    permission, _ = CrownPermission.objects.get_or_create(
        code=code,
        defaults={
            "description": (
                "Create or modify transportation operational records"
                if code == "transportation.edit"
                else "View transportation dashboard"
            )
        },
    )
    role_code = "transportation_security_test"
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)
    UserRole.objects.get_or_create(user=user, school=school, role_code=role_code)


def test_spoofed_transportation_role_cannot_read_without_persistent_permission():
    school = _school("Transport spoof read")
    user = _user(school)
    response = _client(user, school, spoofed_role="transportation_director").get(URL)
    assert response.status_code == 403


def test_spoofed_admin_role_cannot_write_without_persistent_permission():
    school = _school("Transport spoof write")
    user = _user(school)
    response = _client(user, school, spoofed_role="admin").post(
        URL,
        {"name": "Spoofed Bus", "vehicle_type": "BUS", "capacity": 20},
        format="json",
    )
    assert response.status_code == 403


def test_django_staff_flag_cannot_bypass_transportation_permission():
    school = _school("Transport staff bypass")
    user = _user(school, is_staff=True)
    response = _client(user, school).get(URL)
    assert response.status_code == 403


def test_persistent_same_school_view_permission_allows_read():
    school = _school("Transport authorized")
    user = _user(school)
    _grant(user, school)
    response = _client(user, school).get(URL)
    assert response.status_code == 200


def test_view_permission_does_not_allow_mutation():
    school = _school("Transport view only")
    user = _user(school)
    _grant(user, school, "transportation.view")
    response = _client(user, school).post(
        URL,
        {"name": "Denied Bus", "vehicle_type": "BUS", "capacity": 20},
        format="json",
    )
    assert response.status_code == 403


def test_edit_permission_allows_mutation():
    school = _school("Transport editor")
    user = _user(school)
    _grant(user, school, "transportation.view")
    _grant(user, school, "transportation.edit")
    response = _client(user, school).post(
        URL,
        {"name": "Authorized Bus", "vehicle_type": "BUS", "capacity": 20},
        format="json",
    )
    assert response.status_code == 201


def test_permission_in_other_school_does_not_authorize_target_tenant():
    school_a = _school("Transport school A")
    school_b = _school("Transport school B")
    user = _user(school_a)
    _grant(user, school_a)
    _grant(user, school_a, "transportation.edit")
    response = _client(user, school_b, spoofed_role="transportation_director").get(URL)
    assert response.status_code == 403
