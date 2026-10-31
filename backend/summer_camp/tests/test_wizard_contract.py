"""Camp setup access, persistence, completion and payload guard regressions."""
import uuid
import pytest
from rest_framework.test import APIClient
from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from summer_camp.models import SummerCampProgramConfig, SummerCampConfigWizardState
pytestmark = pytest.mark.django_db
URL = "/api/v1/summer-camp/wizard/setup/"
STEPS = ["Program", "Registration", "Operations", "Review"]


def _client(school, role=None, *grants, staff=False, foreign=None):
    user = UserAccount.objects.create_user(username=f"camp-wizard-{uuid.uuid4().hex}",
                                           school=school, password="synthetic", is_staff=staff)
    if role:
        UserRole.objects.create(user=user, school=foreign or school, role_code=role)
        for grant in grants:
            permission, _ = CrownPermission.objects.get_or_create(code=grant)
            RolePermission.objects.get_or_create(role_code=role, permission=permission)
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return client


def _no_state(school):
    assert not SummerCampProgramConfig.objects.filter(school=school).exists()
    assert not SummerCampConfigWizardState.objects.filter(school=school).exists()


def test_ordinary_staff_and_foreign_role_cannot_read_or_write():
    school = School.objects.create(name="Camp Wizard")
    foreign = School.objects.create(name="Foreign Camp Wizard")
    clients = [_client(school, staff=True),
               _client(school, "REGISTRAR", "summer_camp.view", "summer_camp.edit", foreign=foreign)]
    for client in clients:
        assert client.get(URL).status_code == 403
        assert client.post(URL, {"config": {"camp_name": "Denied"}}, format="json").status_code == 403
        _no_state(school)


def test_view_only_grant_cannot_mutate_configuration():
    school = School.objects.create(name="Camp Viewer")
    client = _client(school, "TEACHER", "summer_camp.view")
    assert client.get(URL).status_code == 200
    assert client.post(URL, {"config": {"camp_name": "Denied"}}, format="json").status_code == 403
    assert SummerCampProgramConfig.objects.get(school=school).camp_name == "Summer Camp"


def test_editor_roundtrip_idempotence_completion_reset_and_rejection():
    school = School.objects.create(name="Camp Editor")
    client = _client(school, "HEAD_OF_SCHOOL", "summer_camp.view", "summer_camp.edit")
    payload = {"config": {"camp_name": "Theme Week", "default_capacity": 42,
              "default_staff_ratio": 7, "public_registration_enabled": False,
              "billing_policy": "PER_WEEK"}, "completed_steps": STEPS, "is_completed": True}
    for _ in range(2):
        result = client.post(URL, payload, format="json")
        assert result.status_code == 200 and result.data["wizard"]["is_completed"] is True
        assert result.data["config"]["default_capacity"] == 42
    read = client.get(URL)
    assert read.data["config"]["camp_name"] == "Theme Week"
    assert read.data["config"]["billing_policy"] == "PER_WEEK"
    assert read.data["wizard"]["completed_steps"] == STEPS
    assert SummerCampProgramConfig.objects.filter(school=school).count() == 1
    assert SummerCampConfigWizardState.objects.filter(school=school).count() == 1
    revised = client.post(URL, {"config": {"camp_name": "Revised"},
                               "completed_steps": ["Program"]}, format="json")
    assert revised.status_code == 200
    assert revised.data["wizard"] == {"completed_steps": ["Program"], "is_completed": False}
    denied = client.post(URL, {"config": {"camp_name": "Must Not Persist"},
                              "completed_steps": ["Program"], "is_completed": True}, format="json")
    assert denied.status_code == 400
    assert client.get(URL).data["config"]["camp_name"] == "Revised"
    state = SummerCampConfigWizardState.objects.get(school=school)
    assert state.completed_steps == ["Program"] and state.is_completed is False


@pytest.mark.parametrize("payload", [
    {"camp_name": "Legacy flat"}, {"config": {"school": "foreign"}},
    {"config": {"camp_name": "Incomplete"}, "completed_steps": ["Program"], "is_completed": True},
    {"config": {"camp_name": "Out of order"}, "completed_steps": ["Operations"]},
    {"config": {}},
])
def test_invalid_payloads_have_no_side_effects(payload):
    school = School.objects.create(name="Camp Invalid")
    client = _client(school, "REGISTRAR", "summer_camp.edit")
    assert client.post(URL, payload, format="json").status_code == 400
    _no_state(school)
