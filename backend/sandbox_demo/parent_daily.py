from __future__ import annotations

from datetime import date

from django.conf import settings
from django.utils import timezone

from core.models import Family, GradeLevel, Student, UserAccount
from crown_api.models import AttendanceRecord, GradeRecord
from crown_api.models_academics_core import Course
from crown_api.models_comms_core import Message, MessageThread
from crown_api.models_households import Household as CommsHousehold, Person
from finance.models import FinanceAllocation, FinanceObligation, MoneyStatus

from .attendance_fixture import ensure_section_attendance_identity
from .catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS


PARENT_EMAIL = SANDBOX_PERSONAS["parent"].email
SCHOOL_ID = SANDBOX_SCHOOLS["heritage-core"].id
STUDENT_NUMBER = "HCA-PARENT-JORDAN"
COURSE_CODE = "HCA-PARENT-ELA7"
COMMS_HOUSEHOLD_NAME = "Reed Family Parent Sandbox HCA"


class SandboxParentDailyError(Exception):
    pass


def _require_parent(user) -> UserAccount:
    if not bool(getattr(settings, "CROWN_SANDBOX_ALLOW_OPEN_SESSION", False)):
        raise SandboxParentDailyError("sandbox_open_session_required")
    if user is None or not getattr(user, "is_authenticated", False):
        raise SandboxParentDailyError("authenticated_parent_required")
    if str(getattr(user, "email", "") or "").strip().lower() != PARENT_EMAIL:
        raise SandboxParentDailyError("heritage_parent_required")
    if str(getattr(user, "school_id", "") or "") != str(SCHOOL_ID):
        raise SandboxParentDailyError("heritage_school_required")
    return user


def _ensure_daily_records(parent: UserAccount) -> Student:
    family, _ = Family.objects.get_or_create(
        school_id=SCHOOL_ID,
        family_name="Reed Family",
        defaults={
            "address_line1": "100 Demo Lane",
            "city": "Fairview",
            "state": "PA",
            "zip_code": "19000",
            "status": "ACTIVE",
        },
    )
    grade, _ = GradeLevel.objects.get_or_create(
        school_id=SCHOOL_ID,
        code="7",
        defaults={"label": "Grade 7", "sort_order": 8},
    )
    student, _ = Student.objects.update_or_create(
        school_id=SCHOOL_ID,
        student_number=STUDENT_NUMBER,
        defaults={
            "family": family,
            "first_name": "Jordan",
            "last_name": "Reed",
            "dob": date(2013, 2, 15),
            "status": "ACTIVE",
            "current_grade_level": grade,
        },
    )

    course, _ = Course.objects.update_or_create(
        course_code=COURSE_CODE,
        defaults={"name": "Grade 7 English Language Arts", "term": "Fall 2026", "active": True},
    )
    _, section = ensure_section_attendance_identity(
        core_student=student,
        course_code=COURSE_CODE,
        course_name="Grade 7 English Language Arts",
        grade_band="7",
        evidence_reference=f"sandbox:heritage:parent-daily:{STUDENT_NUMBER}",
    )
    AttendanceRecord.objects.filter(
        student=student,
        date=date(2026, 8, 10),
        section__isnull=True,
    ).delete()
    AttendanceRecord.objects.update_or_create(
        student=student,
        section=section,
        date=date(2026, 8, 10),
        defaults={
            "course": None,
            "status": AttendanceRecord.STATUS_PRESENT,
            "notes_public": "Heritage family-view section-aware attendance.",
        },
    )
    GradeRecord.objects.update_or_create(
        student=student,
        course=course,
        period="Q1",
        assignment_name="First Week Reading Check",
        defaults={
            "category": "Reading",
            "score": 19,
            "score_max": 20,
            "letter_grade": "A",
            "posted_at": timezone.now(),
            "notes_public": "Jordan is off to a strong start.",
        },
    )

    household, _ = CommsHousehold.objects.update_or_create(
        household_name=COMMS_HOUSEHOLD_NAME,
        defaults={
            "primary_address_line1": "100 Demo Lane",
            "primary_city": "Fairview",
            "primary_state": "PA",
            "primary_postal_code": "19000",
        },
    )
    teacher, _ = Person.objects.update_or_create(
        email="teacher.lower@heritage.example.org",
        defaults={"first_name": "Eleanor", "last_name": "Lower", "phone": "555-0110"},
    )
    thread, _ = MessageThread.objects.update_or_create(
        household=household,
        student=student,
        subject="Jordan Reed - First Week Update",
        defaults={
            "thread_type": "FAMILY_UPDATE",
            "created_by": teacher,
            "last_message_at": timezone.now(),
        },
    )
    Message.objects.update_or_create(
        thread=thread,
        sender_person=teacher,
        body="Jordan participated well today. Please review the reading notes before Friday.",
        defaults={"sent_at": timezone.now()},
    )
    return student


def _family_balance(parent: UserAccount) -> int:
    obligations = list(
        FinanceObligation.objects.filter(
            school_id=SCHOOL_ID,
            payer_user=parent,
        ).exclude(status=MoneyStatus.VOID)
    )
    total = sum(int(row.amount_cents) for row in obligations)
    allocated = sum(
        int(value)
        for value in FinanceAllocation.objects.filter(
            school_id=SCHOOL_ID,
            obligation__in=obligations,
        ).values_list("amount_cents", flat=True)
    )
    return max(total - allocated, 0)


def parent_daily_state(user) -> dict:
    parent = _require_parent(user)
    student = _ensure_daily_records(parent)
    attendance = (
        AttendanceRecord.objects.filter(student=student, section__isnull=False)
        .select_related("section__course")
        .order_by("-date", "section_id")
    )
    grades = GradeRecord.objects.filter(student=student).select_related("course").order_by("-posted_at")
    threads = MessageThread.objects.filter(student=student).prefetch_related("messages").order_by("-last_message_at")
    return {
        "child": {
            "id": str(student.id),
            "student_number": student.student_number,
            "name": f"{student.first_name} {student.last_name}",
            "grade": student.current_grade_level.code if student.current_grade_level else "",
        },
        "attendance": [
            {"date": row.date.isoformat(), "section_id": str(row.section_id), "course": row.section.course.name, "status": row.status}
            for row in attendance
        ],
        "progress": [
            {
                "assignment": row.assignment_name,
                "course": row.course.name if row.course else "",
                "score": str(row.score) if row.score is not None else None,
                "score_max": str(row.score_max) if row.score_max is not None else None,
                "letter_grade": row.letter_grade,
                "feedback": row.notes_public,
            }
            for row in grades
        ],
        "communications": [
            {"subject": thread.subject, "messages": [message.body for message in thread.messages.all()]}
            for thread in threads
        ],
        "billing": {
            "balance_cents": _family_balance(parent),
            "external_payment_provider_enabled": False,
        },
        "staff_controls": {
            "grade_write": False,
            "attendance_write": False,
            "admissions_decision": False,
            "finance_admin": False,
            "tenant_admin": False,
        },
    }
