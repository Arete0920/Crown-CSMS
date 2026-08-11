import pytest
from rest_framework.test import APIClient

from core.models import UserAccount
from sandbox_demo.services import seed_heritage_flagship
from sandbox_demo.student_self_service import SandboxStudentError, student_self_service_state


pytestmark = pytest.mark.django_db(transaction=True)


def _user(email):
    return UserAccount.objects.get(username=email)


def test_student_self_service_returns_real_schedule_progress_attendance_and_comms(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    student_user = _user("student.avery.reed11@heritage.example.org")

    state = student_self_service_state(student_user)
    assert state["student"]["name"] == "Avery Reed"
    assert state["schedule"]
    assert state["learning_tasks"]
    assert state["attendance"]
    assert state["communications"]
    assert all(value is False for value in state["privileged_actions"].values())

    replay = student_self_service_state(student_user)
    assert replay["student"]["id"] == state["student"]["id"]
    assert replay["schedule"] == state["schedule"]


def test_non_student_persona_cannot_use_student_self_service(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    teacher = _user("teacher.lower@heritage.example.org")
    with pytest.raises(SandboxStudentError, match="heritage_student_required"):
        student_self_service_state(teacher)


def test_student_self_service_requires_sandbox_open_session(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = False
    seed_heritage_flagship(reset=True)
    student_user = _user("student.avery.reed11@heritage.example.org")
    with pytest.raises(SandboxStudentError, match="sandbox_open_session_required"):
        student_self_service_state(student_user)


def test_student_self_service_api_returns_real_state(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    student_user = _user("student.avery.reed11@heritage.example.org")
    client = APIClient()
    client.force_authenticate(user=student_user)
    response = client.get("/api/v1/sandbox/student/self-service/")
    assert response.status_code == 200, response.content
    payload = response.json()
    assert payload["student"]["name"] == "Avery Reed"
    assert payload["schedule"]
    assert payload["learning_tasks"]
    assert payload["attendance"]
    assert payload["communications"]
    assert all(value is False for value in payload["privileged_actions"].values())


def test_student_self_service_api_denies_non_student_persona(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    teacher = _user("teacher.lower@heritage.example.org")
    client = APIClient()
    client.force_authenticate(user=teacher)
    response = client.get("/api/v1/sandbox/student/self-service/")
    assert response.status_code == 403
    assert response.json()["detail"] == "heritage_student_required"


def test_student_self_service_api_requires_authentication(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    client = APIClient()
    response = client.get("/api/v1/sandbox/student/self-service/")
    assert response.status_code in {401, 403}
