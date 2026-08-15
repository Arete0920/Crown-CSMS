from __future__ import annotations

import uuid
from datetime import date, time

from django.conf import settings
from django.utils import timezone

from academics.models import Course as AcademicCourse
from academics.models import Enrollment as AcademicEnrollment
from academics.models import Section as AcademicSection
from academics.models import Term as AcademicTerm
from bell_schedule_wizard.models import BellSchedule, DayTemplate, PeriodBlock
from core.models import AcademicYear, Family, GradeLevel, Student, StudentIdentityLink, UserAccount
from crown_api.models import AttendanceRecord, GradeRecord
from crown_api.models_academics_core import Course as LegacyCourse
from crown_api.models_comms_core import Message, MessageThread
from crown_api.models_households import Household as CommsHousehold, Person
from households.models import Household as AcademicHousehold
from households.models import Student as AcademicStudent
from room_setup_wizard.models import Room
from section_scheduler_wizard.models import SectionPlacement

from .catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS


STUDENT_EMAIL = SANDBOX_PERSONAS["student"].email
SCHOOL_ID = SANDBOX_SCHOOLS["heritage-core"].id
STUDENT_NUMBER = "HCA-STUDENT-AVERY"
TERM_CODE = "2026-FALL-STUDENT"
COURSE_CODE = "HCA-STU-ELA7"
SANDBOX_SECTION_NAMESPACE = uuid.UUID("3c880801-d8c8-4e8c-9dca-e4d21e399ed8")


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


