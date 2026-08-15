import pytest

from core.models import StudentIdentityLink, UserAccount
from crown_api.models import AttendanceRecord
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
    attendance_row = state["attendance"][0]
    assert attendance_row["status"] == AttendanceRecord.STATUS_PRESENT
    assert attendance_row["section_id"]

    record = AttendanceRecord.objects.get(student_id=state["child"]["id"], date="2026-08-10")
    assert record.section_id is not None
    assert record.status == AttendanceRecord.STATUS_PRESENT
    assert not AttendanceRecord.objects.filter(
        student_id=state["child"]["id"],
        date="2026-08-10",
        section__isnull=True,
    ).exists()
    link = StudentIdentityLink.objects.get(core_student_id=state["child"]["id"])
    assert link.verification_status == StudentIdentityLink.STATUS_VERIFIED
    assert link.evidence_reference
    assert str(link.school_id) == str(parent.school_id)
    assert str(link.compatibility_student.school_id) == str(parent.school_id)

    assert state["progress"]
    assert state["progress"][0]["letter_grade"] == "A"
    assert state["communications"]
    assert state["billing"]["balance_cents"] > 0
    assert state["billing"]["external_payment_provider_enabled"] is False
    assert all(value is False for value in state["staff_controls"].values())

    replay = parent_daily_state(parent)
    assert replay["child"]["id"] == state["child"]["id"]
    assert replay["attendance"] == state["attendance"]
    assert replay["billing"]["balance_cents"] == state["billing"]["balance_cents"]
    assert AttendanceRecord.objects.filter(
        student_id=state["child"]["id"],
        date="2026-08-10",
        section_id=record.section_id,
    ).count() == 1


def test_non_parent_persona_cannot_use_parent_daily_state(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    teacher = _user("teacher.lower@heritage.example.org")
    with pytest.raises(SandboxParentDailyError, match="heritage_parent_required"):
        parent_daily_state(teacher)
