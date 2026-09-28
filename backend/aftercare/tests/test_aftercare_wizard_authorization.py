import uuid

import pytest
from rest_framework.test import APIClient

from aftercare.models import AftercareProgramConfig
from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole

pytestmark = pytest.mark.django_db

URL = "/api/v1/aftercare/wizard/setup/"


def _user(school: School, suffix: str, *, is_staff: bool = False) -> UserAccount:
    return UserAccount.objects.create_user(
        username=f"aftercare-wizard-{suffix}-{uuid.uuid4().hex[:8]}",
        email=f"aftercare-wizard-{suffix}@example.com",
        password="test-pass",
        school=school,
        is_staff=is_staff,
    )


def _grant(user: UserAccount, school: School, role_code: str, *permission_codes: str) -> None:
    UserRole.objects.create(user=user, school=school, role_code=role_code)
    for code in permission_codes:
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code=role_code, permission=permission)


def _client(user: UserAccount, school: School) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return client


def test_wizard_get_requires_extended_care_view():
    school = School.objects.create(name="Wizard Read Denied")
    user = _user(school, "read-denied")

    response = _client(user, school).get(URL)

    assert response.status_code == 403
    assert not AftercareProgramConfig.objects.filter(school_fk=school).exists()


def test_django_staff_flag_does_not_bypass_wizard_permission():
    school = School.objects.create(name="Wizard Staff Denied")
    user = _user(school, "staff-denied", is_staff=True)

    client = _client(user, school)
    assert client.get(URL).status_code == 403
    assert client.post(URL, {"late_fee_grace_minutes": 5}, format="json").status_code == 403
    assert not AftercareProgramConfig.objects.filter(school_fk=school).exists()


def test_view_permission_allows_get_but_not_post():
    school = School.objects.create(name="Wizard Viewer")
    user = _user(school, "viewer")
    _grant(user, school, "wizard_viewer", "extended_care.view")

    client = _client(user, school)
    get_response = client.get(URL)
    post_response = client.post(URL, {"late_fee_grace_minutes": 5}, format="json")

    assert get_response.status_code == 200
    assert post_response.status_code == 403
    config = AftercareProgramConfig.objects.get(school_fk=school)
    assert config.school_id is None
    assert config.late_fee_grace_minutes == 0


def test_edit_permission_updates_only_canonical_school_config():
    school = School.objects.create(name="Wizard Editor")
    user = _user(school, "editor")
    _grant(user, school, "wizard_editor", "extended_care.edit")

    response = _client(user, school).post(
        URL,
        {"config": {"late_fee_grace_minutes": 7, "late_fee_cap": "75.00"}},
        format="json",
    )

    assert response.status_code == 200
    config = AftercareProgramConfig.objects.get(school_fk=school)
    assert config.school_id is None
    assert config.late_fee_grace_minutes == 7
    assert str(config.late_fee_cap) == "75.00"
    assert AftercareProgramConfig.objects.filter(school_fk=school).count() == 1


def test_permission_in_other_school_does_not_authorize_wizard():
    requested_school = School.objects.create(name="Wizard Requested School")
    other_school = School.objects.create(name="Wizard Other School")
    user = _user(requested_school, "cross-school")
    _grant(user, other_school, "wizard_other_school", "extended_care.view", "extended_care.edit")

    client = _client(user, requested_school)

    assert client.get(URL).status_code == 403
    assert client.post(URL, {"late_fee_grace_minutes": 9}, format="json").status_code == 403
    assert not AftercareProgramConfig.objects.filter(school_fk=requested_school).exists()


def test_permission_scope_uses_canonical_school_without_middleware():
    """Direct DRF invocation must never fall back to roles from all schools."""
    from rest_framework.test import APIRequestFactory, force_authenticate
    from aftercare.wizard_api import aftercare_setup_wizard

    school = School.objects.create(name="Direct Wizard Requested")
    other_school = School.objects.create(name="Direct Wizard Other")
    user = _user(school, "direct-cross-school")
    _grant(user, other_school, "direct_wizard_other", "extended_care.view", "extended_care.edit")
    factory = APIRequestFactory()
    for method in ("get", "post"):
        request = getattr(factory, method)(URL, {}, format="json", HTTP_X_SCHOOL_ID=str(school.id))
        force_authenticate(request, user=user)
        assert aftercare_setup_wizard(request).status_code == 403
    assert not AftercareProgramConfig.objects.filter(school_fk=school).exists()
