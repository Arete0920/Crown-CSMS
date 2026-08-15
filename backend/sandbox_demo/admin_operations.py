from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.models import Enrollment, Student, StudentTuition, UserAccount, UserRole
from crown_api.models import AttendanceRecord, GradeRecord
from crown_api.models_comms_core import Message, MessageThread
from crown_api.models_households import Household as CommsHousehold, Person
from finance.models import FinanceObligation, MoneyStatus

from .attendance_fixture import ensure_section_attendance_identity
from .catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS

ADMIN_EMAIL = SANDBOX_PERSONAS["school_admin"].email
ADMIN_ROLE_CODE = SANDBOX_PERSONAS["school_admin"].role_code
SCHOOL_ID = SANDBOX_SCHOOLS["heritage-core"].id
STUDENT_NUMBER = "HCA-0001"
DEMO_DATE = date(2026, 8, 10)
VERIFIED_ADDRESS_LINE2 = "Admin-verified demo household"
COMMUNICATION_SUBJECT = "Administrator attendance follow-up"

class SandboxAdminError(Exception):
    pass

@dataclass(frozen=True)
class SandboxAdminState:
    student_id: str
    student_number: str
    student_name: str
    family_name: str
    household_note: str
    enrollment_status: str
    roster_grade: str
    tuition_context_cents: int
    academic_context: str
    finance_open_obligation_count: int
    finance_open_obligation_cents: int
    attendance_date: str
    attendance_status: str
    exception_status: str
    communication_status: str
    is_platform_superuser: bool
    is_django_staff: bool

def _require_admin(user) -> UserAccount:
    if not bool(getattr(settings, "CROWN_SANDBOX_ALLOW_OPEN_SESSION", False)):
        raise SandboxAdminError("sandbox_open_session_required")
    if user is None or not getattr(user, "is_authenticated", False):
        raise SandboxAdminError("authenticated_school_admin_required")
    if str(getattr(user, "school_id", "") or "") != str(SCHOOL_ID):
        raise SandboxAdminError("heritage_school_required")
    if str(getattr(user, "email", "") or "").strip().lower() != ADMIN_EMAIL:
        raise SandboxAdminError("heritage_school_admin_required")
    if not UserRole.objects.filter(user=user, school_id=SCHOOL_ID, role_code=ADMIN_ROLE_CODE).exists():
        raise SandboxAdminError("school_admin_role_required")
    if bool(getattr(user, "is_superuser", False)):
        raise SandboxAdminError("platform_authority_boundary_failed")
    return user

def _student() -> Student:
    try:
        return Student.objects.select_related("family", "current_grade_level").get(school_id=SCHOOL_ID, student_number=STUDENT_NUMBER)
    except Student.DoesNotExist as exc:
        raise SandboxAdminError("demo_student_not_seeded") from exc

def seed_heritage_admin_context() -> dict[str, str]:
    student = _student()
    grade_band = student.current_grade_level.code if student.current_grade_level else ""
    _, section = ensure_section_attendance_identity(
        core_student=student,
        course_code="HCA-ADMIN-ATTENDANCE",
        course_name="Administrator Attendance Review",
        grade_band=grade_band,
        evidence_reference=f"sandbox:heritage:admin-operations:{STUDENT_NUMBER}",
    )
    AttendanceRecord.objects.filter(student=student, date=DEMO_DATE, section__isnull=True).delete()
    attendance, _ = AttendanceRecord.objects.update_or_create(
        student=student,
        section=section,
        date=DEMO_DATE,
        defaults={
            "course": None,
            "status": AttendanceRecord.STATUS_ABSENT,
            "notes_public": "Sandbox section-aware attendance exception awaiting administrator review.",
        },
    )
    grade, _ = GradeRecord.objects.update_or_create(student=student, course=None, period="Q1", assignment_name="Administrator progress checkpoint", defaults={"category": "Progress", "score": 88, "score_max": 100, "letter_grade": "B+", "posted_at": timezone.now(), "notes_public": "On track; continue monitoring first-quarter progress."})
    return {"admin_attendance_id": str(attendance.id), "admin_grade_id": str(grade.id)}

def _attendance(student: Student) -> AttendanceRecord:
    try:
        return AttendanceRecord.objects.select_related("section").get(student=student, section__isnull=False, date=DEMO_DATE)
    except AttendanceRecord.DoesNotExist as exc:
        raise SandboxAdminError("admin_attendance_not_seeded") from exc
    except AttendanceRecord.MultipleObjectsReturned as exc:
        raise SandboxAdminError("admin_attendance_duplicate_scope") from exc

