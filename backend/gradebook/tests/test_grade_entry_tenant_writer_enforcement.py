import uuid

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

    grade.refresh_from_db()
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

    grade.refresh_from_db()
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



def test_bulk_grade_entry_insert_rejects_cross_school_student():
    school, section, assignment, student = _school_graph("Alpha")
    _, _, _, other_student = _school_graph("Beta")

    records = [
        GradeEntry(
            school_id=school.id,
            section=section,
            student=student,
            assignment=assignment,
            assignment_name="Valid",
            points_earned=80,
            points_possible=100,
        ),
        GradeEntry(
            school_id=school.id,
            section=section,
            student=other_student,
            assignment=assignment,
            assignment_name="Cross school",
            points_earned=90,
            points_possible=100,
        ),
    ]
    with pytest.raises(ValidationError, match="same school"):
        GradeEntry.objects.bulk_create(records)
    assert GradeEntry.objects.count() == 0


def test_bulk_grade_entry_insert_accepts_scoped_student():
    school, section, assignment, student = _school_graph("Alpha")
    inserted = GradeEntry.objects.bulk_create([
        GradeEntry(
            school_id=school.id,
            section=section,
            student=student,
            assignment=assignment,
            assignment_name=assignment.name,
            points_earned=100,
            points_possible=100,
        )
    ])
    assert len(inserted) == 1
    assert GradeEntry.objects.filter(school_id=school.id).count() == 1


def test_grade_entry_queryset_update_rejects_tenant_and_grade_reassignment():
    school, section, assignment, student = _school_graph("Alpha")
    _, _, _, other_student = _school_graph("Beta")
    grade = GradeEntry.objects.create(
        school_id=school.id, section=section, student=student,
        assignment=assignment, assignment_name="Exam",
        points_earned=95, points_possible=100,
    )
    for change in (
        {"student_id": other_student.id},
        {"school_id": other_student.school_id},
        {"points_earned": -5},
    ):
        with pytest.raises(ValidationError, match="protected fields"):
            GradeEntry.objects.filter(pk=grade.pk).update(**change)
    grade.refresh_from_db()
    assert grade.school_id == school.id
    assert grade.student_id == student.id
    assert grade.points_earned == 95


def test_grade_entry_bulk_update_rejects_relational_reassignment():
    school, section, assignment, student = _school_graph("Alpha")
    _, _, _, other_student = _school_graph("Beta")
    grade = GradeEntry.objects.create(
        school_id=school.id, section=section, student=student,
        assignment=assignment, assignment_name="Exam",
        points_earned=95, points_possible=100,
    )
    grade.student = other_student
    with pytest.raises(ValidationError, match="protected fields"):
        GradeEntry.objects.bulk_update([grade], ["student"])
    grade.refresh_from_db()
    assert grade.student_id == student.id


@pytest.mark.parametrize("invalid", [-1, float("nan"), float("inf")])
def test_grade_entry_direct_instance_write_rejects_unsafe_numeric_scores(invalid):
    school, section, assignment, student = _school_graph("Alpha")
    with pytest.raises(ValidationError, match="nonnegative"):
        GradeEntry.objects.create(
            school_id=school.id, section=section, student=student,
            assignment=assignment, assignment_name="Exam",
            points_earned=invalid, points_possible=100,
        )
    assert GradeEntry.objects.count() == 0


def test_grade_entry_bulk_upsert_cannot_bypass_clean():
    school, section, assignment, student = _school_graph("Alpha")
    grade = GradeEntry(
        school_id=school.id, section=section, student=student,
        assignment=assignment, assignment_name="Exam",
        points_earned=80, points_possible=100,
    )
    with pytest.raises(ValidationError, match="bulk upsert"):
        GradeEntry.objects.bulk_create(
            [grade], update_conflicts=True,
            update_fields=["points_earned"],
            unique_fields=["id"],
        )
    assert GradeEntry.objects.count() == 0


def test_grade_entry_bulk_update_allows_non_authority_timestamp():
    """Unprotected maintenance fields remain available to Django bulk_update."""
    from django.utils import timezone

    school, section, assignment, student = _school_graph("Alpha")
    grade = GradeEntry.objects.create(
        school_id=school.id, section=section, student=student,
        assignment=assignment, assignment_name="Exam",
        points_earned=95, points_possible=100,
    )
    grade.updated_at = timezone.now()
    assert GradeEntry.objects.bulk_update([grade], ["updated_at"]) == 1


def test_gradeentry_primary_key_update_is_forbidden():
    school, section, assignment, student = _school_graph("Alpha")
    entry = GradeEntry.objects.create(
        school_id=school.id, section=section, student=student,
        assignment=assignment, assignment_name="Exam",
        points_earned=90, points_possible=100,
    )
    with pytest.raises(ValidationError, match="protected fields"):
        GradeEntry.objects.using("default").filter(pk=entry.pk).update(
            id=uuid.uuid4()
        )
    assert GradeEntry.objects.filter(pk=entry.pk).exists()


def test_cached_student_school_cannot_override_persisted_tenant_authority():
    _, _, _, student_a = _school_graph("Alpha")
    school_b, section_b, assignment_b, _ = _school_graph("Beta")
    student_a.school_id = school_b.id
    entry = GradeEntry(
        school_id=school_b.id, section=section_b, student=student_a,
        assignment=assignment_b, assignment_name="Exam",
        points_earned=90, points_possible=100,
    )
    with pytest.raises(ValidationError, match="same school"):
        entry.save()
    with pytest.raises(ValidationError, match="same school"):
        GradeEntry.objects.using("default").bulk_create([entry])
    assert GradeEntry.objects.count() == 0


def test_cached_assignment_section_cannot_override_persisted_section():
    school, section_a, assignment, student = _school_graph("Alpha")
    section_b = Section.objects.create(
        school_id=school.id, course=section_a.course, term="2027-SPRING"
    )
    assignment.section_id = section_b.id
    with pytest.raises(ValidationError, match="selected section"):
        GradeEntry.objects.create(
            school_id=school.id, section=section_b, student=student,
            assignment=assignment, assignment_name="Exam",
            points_earned=90, points_possible=100,
        )
    assert GradeEntry.objects.count() == 0


def test_null_grade_and_generator_fields_bulk_update_remain_supported():
    from django.utils import timezone

    school, section, assignment, student = _school_graph("Alpha")
    (entry,) = GradeEntry.objects.using("default").bulk_create([
        GradeEntry(
            school_id=school.id, section=section, student=student,
            assignment=assignment, assignment_name="Missing",
            points_earned=None, points_possible=100,
        )
    ])
    assert GradeEntry.objects.get(pk=entry.pk).points_earned is None
    entry.updated_at = timezone.now()
    field_names = (field for field in ("updated_at",))
    assert GradeEntry.objects.bulk_update([entry], field_names) == 1
    entry.refresh_from_db()
    assert entry.points_earned is None


def test_bulk_update_rejects_unsafe_score_via_database_alias():
    school, section, assignment, student = _school_graph("Alpha")
    entry = GradeEntry.objects.create(
        school_id=school.id, section=section, student=student,
        assignment=assignment, assignment_name="Exam",
        points_earned=90, points_possible=100,
    )
    entry.points_earned = -1
    with pytest.raises(ValidationError, match="protected fields"):
        GradeEntry.objects.using("default").bulk_update(
            [entry], ["points_earned"]
        )
    assert GradeEntry.objects.get(pk=entry.pk).points_earned == 90
