import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from academics.models import (
    Assignment,
    AssignmentCategory,
    Course,
    Enrollment,
    Section,
    Submission,
)
from core.models import School
from households.models import Household, Student


pytestmark = pytest.mark.django_db
User = get_user_model()


def _school_graph(name):
    school = School.objects.create(name=name)
    household = Household.objects.create(school_id=school.id, name=f"{name} Household")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Bulk",
        last_name=name,
        grade_level="5",
    )
    course = Course.objects.create(
        school_id=school.id,
        code=f"BULK-{uuid.uuid4().hex[:8]}",
        name=f"{name} Course",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term="2026-FALL",
        teacher_name="Original",
    )
    enrollment = Enrollment.objects.create(
        school_id=school.id,
        section=section,
        student=student,
    )
    category = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name=f"Category {uuid.uuid4().hex[:8]}",
        weight_percent=Decimal("100.00"),
    )
    assignment = Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=category,
        name=f"Assignment {uuid.uuid4().hex[:8]}",
        points_possible=Decimal("100.00"),
    )
    return {
        "school": school,
        "student": student,
        "course": course,
        "section": section,
        "enrollment": enrollment,
        "category": category,
        "assignment": assignment,
    }


def test_queryset_update_allows_non_authority_fields():
    graph = _school_graph("Safe Queryset")
    updated = Section.objects.filter(pk=graph["section"].pk).update(teacher_name="Updated")
    graph["section"].refresh_from_db()
    assert updated == 1
    assert graph["section"].teacher_name == "Updated"


def test_queryset_update_allows_nullable_authority_clear():
    graph = _school_graph("Nullable Clear")
    teacher = User.objects.create_user(
        username=f"nullable-clear-{uuid.uuid4()}",
        password="pass12345!",
        school=graph["school"],
    )
    graph["section"].teacher = teacher
    graph["section"].save(update_fields=["teacher"])

    updated = Section.objects.filter(pk=graph["section"].pk).update(teacher=None)

    graph["section"].refresh_from_db()
    assert updated == 1
    assert graph["section"].teacher_id is None


def test_deletion_collector_can_clear_nullable_authority_relation():
    graph = _school_graph("Deletion Collector")
    teacher = User.objects.create_user(
        username=f"deletion-collector-{uuid.uuid4()}",
        password="pass12345!",
        school=graph["school"],
    )
    graph["section"].teacher = teacher
    graph["section"].save(update_fields=["teacher"])

    teacher.delete()

    graph["section"].refresh_from_db()
    assert graph["section"].teacher_id is None


def test_queryset_update_rejects_authority_fields_without_persistence():
    graph_a = _school_graph("Queryset A")
    graph_b = _school_graph("Queryset B")
    with pytest.raises(ValidationError, match="QuerySet.update"):
        Section.objects.filter(pk=graph_a["section"].pk).update(course_id=graph_b["course"].pk)
    graph_a["section"].refresh_from_db()
    assert graph_a["section"].course_id == graph_a["course"].pk
    assert graph_a["section"].school_id == graph_a["school"].pk


def test_bulk_create_accepts_valid_same_school_sections():
    graph = _school_graph("Bulk Create Valid")
    rows = [
        Section(
            school_id=graph["school"].id,
            course=graph["course"],
            term="2027-SPRING",
            teacher_name=f"Teacher {index}",
        )
        for index in range(2)
    ]
    created = Section.objects.bulk_create(rows)
    assert len(created) == 2
    assert Section.objects.filter(school_id=graph["school"].id, term="2027-SPRING").count() == 2


def test_bulk_create_rejects_cross_school_batch_atomically():
    graph_a = _school_graph("Bulk Create A")
    graph_b = _school_graph("Bulk Create B")
    before = Section.objects.count()
    rows = [
        Section(school_id=graph_a["school"].id, course=graph_a["course"], term="2027-SPRING"),
        Section(school_id=graph_a["school"].id, course=graph_b["course"], term="2027-SPRING"),
    ]
    with pytest.raises(ValidationError):
        Section.objects.bulk_create(rows)
    assert Section.objects.count() == before


def test_bulk_update_accepts_valid_same_school_authority_change():
    graph = _school_graph("Bulk Update Valid")
    replacement_course = Course.objects.create(
        school_id=graph["school"].id,
        code="VALID-REPLACEMENT",
        name="Replacement",
    )
    row = graph["section"]
    row.course = replacement_course
    updated = Section.objects.bulk_update([row], ["course"])
    row.refresh_from_db()
    assert updated == 1
    assert row.course_id == replacement_course.id


def test_bulk_update_rejects_cross_school_authority_change_atomically():
    graph_a = _school_graph("Bulk Update A")
    graph_b = _school_graph("Bulk Update B")
    valid_replacement = Course.objects.create(
        school_id=graph_a["school"].id,
        code="VALID-A",
        name="Valid A",
    )
    first = graph_a["section"]
    second_course = Course.objects.create(
        school_id=graph_a["school"].id,
        code="SECOND-A",
        name="Second A",
    )
    second = Section.objects.create(
        school_id=graph_a["school"].id,
        course=second_course,
        term="2026-FALL",
    )
    original_first_course = first.course_id
    original_second_course = second.course_id
    first.course = valid_replacement
    second.course = graph_b["course"]
    with pytest.raises(ValidationError):
        Section.objects.bulk_update([first, second], ["course"])
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.course_id == original_first_course
    assert second.course_id == original_second_course


def test_bulk_create_submission_infers_school_and_validates_lineage():
    graph = _school_graph("Submission Bulk Valid")
    row = Submission(
        assignment=graph["assignment"],
        enrollment=graph["enrollment"],
    )
    Submission.objects.bulk_create([row])
    row.refresh_from_db()
    assert row.school_id == graph["school"].id


def test_bulk_create_submission_rejects_wrong_section_lineage():
    graph = _school_graph("Submission Bulk Lineage")
    other_course = Course.objects.create(
        school_id=graph["school"].id,
        code="OTHER-COURSE",
        name="Other Course",
    )
    other_section = Section.objects.create(
        school_id=graph["school"].id,
        course=other_course,
        term="2026-FALL",
    )
    other_enrollment = Enrollment.objects.create(
        school_id=graph["school"].id,
        section=other_section,
        student=graph["student"],
    )
    row = Submission(
        assignment=graph["assignment"],
        enrollment=other_enrollment,
    )
    with pytest.raises(ValidationError, match="assignment section"):
        Submission.objects.bulk_create([row])
    assert not Submission.objects.filter(pk=row.pk).exists()
