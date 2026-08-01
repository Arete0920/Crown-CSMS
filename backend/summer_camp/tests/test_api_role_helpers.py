from types import SimpleNamespace
from unittest.mock import Mock

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


def test_require_role_allows_superuser_without_permission_lookup(monkeypatch):
    permission_check = Mock()
    monkeypatch.setattr(api, "user_has_permission", permission_check)

    assert api._require_role(_request(_user(superuser=True)), api.EDIT_ROLES) is True
    permission_check.assert_not_called()


def test_require_role_allows_staff_without_permission_lookup(monkeypatch):
    permission_check = Mock()
    monkeypatch.setattr(api, "user_has_permission", permission_check)

    assert api._require_role(_request(_user(staff=True)), api.EDIT_ROLES) is True
    permission_check.assert_not_called()


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
