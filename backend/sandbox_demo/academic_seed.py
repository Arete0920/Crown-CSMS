from __future__ import annotations

from academics.models import Course, LessonPlan, Section, TeacherAssignment
from core.models import School, UserAccount


HERITAGE_SCHOOL_ID = "19801b59-8c05-4c84-9312-5d792e4e839d"
TEACHER_USERNAME = "teacher.lower@heritage.example.org"
DEMO_COURSE_CODE = "HCA-DEMO-ELA5"
DEMO_TERM_CODE = "2026-FALL"


def reset_heritage_teacher_academics() -> None:
    """Clear mutable teacher-demo records before the flagship user/staff reset runs."""
    sections = Section.objects.filter(
        school_id=HERITAGE_SCHOOL_ID,
        course__code=DEMO_COURSE_CODE,
        term=DEMO_TERM_CODE,
    )
    LessonPlan.objects.filter(section__in=sections, school_id=HERITAGE_SCHOOL_ID).delete()
    TeacherAssignment.objects.filter(section__in=sections, school_id=HERITAGE_SCHOOL_ID).delete()


def seed_heritage_teacher_academics() -> dict:
    """Create deterministic, teacher-owned instructional data for the flagship sandbox."""
    school = School.objects.get(pk=HERITAGE_SCHOOL_ID)
    teacher = UserAccount.objects.get(school=school, username=TEACHER_USERNAME)
    if teacher.staff_id is None:
        raise RuntimeError("Heritage teacher sandbox persona is missing its Staff record.")

    course, _ = Course.objects.update_or_create(
        school_id=school.id,
        code=DEMO_COURSE_CODE,
        defaults={
            "name": "Grade 5 English Language Arts",
            "department": "English Language Arts",
            "credits": 1,
        },
    )
    section, _ = Section.objects.update_or_create(
        school_id=school.id,
        course=course,
        term=DEMO_TERM_CODE,
        defaults={
            "teacher": teacher,
            "teacher_name": "Eleanor Lower",
            "grade_band": "5",
            "term_ref": None,
        },
    )
    TeacherAssignment.objects.update_or_create(
        school_id=school.id,
        section=section,
        staff_id=teacher.staff_id,
        defaults={},
    )

    return {
        "teacher_course_id": str(course.id),
        "teacher_section_id": str(section.id),
        "teacher_section_code": DEMO_COURSE_CODE,
        "teacher_username": teacher.username,
    }
