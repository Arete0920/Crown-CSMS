import pytest

from core.models import Family, StudentIdentityLink, UserAccount
from crown_api.models import AttendanceRecord, GradeRecord
from crown_api.models_comms_core import MessageThread
from sandbox_demo.admin_operations import (
    SandboxAdminError,
    resolve_admin_demo_workflow,
    seed_heritage_admin_context,
    serialize_admin_state,
)
from sandbox_demo.services import seed_heritage_flagship

pytestmark = pytest.mark.django_db(transaction=True)


def _user(email):
    return UserAccount.objects.get(username=email)


def _prepare(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    seed_heritage_admin_context()
    return _user("admin@heritage.example.org")


def test_school_admin_reviews_context_updates_household_resolves_attendance_and_communicates(settings):
    admin = _prepare(settings)
    before = serialize_admin_state(admin)
    assert before.student_number == "HCA-0001"
    assert before.enrollment_status == "ENROLLED"
    assert before.roster_grade
    assert before.tuition_context_cents > 0
    assert "B+" in before.academic_context
    assert before.finance_open_obligation_count > 0
    assert before.finance_open_obligation_cents > 0
    assert before.exception_status == "open"
    assert before.communication_status == "pending"
    assert before.is_platform_superuser is False

    seeded_record = AttendanceRecord.objects.get(student_id=before.student_id, date="2026-08-10")
    assert seeded_record.section_id is not None
    assert seeded_record.status == AttendanceRecord.STATUS_ABSENT
    assert not AttendanceRecord.objects.filter(
        student_id=before.student_id,
        date="2026-08-10",
        section__isnull=True,
    ).exists()
    link = StudentIdentityLink.objects.get(core_student_id=before.student_id)
    assert link.verification_status == StudentIdentityLink.STATUS_VERIFIED
    assert str(link.school_id) == str(admin.school_id)
    assert str(link.compatibility_student.school_id) == str(admin.school_id)

    result = resolve_admin_demo_workflow(admin)
    assert result["student_household_update_persisted"] is True
    assert result["attendance_exception_resolved"] is True
    assert result["communication_sent"] is True
    assert result["attendance_status"] == AttendanceRecord.STATUS_EXCUSED
    assert result["exception_status"] == "resolved"
    assert result["communication_status"] == "sent"
    assert result["household_note"] == "Admin-verified demo household"
    assert result["is_platform_superuser"] is False

    family = Family.objects.get(family_name=result["family_name"], school_id=admin.school_id)
    assert family.address_line2 == "Admin-verified demo household"
    record = AttendanceRecord.objects.get(student_id=result["student_id"], date="2026-08-10")
    assert record.section_id == seeded_record.section_id
    assert record.status == AttendanceRecord.STATUS_EXCUSED
    assert MessageThread.objects.filter(student_id=result["student_id"], subject="Administrator attendance follow-up").exists()

    replay = resolve_admin_demo_workflow(admin)
    assert replay["exception_status"] == "resolved"
    assert replay["communication_status"] == "sent"
    assert AttendanceRecord.objects.filter(
        student_id=result["student_id"],
        date="2026-08-10",
        section_id=record.section_id,
    ).count() == 1
    assert MessageThread.objects.filter(student_id=result["student_id"], subject="Administrator attendance follow-up").count() == 1


def test_admin_state_read_is_side_effect_free(settings):
    admin = _prepare(settings)
    before_attendance = AttendanceRecord.objects.count()
    before_grades = GradeRecord.objects.count()
    before_threads = MessageThread.objects.count()
    first = serialize_admin_state(admin)
    second = serialize_admin_state(admin)
    assert first == second
    assert AttendanceRecord.objects.count() == before_attendance
    assert GradeRecord.objects.count() == before_grades
    assert MessageThread.objects.count() == before_threads


def test_non_admin_persona_is_denied_admin_orchestration(settings):
    _prepare(settings)
    teacher = _user("teacher.lower@heritage.example.org")
    with pytest.raises(SandboxAdminError, match="heritage_school_admin_required"):
        resolve_admin_demo_workflow(teacher)
