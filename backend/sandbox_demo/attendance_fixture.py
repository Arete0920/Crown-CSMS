from __future__ import annotations

import uuid

from academics.models import Course as AcademicCourse
from academics.models import Enrollment as AcademicEnrollment
from academics.models import Section as AcademicSection
from core.models import Student as CoreStudent, StudentIdentityLink
from households.models import Household, Student as CompatibilityStudent


ATTENDANCE_SANDBOX_NAMESPACE = uuid.UUID("f7fca0f4-1541-420f-910e-4f4bf75e285a")


def ensure_section_attendance_identity(
    *,
    core_student: CoreStudent,
    course_code: str,
    course_name: str,
    grade_band: str,
    term_code: str = "2026-FALL",
    teacher_name: str = "Eleanor Lower",
    evidence_reference: str,
) -> tuple[CompatibilityStudent, AcademicSection]:
    """Ensure one deterministic, same-school sandbox identity bridge and section.

    This is sandbox fixture plumbing only. It does not infer identity from names,
    email, or coincident UUIDs. The explicit VERIFIED StudentIdentityLink created
    here is the authority connecting canonical AttendanceRecord.student to the
    compatibility student used by academics.Enrollment.
    """
    # Callers may have just created the canonical student with a string UUID in
    # school_id. Reload the FK so StudentIdentityLink.clean() compares typed IDs.
    core_student.refresh_from_db(fields=["school"])
    school = core_student.school
    school_id = school.id
    household_id = uuid.uuid5(
        ATTENDANCE_SANDBOX_NAMESPACE,
        f"household:{school_id}:{core_student.student_number}",
    )
    compatibility_id = uuid.uuid5(
        ATTENDANCE_SANDBOX_NAMESPACE,
        f"student:{school_id}:{core_student.student_number}",
    )
    section_id = uuid.uuid5(
        ATTENDANCE_SANDBOX_NAMESPACE,
        f"section:{school_id}:{course_code}:{term_code}",
    )

    household, _ = Household.objects.update_or_create(
        id=household_id,
        defaults={
            "school_id": school_id,
            "name": f"{core_student.student_number} Attendance Sandbox",
            "is_active": True,
        },
    )
    compatibility_student, _ = CompatibilityStudent.objects.update_or_create(
        id=compatibility_id,
        defaults={
            "school_id": school_id,
            "household": household,
            "account": None,
            "first_name": core_student.first_name,
            "last_name": core_student.last_name,
            "grade_level": grade_band,
            "is_active": True,
        },
    )

    StudentIdentityLink.objects.update_or_create(
        core_student=core_student,
        defaults={
            "school": school,
            "compatibility_student": compatibility_student,
            "source": StudentIdentityLink.SOURCE_RECONCILIATION,
            "verification_status": StudentIdentityLink.STATUS_VERIFIED,
            "evidence_reference": evidence_reference,
        },
    )

    course, _ = AcademicCourse.objects.update_or_create(
        school_id=school_id,
        code=course_code,
        defaults={"name": course_name},
    )
    section, _ = AcademicSection.objects.update_or_create(
        id=section_id,
        defaults={
            "school_id": school_id,
            "course": course,
            "term": term_code,
            "term_ref": None,
            "teacher": None,
            "teacher_name": teacher_name,
            "grade_band": grade_band,
        },
    )
    AcademicEnrollment.objects.update_or_create(
        school_id=school_id,
        section=section,
        student=compatibility_student,
        defaults={},
    )
    return compatibility_student, section