def _canonical_schedule_fixture(user: UserAccount) -> AcademicStudent:
    """Create the sandbox compatibility identity and canonical schedule once."""
    school_id = user.school_id
    academic_year = (
        AcademicYear.objects.filter(school_id=school_id, is_current=True)
        .order_by("start_date", "id")
        .first()
    )
    if academic_year is None:
        academic_year = AcademicYear.objects.create(
            school_id=school_id,
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 6, 30),
            is_current=True,
        )

    household, _ = AcademicHousehold.objects.get_or_create(
        school_id=school_id,
        name="Reed Family Student Sandbox",
        defaults={
            "address1": "100 Demo Lane",
            "city": "Fairview",
            "state": "PA",
            "postal_code": "19000",
            "is_active": True,
        },
    )
    academic_student_id = uuid.uuid5(SANDBOX_SECTION_NAMESPACE, f"student:{user.id}")
    academic_student, academic_student_created = AcademicStudent.objects.get_or_create(
        id=academic_student_id,
        defaults={
            "school_id": school_id,
            "household": household,
            "account": None,
            "first_name": "Avery",
            "last_name": "Reed",
            "grade_level": "7",
            "is_active": True,
        },
    )
    if not academic_student_created and (
        str(academic_student.school_id) != str(school_id)
        or academic_student.household_id != household.id
        or academic_student.account_id is not None
    ):
        raise SandboxStudentError("canonical_student_authority_mismatch")

    course, _ = AcademicCourse.objects.get_or_create(
        school_id=school_id,
        code=COURSE_CODE,
        defaults={"name": "Grade 7 English Language Arts"},
    )
    term, term_created = AcademicTerm.objects.get_or_create(
        academic_year=academic_year,
        code=TERM_CODE,
        defaults={
            "school_id": school_id,
            "name": "Fall 2026",
            "school_year": academic_year.name,
            "start_date": date(2026, 8, 15),
            "end_date": date(2026, 12, 18),
            "ordering": 1,
            "active": True,
        },
    )
    if not term_created:
        if str(term.school_id) != str(school_id):
            raise SandboxStudentError("canonical_term_authority_mismatch")
        term_values = {
            "name": "Fall 2026",
            "school_year": academic_year.name,
            "start_date": date(2026, 8, 15),
            "end_date": date(2026, 12, 18),
            "ordering": 1,
            "active": True,
        }
        changed_fields = []
        for field_name, expected in term_values.items():
            if getattr(term, field_name) != expected:
                setattr(term, field_name, expected)
                changed_fields.append(field_name)
        if changed_fields:
            term.save(update_fields=changed_fields)

    section_id = uuid.uuid5(
        SANDBOX_SECTION_NAMESPACE,
        f"{school_id}:{academic_year.id}:{COURSE_CODE}:01",
    )
    section, section_created = AcademicSection.objects.get_or_create(
        id=section_id,
        defaults={
            "school_id": school_id,
            "course": course,
            "term_ref": term,
            "term": term.code,
            "teacher": None,
            "teacher_name": "Eleanor Lower",
            "grade_band": "7",
        },
    )
    if not section_created:
        if (
            str(section.school_id) != str(school_id)
            or section.course_id != course.id
            or section.term_ref_id != term.id
            or section.teacher_id is not None
        ):
            raise SandboxStudentError("canonical_section_authority_mismatch")
        section_values = {
            "term": term.code,
            "teacher_name": "Eleanor Lower",
            "grade_band": "7",
        }
        changed_fields = []
        for field_name, expected in section_values.items():
            if getattr(section, field_name) != expected:
                setattr(section, field_name, expected)
                changed_fields.append(field_name)
        if changed_fields:
            section.save(update_fields=changed_fields)

    enrollment, enrollment_created = AcademicEnrollment.objects.get_or_create(
        section=section,
        student=academic_student,
        defaults={"school_id": school_id},
    )
    if not enrollment_created and str(enrollment.school_id) != str(school_id):
        raise SandboxStudentError("canonical_enrollment_authority_mismatch")

    room, _ = Room.objects.get_or_create(
        school_id=school_id,
        code="207",
        defaults={"name": "Room 207", "capacity": 30, "is_active": True},
    )
    bell, _ = BellSchedule.objects.get_or_create(
        school_id=school_id,
        academic_year=academic_year,
        name="Student Sandbox Bell",
        defaults={"schedule_mode": "DAY_TEMPLATES", "is_active": False},
    )
    day_template, _ = DayTemplate.objects.get_or_create(
        schedule=bell,
        template_code="MTWTF",
        defaults={"ordering": 1},
    )
    block, _ = PeriodBlock.objects.get_or_create(
        template=day_template,
        code="ELA7",
        defaults={
            "label": "09:15-10:05",
            "start_time": time(9, 15),
            "end_time": time(10, 5),
            "ordering": 1,
            "is_instructional": True,
            "is_lunch": False,
            "is_break": False,
        },
    )
    placement, placement_created = SectionPlacement.objects.get_or_create(
        section=section,
        day_template=day_template,
        period_block=block,
        defaults={
            "school_id": school_id,
            "academic_year": academic_year,
            "room": room,
            "is_active": True,
        },
    )
    if not placement_created:
        if (
            str(placement.school_id) != str(school_id)
            or placement.academic_year_id != academic_year.id
            or placement.room_id != room.id
        ):
            raise SandboxStudentError("canonical_placement_authority_mismatch")
        if not placement.is_active:
            placement.is_active = True
            placement.save(update_fields=["is_active"])
    return academic_student


