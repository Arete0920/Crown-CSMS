import pytest
from django.core.exceptions import ValidationError

from academics.models import Assignment, AssignmentCategory, Course, Section
from core.models import School
from gradebook.models import GradeEntry
from households.models import Household, Student


pytestmark = pytest.mark.django_db


def _school_graph(name):
    school = School.objects.create(name=name)
    course = Course.objects.create(
        school_id=school.id,
        code=f"{name[:3].upper()}-101",
        name="Course",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term="2026-FALL",
    )
    category = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Tests",
        weight_percent=100,
    )
    assignment = Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=category,
        name="Exam",
        points_possible=100,
    )
    household = Household.objects.create(
        school_id=school.id,
        name=f"{name} Household",
    )
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Student",
        last_name=name,
        grade_level="9",
    )
    return school, section, assignment, student


def test_same_school_grade_entry_is_allowed():
    school, section, assignment, student = _school_graph("Alpha")

    grade = GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment=assignment,
        assignment_name=assignment.name,
        points_earned=95,
        points_possible=100,
    )

    assert grade.pk is not None


def test_same_school_grade_entry_accepts_string_school_id():
    school, section, assignment, student = _school_graph("Alpha")

    grade = GradeEntry.objects.create(
        school_id=str(school.id),
        section=section,
        student=student,
        assignment=assignment,
        assignment_name=assignment.name,
        points_earned=95,
        points_possible=100,
    )

    assert grade.pk is not None
    assert grade.school_id == school.id


def test_same_school_grade_entry_accepts_string_foreign_key_ids():
    school, section, assignment, student = _school_graph("Alpha")

    grade = GradeEntry.objects.create(
        school_id=str(school.id),
        section_id=str(section.id),
        student_id=str(student.id),
        assignment_id=str(assignment.id),
        assignment_name=assignment.name,
        points_earned=95,
        points_possible=100,
    )

    assert grade.pk is not None
    assert grade.section_id == section.id
    assert grade.assignment_id == assignment.id


@pytest.mark.parametrize("relation", ["section", "student", "assignment"])
def test_cross_school_grade_entry_relation_is_rejected(relation):
    school_a, section_a, assignment_a, student_a = _school_graph("Alpha")
    _, section_b, assignment_b, student_b = _school_graph("Beta")
    values = {
        "school_id": school_a.id,
        "section": section_a,
        "student": student_a,
        "assignment": assignment_a,
        "assignment_name": "Exam",
        "points_possible": 100,
    }
    values[relation] = {
        "section": section_b,
        "student": student_b,
        "assignment": assignment_b,
    }[relation]

    with pytest.raises(ValidationError, match="same school"):
        GradeEntry.objects.create(**values)


def test_assignment_must_belong_to_grade_entry_section():
    school, section_a, _, student = _school_graph("Alpha")
    course = Course.objects.create(
        school_id=school.id,
        code="ALT-101",
        name="Alternate",
    )
    section_b = Section.objects.create(
        school_id=school.id,
        course=course,
        term="2026-FALL",
    )
    category = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section_b,
        name="Tests",
        weight_percent=100,
    )
    assignment_b = Assignment.objects.create(
        school_id=school.id,
        section=section_b,
        category=category,
        name="Other Exam",
        points_possible=100,
    )

    with pytest.raises(ValidationError, match="selected section"):
        GradeEntry.objects.create(
            school_id=school.id,
            section=section_a,
            student=student,
            assignment=assignment_b,
            assignment_name=assignment_b.name,
            points_possible=100,
        )


def test_cross_school_repoint_update_is_rejected():
    school, section, assignment, student = _school_graph("Alpha")
    _, _, _, other_student = _school_graph("Beta")
    grade = GradeEntry.objects.create(
        school_id=school.id,
        section=section,
        student=student,
        assignment=assignment,
        assignment_name=assignment.name,
        points_possible=100,
    )

    grade.student = other_student
    with pytest.raises(ValidationError, match="same school"):
        grade.save(update_fields=["student", "updated_at"])
