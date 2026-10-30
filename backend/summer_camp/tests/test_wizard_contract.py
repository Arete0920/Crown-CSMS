"""Camp setup permission and persistence regression tests on synthetic tenants."""

import uuid

import pytest
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from summer_camp.models import SummerCampConfigWizardState, SummerCampProgramConfig

pytestmark = pytest.mark.django_db
URL = "/api/v1/summer-camp/wizard/setup/"
STEPS = ["Program", "Registration", "Operations", "Review"]


def _user(school, name, *, staff=False):
    return UserAccount.objects.create_user(
        username=f"camp-wizard-{name}-{uuid.uuid4().hex[:8]}",
        password="synthetic-test", school=school, is_staff=staff,
    )


def _grant(user, school, role, *codes):
    UserRole.objects.create(user=user, school=school, role_code=role)
    for code in codes:
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code=role, permission=permission)


def _client(user, school):
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return client


def test_staff_bit_alone_cannot_read_or_mutate_camp_setup():
    school = School.objects.create(name="Camp Wizard Staff Denied")
    user = _user(school, "staff", staff=True)
    client = _client(user, school)
    assert client.get(URL).status_code == 403
    assert client.post(
        URL, {"config": {"camp_name": "Unauthorized"}}, format="json",
    ).status_code == 403
    assert not SummerCampProgramConfig.objects.filter(school=school).exists()
    assert not SummerCampConfigWizardState.objects.filter(school=school).exists()


def test_view_only_role_cannot_save_configuration():
    school = School.objects.create(name="Camp Wizard Viewer")
    user = _user(school, "viewer")
    _grant(user, school, "TEACHER", "summer_camp.view")
    client = _client(user, school)
    assert client.get(URL).status_code == 200
    response = client.post(
        URL, {"config": {"camp_name": "Forbidden Edit"}}, format="json",
    )
    assert response.status_code == 403
    assert SummerCampProgramConfig.objects.get(school=school).camp_name == "Summer Camp"


def test_editor_round_trips_config_and_completion_without_duplicate_state():
    school = School.objects.create(name="Camp Wizard Editor")
    user = _user(school, "editor")
    _grant(user, school, "HEAD_OF_SCHOOL", "summer_camp.view", "summer_camp.edit")
    client = _client(user, school)
    request = {
        "config": {
            "camp_name": "Synthetic Theme Week Camp",
            "default_capacity": 42,
            "default_staff_ratio": 7,
            "public_registration_enabled": False,
            "billing_policy": "PER_WEEK",
        },
        "completed_steps": STEPS,
        "is_completed": True,
    }
    result = client.post(URL, request, format="json")
    assert result.status_code == 200, result.data
    assert result.data["config"]["default_capacity"] == 42
    assert result.data["wizard"]["is_completed"] is True
    assert client.post(URL, request, format="json").status_code == 200
    readback = client.get(URL)
    assert readback.status_code == 200
    assert readback.data["config"]["camp_name"] == "Synthetic Theme Week Camp"
    assert readback.data["config"]["billing_policy"] == "PER_WEEK"
    assert readback.data["wizard"]["completed_steps"] == STEPS
    assert SummerCampProgramConfig.objects.filter(school=school).count() == 1
    assert SummerCampConfigWizardState.objects.filter(school=school).count() == 1


def test_foreign_school_role_does_not_authorize_requested_school():
    school = School.objects.create(name="Camp Wizard Requested")
    foreign = School.objects.create(name="Camp Wizard Foreign")
    user = _user(school, "foreign")
    _grant(user, foreign, "REGISTRAR", "summer_camp.view", "summer_camp.edit")
    client = _client(user, school)
    assert client.get(URL).status_code == 403
    assert client.post(URL, {"config": {"camp_name": "No"}}, format="json").status_code == 403
    assert not SummerCampProgramConfig.objects.filter(school=school).exists()


@pytest.mark.parametrize("payload", [
    {"camp_name": "Legacy flat ignored payload"},
    {"config": {"school": "foreign"}},
    {"config": {"camp_name": "Incomplete"}, "completed_steps": ["Program"], "is_completed": True},
    {"config": {"camp_name": "Out of order"}, "completed_steps": ["Operations"]},
    {"config": {}},
])
def test_invalid_config_does_not_report_success_or_mutate_state(payload):
    school = School.objects.create(name="Camp Wizard Invalid")
    user = _user(school, "invalid")
    _grant(user, school, "REGISTRAR", "summer_camp.edit")
    response = _client(user, school).post(URL, payload, format="json")
    assert response.status_code == 400, response.data
    assert not SummerCampProgramConfig.objects.filter(school=school).exists()
    assert not SummerCampConfigWizardState.objects.filter(school=school).exists()