def _ensure_student_records(user: UserAccount) -> tuple[Student, AcademicStudent]:
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
    student, _ = Student.objects.get_or_create(
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
    academic_student = _canonical_schedule_fixture(user)

    StudentIdentityLink.objects.update_or_create(
        core_student=student,
        defaults={
            "school_id": SCHOOL_ID,
            "compatibility_student": academic_student,
            "source": StudentIdentityLink.SOURCE_RECONCILIATION,
            "verification_status": StudentIdentityLink.STATUS_VERIFIED,
            "evidence_reference": f"sandbox:heritage:student-self-service:{STUDENT_NUMBER}",
        },
    )
    enrollment = AcademicEnrollment.objects.select_related("section").get(
        school_id=SCHOOL_ID,
        student=academic_student,
    )

    # Grade compatibility fixtures remain course-scoped; Attendance is canonical section-scoped.
    course, _ = LegacyCourse.objects.get_or_create(
        course_code=COURSE_CODE,
        defaults={"name": "Grade 7 English Language Arts", "term": "Fall 2026", "active": True},
    )
    teacher, _ = Person.objects.get_or_create(
        email="teacher.lower@heritage.example.org",
        defaults={"first_name": "Eleanor", "last_name": "Lower", "phone": "555-0110"},
    )
    AttendanceRecord.objects.filter(
        student=student,
        date=date(2026, 8, 10),
        section__isnull=True,
    ).delete()
    AttendanceRecord.objects.update_or_create(
        student=student,
        section=enrollment.section,
        date=date(2026, 8, 10),
        defaults={
            "course": None,
            "status": AttendanceRecord.STATUS_PRESENT,
            "notes_public": "Heritage sandbox section-aware attendance.",
        },
    )
    GradeRecord.objects.get_or_create(
        student=student,
        course=course,
        period="Q1",
        assignment_name="Summer Reading Reflection",
        defaults={
            "category": "Writing",
            "score": 92,
            "score_max": 100,
            "letter_grade": "A-",
            "posted_at": timezone.now(),
            "notes_public": "Strong textual evidence and clear reflection.",
        },
    )
    GradeRecord.objects.get_or_create(
        student=student,
        course=course,
        period="Q1",
        assignment_name="Vocabulary Check 1",
        defaults={
            "category": "Assessment",
            "score": 18,
            "score_max": 20,
            "letter_grade": "A-",
            "posted_at": timezone.now(),
            "notes_public": "Review two missed terms before Friday.",
        },
    )
    comms_household, _ = CommsHousehold.objects.get_or_create(
        household_name="Reed Family Student Sandbox",
        defaults={
            "primary_address_line1": "100 Demo Lane",
            "primary_city": "Fairview",
            "primary_state": "PA",
            "primary_postal_code": "19000",
        },
    )
    thread, _ = MessageThread.objects.get_or_create(
        household=comms_household,
        student=student,
        subject="Grade 7 Welcome and First Week",
        defaults={
            "thread_type": "ANNOUNCEMENT",
            "created_by": teacher,
            "last_message_at": timezone.now(),
        },
    )
    Message.objects.get_or_create(
        thread=thread,
        sender_person=teacher,
        body="Welcome to Grade 7. Bring your summer reading notes and Chromebook on the first day.",
        defaults={"sent_at": timezone.now()},
    )
    return student, academic_student


def _schedule_row(enrollment: AcademicEnrollment) -> dict:
    section = enrollment.section
    placement = (
        section.schedule_placements.filter(is_active=True)
        .select_related("room", "day_template", "period_block")
        .order_by("day_template__ordering", "period_block__ordering", "id")
        .first()
    )
    return {
        "section": str(section.id),
        "course": section.course.name,
        "room": placement.room.code if placement and placement.room_id else "",
        "days": placement.day_template.template_code if placement else "",
        "time": placement.period_block.label if placement else "",
        "teacher": section.teacher_name,
    }


def student_self_service_state(user) -> dict:
    user = _require_student(user)
    student, academic_student = _ensure_student_records(user)
    sections = (
        AcademicEnrollment.objects.filter(student=academic_student, school_id=SCHOOL_ID)
        .select_related("section__course")
        .order_by("section__course__code", "section__id")
    )
    grades = GradeRecord.objects.filter(student=student).select_related("course").order_by("-posted_at")
    attendance = (
        AttendanceRecord.objects.filter(student=student, section__isnull=False)
        .select_related("section__course")
        .order_by("-date", "section_id")
    )
    threads = MessageThread.objects.filter(student=student).prefetch_related("messages").order_by("-last_message_at")

    return {
        "student": {"id": str(student.id), "student_number": student.student_number, "name": f"{student.first_name} {student.last_name}", "grade": student.current_grade_level.code if student.current_grade_level else ""},
        "schedule": [_schedule_row(row) for row in sections],
        "learning_tasks": [{"assignment": row.assignment_name, "course": row.course.name if row.course else "", "category": row.category, "score": str(row.score) if row.score is not None else None, "score_max": str(row.score_max) if row.score_max is not None else None, "letter_grade": row.letter_grade, "feedback": row.notes_public} for row in grades],
        "attendance": [{"date": row.date.isoformat(), "section_id": str(row.section_id), "course": row.section.course.name, "status": row.status} for row in attendance],
        "communications": [{"subject": thread.subject, "messages": [message.body for message in thread.messages.all()]} for thread in threads],
        "privileged_actions": {"grading": False, "admissions": False, "finance_admin": False, "staff_admin": False, "tenant_admin": False},
    }
