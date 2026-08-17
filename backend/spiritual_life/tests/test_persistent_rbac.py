from __future__ import annotations

import uuid

import pytest
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole


pytestmark = pytest.mark.django_db
URL = "/api/spiritual-life/chapel-events/"


def _school(name: str) -> School:
    return School.objects.create(name=name)


def _user(school: School, *, is_staff: bool = False) -> UserAccount:
    return UserAccount.objects.create_user(
        username=f"spiritual-rbac-{uuid.uuid4()}",
        password="testpass",
        school=school,
        is_staff=is_staff,
    )


def _client(user: UserAccount, school: School) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return client


def _grant(user: UserAccount, school: School) -> None:
    permission, _ = CrownPermission.objects.get_or_create(
        code="spiritual_life.view",
        defaults={"description": "View spiritual-life dashboard"},
    )
    role_code = "spiritual_life_security_test"
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)
    UserRole.objects.get_or_create(user=user, school=school, role_code=role_code)


def test_authenticated_same_tenant_user_without_permission_is_denied():
    school = _school("Spiritual denied")
    user = _user(school)
    response = _client(user, school).get(URL)
    assert response.status_code == 403


def test_django_staff_flag_does_not_grant_spiritual_life_authority():
    school = _school("Spiritual staff bypass")
    user = _user(school, is_staff=True)
    response = _client(user, school).get(URL)
    assert response.status_code == 403


def test_persistent_same_school_permission_allows_spiritual_life_access():
    school = _school("Spiritual authorized")
    user = _user(school)
    _grant(user, school)
    response = _client(user, school).get(URL)
    assert response.status_code == 200


def test_cross_tenant_attempt_is_concealed_without_target_school_grant():
    school_a = _school("Spiritual school A")
    school_b = _school("Spiritual school B")
    user = _user(school_a)
    _grant(user, school_a)
    response = _client(user, school_b).get(URL)
    assert response.status_code == 404


def test_django_staff_with_module_grant_is_not_pastoral_authority():
    school = _school("Spiritual pastoral bypass")
    user = _user(school, is_staff=True)
    _grant(user, school)
    response = _client(user, school).get("/api/spiritual-life/pastoral-notes/")
    assert response.status_code == 403


def test_same_school_pastoral_role_allows_pastoral_notes():
    school = _school("Spiritual pastoral allowed")
    user = _user(school)
    _grant(user, school)
    UserRole.objects.create(user=user, school=school, role_code="chaplain")
    response = _client(user, school).get("/api/spiritual-life/pastoral-notes/")
    assert response.status_code == 200


def test_nonpastoral_viewer_cannot_create_private_prayer_request():
    school = _school("Spiritual private prayer")
    user = _user(school)
    _grant(user, school)
    response = _client(user, school).post(
        "/api/spiritual-life/prayer-requests/",
        {"title": "Private", "body": "Sensitive", "visibility": "private"},
        format="json",
    )
    assert response.status_code == 403
