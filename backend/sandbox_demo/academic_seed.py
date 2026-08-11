from __future__ import annotations

from academics.models import (
    Course,
    CurriculumSource,
    Lesson,
    LessonPlan,
    LessonResource,
    Section,
    TeacherAssignment,
    Unit,
)
from core.models import School, UserAccount


HERITAGE_SCHOOL_ID = "19801b59-8c05-4c84-9312-5d792e4e839d"
TEACHER_USERNAME = "teacher.lower@heritage.example.org"
DEMO_COURSE_CODE = "HCA-DEMO-ELA5"
DEMO_TERM_CODE = "2026-FALL"
DEMO_CURRICULUM_SOURCE = "BJU Press"
DEMO_UNIT_TITLE = "Language and Literature Foundations"
DEMO_LESSON_TITLE = "Narrative Voice and Biblical Worldview"


def reset_heritage_teacher_academics() -> None:
    """Clear mutable teacher-demo records before the flagship user/staff reset runs."""
    sections = Section.objects.filter(
        school_id=HERITAGE_SCHOOL_ID,
        course__code=DEMO_COURSE_CODE,
        term=DEMO_TERM_CODE,
    )
    LessonPlan.objects.filter(section__in=sections, school_id=HERITAGE_SCHOOL_ID).delete()
    TeacherAssignment.objects.filter(section__in=sections, school_id=HERITAGE_SCHOOL_ID).delete()
    LessonResource.objects.filter(
        school_id=HERITAGE_SCHOOL_ID,
        lesson__unit__course__code=DEMO_COURSE_CODE,
    ).delete()


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

    curriculum_source, _ = CurriculumSource.objects.update_or_create(
        school_id=school.id,
        name=DEMO_CURRICULUM_SOURCE,
        defaults={
            "source_type": "publisher",
            "reference_link": "https://www.bjupress.com/",
            "description": "Publisher reference metadata only; no licensed content is embedded in the CROWN sandbox.",
        },
    )
    unit, _ = Unit.objects.update_or_create(
        school_id=school.id,
        course=course,
        title=DEMO_UNIT_TITLE,
        defaults={
            "curriculum_source": curriculum_source,
            "description": "Fictional Heritage Grade 5 English unit for sandbox instructional workflow proof.",
            "sequence_order": 1,
        },
    )
    lesson, _ = Lesson.objects.update_or_create(
        school_id=school.id,
        unit=unit,
        title=DEMO_LESSON_TITLE,
        defaults={
            "instructional_notes": "Use this fictional lesson to demonstrate authorized teacher planning and resource linking.",
        },
    )

    return {
        "teacher_course_id": str(course.id),
        "teacher_section_id": str(section.id),
        "teacher_section_code": DEMO_COURSE_CODE,
        "teacher_username": teacher.username,
        "teacher_curriculum_source_id": str(curriculum_source.id),
        "teacher_unit_id": str(unit.id),
        "teacher_lesson_id": str(lesson.id),
    }
