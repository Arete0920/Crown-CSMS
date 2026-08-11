import pytest

from core.models import UserAccount
from sandbox_demo.parent_daily import SandboxParentDailyError, parent_daily_state
from sandbox_demo.services import seed_heritage_flagship


pytestmark = pytest.mark.django_db(transaction=True)


def _user(email):
    return UserAccount.objects.get(username=email)


def test_parent_daily_work_returns_child_attendance_progress_comms_and_billing(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    parent = _user("parent.reed@heritage.example.org")

    state = parent_daily_state(parent)
    assert state["child"]["name"] == "Jordan Reed"
    assert state["attendance"]
    assert state["attendance"][0]["status"] == "PRESENT"
    assert state["progress"]
    assert state["progress"][0]["letter_grade"] == "A"
    assert state["communications"]
    assert state["billing"]["balance_cents"] > 0
    assert state["billing"]["external_payment_provider_enabled"] is False
    assert all(value is False for value in state["staff_controls"].values())

    replay = parent_daily_state(parent)
    assert replay["child"]["id"] == state["child"]["id"]
    assert replay["billing"]["balance_cents"] == state["billing"]["balance_cents"]


def test_non_parent_persona_cannot_use_parent_daily_state(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    teacher = _user("teacher.lower@heritage.example.org")
    with pytest.raises(SandboxParentDailyError, match="heritage_parent_required"):
        parent_daily_state(teacher)
