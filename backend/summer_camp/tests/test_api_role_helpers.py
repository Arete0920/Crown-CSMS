from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from summer_camp import api


def _request(user=None, school=None):
    return SimpleNamespace(user=user, school=school)


def _user(*, authenticated=True, superuser=False, staff=False):
    return SimpleNamespace(
        is_authenticated=authenticated,
        is_superuser=superuser,
        is_staff=staff,
    )


def test_require_role_fails_closed_without_authenticated_user(monkeypatch):
    permission_check = Mock()
    monkeypatch.setattr(api, "user_has_permission", permission_check)

    assert api._require_role(_request(), api.VIEW_ROLES) is False
    assert api._require_role(_request(_user(authenticated=False)), api.VIEW_ROLES) is False
    permission_check.assert_not_called()


def test_require_role_denies_superuser_without_explicit_school_grant(monkeypatch):
    school = SimpleNamespace(id="school-a")
    permission_check = Mock(return_value=False)
    monkeypatch.setattr(api, "user_has_permission", permission_check)

    assert api._require_role(_request(_user(superuser=True), school), api.EDIT_ROLES) is False
    assert permission_check.call_count == 1
    assert permission_check.call_args.args[1] == "summer_camp.edit"
    assert permission_check.call_args.kwargs == {"school": school}


def test_require_role_denies_staff_without_explicit_school_grant(monkeypatch):
    school = SimpleNamespace(id="school-a")
    permission_check = Mock(return_value=False)
    monkeypatch.setattr(api, "user_has_permission", permission_check)

    assert api._require_role(_request(_user(staff=True), school), api.EDIT_ROLES) is False
    assert permission_check.call_count == 1
    assert permission_check.call_args.kwargs == {"school": school}


def test_require_role_checks_permissions_against_request_school(monkeypatch):
    school = SimpleNamespace(id="school-a")
    user = _user()
    permission_check = Mock(
        side_effect=lambda _user, permission, *, school: permission == "summer_camp.view"
    )
    monkeypatch.setattr(api, "user_has_permission", permission_check)

    assert api._require_role(_request(user, school), api.VIEW_ROLES) is True
    assert permission_check.call_count >= 1
    for call in permission_check.call_args_list:
        assert call.args[0] is user
        assert call.kwargs == {"school": school}


def test_require_role_denies_when_no_allowed_permission_matches(monkeypatch):
    school = SimpleNamespace(id="school-a")
    user = _user()
    permission_check = Mock(return_value=False)
    monkeypatch.setattr(api, "user_has_permission", permission_check)

    assert api._require_role(_request(user, school), api.EDIT_ROLES) is False
    permission_check.assert_called_once_with(
        user,
        "summer_camp.edit",
        school=school,
    )


def test_view_roles_include_view_and_edit_permissions():
    assert api.VIEW_ROLES == {"summer_camp.view", "summer_camp.edit"}


def test_edit_roles_are_restricted_to_edit_permission():
    assert api.EDIT_ROLES == {"summer_camp.edit"}


@pytest.mark.django_db
def test_unprivileged_django_staff_cannot_create_camp_config_on_read():
    import uuid
    from rest_framework.test import APIClient
    from core.models import School, UserAccount
    from summer_camp.models import SummerCampProgramConfig

    school = School.objects.create(name=f"Camp RBAC Denied {uuid.uuid4().hex[:8]}")
    user = UserAccount.objects.create_user(
        username=f"camp-no-grant-{uuid.uuid4().hex[:8]}",
        password="synthetic", school=school, is_staff=True,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    assert client.get("/api/v1/summer-camp/config/").status_code == 403
    assert client.put(
        "/api/v1/summer-camp/config/", {"camp_name": "Unauthorized"}, format="json",
    ).status_code == 403
    assert not SummerCampProgramConfig.objects.filter(school=school).exists()