def _academic_context(student: Student) -> GradeRecord:
    try:
        return GradeRecord.objects.get(student=student, course=None, period="Q1", assignment_name="Administrator progress checkpoint")
    except GradeRecord.DoesNotExist as exc:
        raise SandboxAdminError("admin_academic_context_not_seeded") from exc

def _communication_exists(student: Student) -> bool:
    return MessageThread.objects.filter(student=student, subject=COMMUNICATION_SUBJECT).exists()

def _create_admin_communication(student: Student, admin: UserAccount) -> None:
    household, _ = CommsHousehold.objects.update_or_create(household_name=f"{student.family.family_name} Admin Communication", defaults={"primary_address_line1": student.family.address_line1, "primary_city": student.family.city, "primary_state": student.family.state, "primary_postal_code": student.family.zip_code})
    sender, _ = Person.objects.update_or_create(email=admin.email, defaults={"first_name": admin.first_name or "Grace", "last_name": admin.last_name or "Whitaker"})
    thread, _ = MessageThread.objects.update_or_create(household=household, student=student, subject=COMMUNICATION_SUBJECT, defaults={"thread_type": "ATTENDANCE_FOLLOW_UP", "created_by": sender, "last_message_at": timezone.now()})
    Message.objects.update_or_create(thread=thread, sender_person=sender, body="The attendance exception was reviewed and resolved. No further family action is required for this demo record.", defaults={"sent_at": timezone.now()})

def serialize_admin_state(user) -> SandboxAdminState:
    admin = _require_admin(user)
    student = _student()
    attendance = _attendance(student)
    grade = _academic_context(student)
    enrollment = Enrollment.objects.filter(school_id=SCHOOL_ID, student=student).select_related("grade_level").order_by("-academic_year__start_date").first()
    tuition = StudentTuition.objects.filter(school_id=SCHOOL_ID, student=student).order_by("-academic_year__start_date").first()
    open_obligations = FinanceObligation.objects.filter(school_id=SCHOOL_ID, status=MoneyStatus.OPEN)
    finance_open_cents = sum(int(value) for value in open_obligations.values_list("amount_cents", flat=True))
    return SandboxAdminState(student_id=str(student.id), student_number=student.student_number, student_name=f"{student.first_name} {student.last_name}".strip(), family_name=student.family.family_name, household_note=student.family.address_line2 or "", enrollment_status=enrollment.status if enrollment else "NOT ENROLLED", roster_grade=(enrollment.grade_level.code if enrollment and enrollment.grade_level else (student.current_grade_level.code if student.current_grade_level else "")), tuition_context_cents=int(tuition.net_annual_cents) if tuition else 0, academic_context=f"{grade.assignment_name}: {grade.letter_grade} ({grade.score}/{grade.score_max})", finance_open_obligation_count=open_obligations.count(), finance_open_obligation_cents=finance_open_cents, attendance_date=attendance.date.isoformat(), attendance_status=attendance.status, exception_status="resolved" if attendance.status == AttendanceRecord.STATUS_EXCUSED else "open", communication_status="sent" if _communication_exists(student) else "pending", is_platform_superuser=bool(admin.is_superuser), is_django_staff=bool(admin.is_staff))

@transaction.atomic
def resolve_admin_demo_workflow(user) -> dict:
    admin = _require_admin(user)
    student = _student()
    family = student.family
    family.address_line2 = VERIFIED_ADDRESS_LINE2
    family.save(update_fields=["address_line2", "updated_at"])
    attendance = _attendance(student)
    attendance.status = AttendanceRecord.STATUS_EXCUSED
    attendance.notes_public = "Attendance exception reviewed and excused by Heritage sandbox school administrator."
    attendance.save(update_fields=["status", "notes_public", "updated_at"])
    _create_admin_communication(student, admin)
    state = serialize_admin_state(admin)
    if state.exception_status != "resolved" or state.household_note != VERIFIED_ADDRESS_LINE2:
        raise SandboxAdminError("administrator_transaction_failed")
    if state.communication_status != "sent":
        raise SandboxAdminError("administrator_communication_failed")
    payload = asdict(state)
    payload.update({"student_household_update_persisted": True, "attendance_exception_resolved": True, "communication_sent": True})
    return payload
