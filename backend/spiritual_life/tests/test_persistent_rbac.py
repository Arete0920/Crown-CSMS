from __future__ import annotations

import uuid

import pytest
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from spiritual_life.models import ChapelEvent


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


@pytest.mark.parametrize("prefix", ["/api/spiritual-life/", "/api/v1/spiritual-life/"])
@pytest.mark.parametrize("surface", ["chapel-events/", "formation/portrait-domains/"])
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_view_only_authority_denies_every_unsafe_method(prefix, surface, method):
    school = _school("Spiritual unsafe methods")
    user = _user(school)
    _grant(user, school)
    response = getattr(_client(user, school), method)(prefix + surface, {}, format="json")
    assert response.status_code == 403


def _grant_edit(user, school):
    permission, _ = CrownPermission.objects.get_or_create(code="spiritual_life.edit")
    role_code = "spiritual_life_edit_security_test"
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)
    UserRole.objects.get_or_create(user=user, school=school, role_code=role_code)


def test_explicit_editor_can_create_and_update_chapel_event():
    school = _school("Spiritual editor")
    user = _user(school)
    _grant(user, school)
    _grant_edit(user, school)
    client = _client(user, school)
    response = client.post(URL, {"title": "Authorized chapel", "event_date": "2026-10-08"}, format="json")
    assert response.status_code == 201
    event = ChapelEvent.objects.get(school=school, title="Authorized chapel")
    response = client.patch(f"{URL}{event.id}/", {"title": "Updated chapel"}, format="json")
    assert response.status_code == 200
    event.refresh_from_db()
    assert event.title == "Updated chapel"


def test_view_only_user_cannot_update_existing_chapel_event():
    school = _school("Spiritual update denied")
    user = _user(school)
    _grant(user, school)
    event = ChapelEvent.objects.create(school=school, title="Original", event_date="2026-10-08")
    response = _client(user, school).patch(f"{URL}{event.id}/", {"title": "Unauthorized"}, format="json")
    assert response.status_code == 403
    event.refresh_from_db()
    assert event.title == "Original"


def test_edit_permission_without_view_permission_is_denied():
    school = _school("Spiritual edit alone")
    user = _user(school)
    _grant_edit(user, school)
    response = _client(user, school).post(URL, {"title": "Denied", "event_date": "2026-10-08"}, format="json")
    assert response.status_code == 403
    assert not ChapelEvent.objects.filter(school=school).exists()


def test_edit_grant_in_another_school_does_not_authorize_writes():
    school_a = _school("Spiritual edit school A")
    school_b = _school("Spiritual view school B")
    user = _user(school_b)
    _grant(user, school_b)
    _grant_edit(user, school_a)
    response = _client(user, school_b).post(URL, {"title": "Denied", "event_date": "2026-10-08"}, format="json")
    assert response.status_code == 403
    assert not ChapelEvent.objects.filter(school=school_b).exists()


def test_cross_tenant_editor_without_target_grant_is_concealed():
    school_a = _school("Spiritual editor school A")
    school_b = _school("Spiritual denied school B")
    user = _user(school_a)
    _grant(user, school_a)
    _grant_edit(user, school_a)
    response = _client(user, school_b).post(URL, {"title": "Denied", "event_date": "2026-10-08"}, format="json")
    assert response.status_code == 404
    assert not ChapelEvent.objects.filter(school=school_b).exists()


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


def test_view_only_user_cannot_create_school_wide_spiritual_life_record():
    school = _school("Spiritual write denied")
    user = _user(school)
    _grant(user, school)

    response = _client(user, school).post(
        URL,
        {
            "title": "Unauthorized chapel",
            "event_date": "2026-10-08",
        },
        format="json",
    )

    assert response.status_code == 403
