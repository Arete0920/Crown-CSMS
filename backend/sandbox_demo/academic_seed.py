from __future__ import annotations

import uuid
from datetime import date

from academics.models import (
    Assignment,
    AssignmentCategory,
    Course,
    CurriculumSource,
    Enrollment as AcademicEnrollment,
    Lesson,
    LessonPlan,
    LessonResource,
    Section,
    TeacherAssignment,
    Unit,
)
from core.models import (
    Family,
    GradeLevel,
    School,
    Student as CoreStudent,
    StudentIdentityLink,
    UserAccount,
)
from households.models import Household, Student as HouseholdStudent


HERITAGE_SCHOOL_ID = "19801b59-8c05-4c84-9312-5d792e4e839d"
TEACHER_USERNAME = "teacher.lower@heritage.example.org"
DEMO_COURSE_CODE = "HCA-DEMO-ELA5"
DEMO_TERM_CODE = "2026-FALL"
DEMO_CURRICULUM_SOURCE = "BJU Press"
DEMO_UNIT_TITLE = "Language and Literature Foundations"
DEMO_LESSON_TITLE = "Narrative Voice and Biblical Worldview"
DEMO_CLASSROOM_HOUSEHOLD = "Teacher Classroom Demo Family"
DEMO_CATEGORY_NAME = "Classwork"
DEMO_STUDENTS = (
    ("Caleb", "Demo", "HCA-TCHR-001"),
    ("Naomi", "Demo", "HCA-TCHR-002"),
)


def _demo_student_ids() -> list[uuid.UUID]:
    school_namespace = uuid.UUID(HERITAGE_SCHOOL_ID)
    return [uuid.uuid5(school_namespace, student_number) for _, _, student_number in DEMO_STUDENTS]


def reset_heritage_teacher_academics() -> None:
    """Clear mutable teacher-demo records before the flagship user/staff reset runs."""
    sections = Section.objects.filter(
        school_id=HERITAGE_SCHOOL_ID,
        course__code=DEMO_COURSE_CODE,
        term=DEMO_TERM_CODE,
    )
    Assignment.objects.filter(section__in=sections, school_id=HERITAGE_SCHOOL_ID).delete()
    AssignmentCategory.objects.filter(section__in=sections, school_id=HERITAGE_SCHOOL_ID).delete()
    AcademicEnrollment.objects.filter(section__in=sections, school_id=HERITAGE_SCHOOL_ID).delete()
    LessonPlan.objects.filter(section__in=sections, school_id=HERITAGE_SCHOOL_ID).delete()
    TeacherAssignment.objects.filter(section__in=sections, school_id=HERITAGE_SCHOOL_ID).delete()
    LessonResource.objects.filter(
        school_id=HERITAGE_SCHOOL_ID,
        lesson__unit__course__code=DEMO_COURSE_CODE,
    ).delete()

    demo_student_ids = _demo_student_ids()
    StudentIdentityLink.objects.filter(
        school_id=HERITAGE_SCHOOL_ID,
        core_student_id__in=demo_student_ids,
    ).delete()

    household_ids = list(
        Household.objects.filter(
            school_id=HERITAGE_SCHOOL_ID,
            name=DEMO_CLASSROOM_HOUSEHOLD,
        ).values_list("id", flat=True)
    )
    if household_ids:
        HouseholdStudent.objects.filter(
            school_id=HERITAGE_SCHOOL_ID,
            household_id__in=household_ids,
        ).delete()
        Household.objects.filter(id__in=household_ids).delete()


def _ensure_teacher_roster(school: School, section: Section) -> list[str]:
    household, _ = Household.objects.update_or_create(
        school_id=school.id,
        name=DEMO_CLASSROOM_HOUSEHOLD,
        defaults={
            "address1": "500 Classroom Lane",
            "city": "Fairview",
            "state": "PA",
            "postal_code": "19000",
            "is_active": True,
        },
    )
    core_family, _ = Family.objects.update_or_create(
        school=school,
        family_name=DEMO_CLASSROOM_HOUSEHOLD,
        defaults={"status": "ACTIVE"},
    )
    grade = GradeLevel.objects.filter(school=school, code="5").first()
    student_ids = []
    for index, (first_name, last_name, student_number) in enumerate(DEMO_STUDENTS, start=1):
        stable_id = uuid.uuid5(uuid.UUID(HERITAGE_SCHOOL_ID), student_number)
        household_student, _ = HouseholdStudent.objects.update_or_create(
            id=stable_id,
            defaults={
                "school_id": school.id,
                "household": household,
                "first_name": first_name,
                "last_name": last_name,
                "grade_level": "5",
                "is_active": True,
            },
        )
        core_student, _ = CoreStudent.objects.update_or_create(
            id=stable_id,
            defaults={
                "school": school,
                "family": core_family,
                "student_number": student_number,
                "first_name": first_name,
                "last_name": last_name,
                "dob": date(2015, 1, index),
                "status": "ACTIVE",
                "current_grade_level": grade,
            },
        )
        StudentIdentityLink.objects.update_or_create(
            core_student=core_student,
            defaults={
                "school": school,
                "compatibility_student": household_student,
                "source": StudentIdentityLink.SOURCE_RECONCILIATION,
                "verification_status": StudentIdentityLink.STATUS_VERIFIED,
                "evidence_reference": f"sandbox:heritage:teacher-roster:{student_number}",
            },
        )
        AcademicEnrollment.objects.update_or_create(
            school_id=school.id,
            section=section,
            student=household_student,
            defaults={},
        )
        student_ids.append(str(stable_id))
    return student_ids


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
    category, _ = AssignmentCategory.objects.update_or_create(
        school_id=school.id,
        section=section,
        name=DEMO_CATEGORY_NAME,
        defaults={
            "weight_percent": 0,
            "sort_order": 1,
            "is_active": True,
        },
    )
    student_ids = _ensure_teacher_roster(school, section)

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
        "teacher_assignment_category_id": str(category.id),
        "teacher_roster_student_ids": student_ids,
        "teacher_curriculum_source_id": str(curriculum_source.id),
        "teacher_unit_id": str(unit.id),
        "teacher_lesson_id": str(lesson.id),
    }
