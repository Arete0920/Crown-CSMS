from __future__ import annotations

from datetime import date

from django.conf import settings
from django.utils import timezone

from core.models import Family, GradeLevel, Student, UserAccount
from crown_api.models import AttendanceRecord, GradeRecord
from crown_api.models_academics_core import Course
from crown_api.models_comms_core import Message, MessageThread
from crown_api.models_households import Household as CommsHousehold, Person
from crown_api.models_scheduling_core import Section, SectionEnrollment, Term

from .catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS


STUDENT_EMAIL = SANDBOX_PERSONAS["student"].email
SCHOOL_ID = SANDBOX_SCHOOLS["heritage-core"].id
STUDENT_NUMBER = "HCA-STUDENT-AVERY"
TERM_CODE = "2026-FALL-STUDENT"
COURSE_CODE = "HCA-STU-ELA7"


class SandboxStudentError(Exception):
    pass


def _require_student(user) -> UserAccount:
    if not bool(getattr(settings, "CROWN_SANDBOX_ALLOW_OPEN_SESSION", False)):
        raise SandboxStudentError("sandbox_open_session_required")
    if user is None or not getattr(user, "is_authenticated", False):
        raise SandboxStudentError("authenticated_student_required")
    if str(getattr(user, "email", "") or "").strip().lower() != STUDENT_EMAIL:
        raise SandboxStudentError("heritage_student_required")
    if str(getattr(user, "school_id", "") or "") != str(SCHOOL_ID):
        raise SandboxStudentError("heritage_school_required")
    return user


def _ensure_student_records() -> Student:
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
            "first_name": "Avery",
            "last_name": "Reed",
            "dob": date(2013, 4, 12),
            "status": "ACTIVE",
            "current_grade_level": grade,
        },
    )

    course, _ = Course.objects.update_or_create(
        course_code=COURSE_CODE,
        defaults={"name": "Grade 7 English Language Arts", "term": "Fall 2026", "active": True},
    )
    term, _ = Term.objects.update_or_create(
        code=TERM_CODE,
        defaults={
            "name": "Fall 2026",
            "start_date": date(2026, 8, 15),
            "end_date": date(2026, 12, 18),
            "active": True,
        },
    )
    teacher, _ = Person.objects.update_or_create(
        email="teacher.lower@heritage.example.org",
        defaults={"first_name": "Eleanor", "last_name": "Lower", "phone": "555-0110"},
    )
    section, _ = Section.objects.update_or_create(
        term=term,
        course=course,
        section_code="01",
        defaults={
            "name_override": "ELA 7 - Section 1",
            "teacher": teacher,
            "room": "207",
            "meeting_days": "MTWTF",
            "meeting_time": "09:15-10:05",
        },
    )
    SectionEnrollment.objects.update_or_create(section=section, student=student, defaults={"active": True})
    AttendanceRecord.objects.update_or_create(student=student, course=course, date=date(2026, 8, 10), defaults={"status": AttendanceRecord.STATUS_PRESENT, "notes_public": "Heritage sandbox attendance."})
    GradeRecord.objects.update_or_create(student=student, course=course, period="Q1", assignment_name="Summer Reading Reflection", defaults={"category": "Writing", "score": 92, "score_max": 100, "letter_grade": "A-", "posted_at": timezone.now(), "notes_public": "Strong textual evidence and clear reflection."})
    GradeRecord.objects.update_or_create(student=student, course=course, period="Q1", assignment_name="Vocabulary Check 1", defaults={"category": "Assessment", "score": 18, "score_max": 20, "letter_grade": "A-", "posted_at": timezone.now(), "notes_public": "Review two missed terms before Friday."})
    comms_household, _ = CommsHousehold.objects.update_or_create(household_name="Reed Family Student Sandbox", defaults={"primary_address_line1": "100 Demo Lane", "primary_city": "Fairview", "primary_state": "PA", "primary_postal_code": "19000"})
    thread, _ = MessageThread.objects.update_or_create(household=comms_household, student=student, subject="Grade 7 Welcome and First Week", defaults={"thread_type": "ANNOUNCEMENT", "created_by": teacher, "last_message_at": timezone.now()})
    Message.objects.update_or_create(thread=thread, sender_person=teacher, body="Welcome to Grade 7. Bring your summer reading notes and Chromebook on the first day.", defaults={"sent_at": timezone.now()})
    return student


def student_self_service_state(user) -> dict:
    _require_student(user)
    student = _ensure_student_records()
    sections = SectionEnrollment.objects.filter(student=student, active=True).select_related("section__course", "section__teacher").order_by("section__meeting_time")
    grades = GradeRecord.objects.filter(student=student).select_related("course").order_by("-posted_at")
    attendance = AttendanceRecord.objects.filter(student=student).select_related("course").order_by("-date")
    threads = MessageThread.objects.filter(student=student).prefetch_related("messages").order_by("-last_message_at")

    return {
        "student": {"id": str(student.id), "student_number": student.student_number, "name": f"{student.first_name} {student.last_name}", "grade": student.current_grade_level.code if student.current_grade_level else ""},
        "schedule": [{"section": row.section.name_override or row.section.section_code, "course": row.section.course.name, "room": row.section.room, "days": row.section.meeting_days, "time": row.section.meeting_time, "teacher": str(row.section.teacher) if row.section.teacher else ""} for row in sections],
        "learning_tasks": [{"assignment": row.assignment_name, "course": row.course.name if row.course else "", "category": row.category, "score": str(row.score) if row.score is not None else None, "score_max": str(row.score_max) if row.score_max is not None else None, "letter_grade": row.letter_grade, "feedback": row.notes_public} for row in grades],
        "attendance": [{"date": row.date.isoformat(), "course": row.course.name if row.course else "School Day", "status": row.status} for row in attendance],
        "communications": [{"subject": thread.subject, "messages": [message.body for message in thread.messages.all()]} for thread in threads],
        "privileged_actions": {"grading": False, "admissions": False, "finance_admin": False, "staff_admin": False, "tenant_admin": False},
    }
