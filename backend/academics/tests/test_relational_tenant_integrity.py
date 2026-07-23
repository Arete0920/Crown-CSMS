import uuid
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from academics.models import (
    Assignment,
    AssignmentCategory,
    Course,
    Enrollment,
    Section,
    Submission,
    TeacherAssignment,
)
from core.models import School, Staff
from households.models import Household, Student


pytestmark = pytest.mark.django_db


def _school_graph(name):
    school = School.objects.create(name=name)
    household = Household.objects.create(school_id=school.id, name=f"{name} Household")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Test",
        last_name=name,
        grade_level="5",
    )
    staff = Staff.objects.create(
        school=school,
        first_name="Teacher",
        last_name=name,
        email=f"{uuid.uuid4().hex[:8]}@example.com",
        role_type="TEACHER",
    )
    course = Course.objects.create(
        school_id=school.id,
        code=f"COURSE-{uuid.uuid4().hex[:8]}",
        name=f"{name} Course",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term="2026-FALL",
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
        "staff": staff,
        "section": section,
        "enrollment": enrollment,
        "category": category,
        "assignment": assignment,
    }


def test_same_school_relational_graph_is_accepted():
    graph = _school_graph("Same School")

    teacher_assignment = TeacherAssignment.objects.create(
        school_id=graph["school"].id,
        section=graph["section"],
        staff=graph["staff"],
    )
    submission = Submission.objects.create(
        school_id=graph["school"].id,
        assignment=graph["assignment"],
        enrollment=graph["enrollment"],
    )

    assert teacher_assignment.school_id == graph["school"].id
    assert submission.school_id == graph["school"].id


@pytest.mark.parametrize("bad_parent", ["section", "staff"])
def test_teacher_assignment_rejects_each_cross_school_parent(bad_parent):
    graph_a = _school_graph(f"Teacher A {bad_parent}")
    graph_b = _school_graph(f"Teacher B {bad_parent}")
    kwargs = {
        "school_id": graph_a["school"].id,
        "section": graph_a["section"],
        "staff": graph_a["staff"],
    }
    kwargs[bad_parent] = graph_b[bad_parent]

    with pytest.raises(ValidationError):
        TeacherAssignment.objects.create(**kwargs)

    assert TeacherAssignment.objects.count() == 0


def test_assignment_category_rejects_cross_school_section():
    graph_a = _school_graph("Category A")
    graph_b = _school_graph("Category B")

    category = AssignmentCategory(
        school_id=graph_a["school"].id,
        section=graph_b["section"],
        name="Invalid",
    )
    with pytest.raises(ValidationError):
        category.save()

    assert not AssignmentCategory.objects.filter(pk=category.pk).exists()


@pytest.mark.parametrize("bad_parent", ["section", "category"])
def test_assignment_rejects_each_cross_school_parent(bad_parent):
    graph_a = _school_graph(f"Assignment A {bad_parent}")
    graph_b = _school_graph(f"Assignment B {bad_parent}")
    kwargs = {
        "school_id": graph_a["school"].id,
        "section": graph_a["section"],
        "category": graph_a["category"],
        "name": "Invalid",
        "points_possible": Decimal("10.00"),
    }
    kwargs[bad_parent] = graph_b[bad_parent]

    assignment = Assignment(**kwargs)
    with pytest.raises(ValidationError):
        assignment.save()

    assert not Assignment.objects.filter(pk=assignment.pk).exists()


def test_assignment_rejects_same_school_category_from_different_section():
    graph = _school_graph("Assignment Lineage")
    course = Course.objects.create(
        school_id=graph["school"].id,
        code="LINEAGE-2",
        name="Second Course",
    )
    second_section = Section.objects.create(
        school_id=graph["school"].id,
        course=course,
        term="2026-FALL",
    )
    second_category = AssignmentCategory.objects.create(
        school_id=graph["school"].id,
        section=second_section,
        name="Second Category",
    )

    with pytest.raises(ValidationError, match="selected section"):
        Assignment.objects.create(
            school_id=graph["school"].id,
            section=graph["section"],
            category=second_category,
            name="Wrong Lineage",
            points_possible=Decimal("10.00"),
        )


@pytest.mark.parametrize("bad_parent", ["assignment", "enrollment"])
def test_submission_rejects_each_cross_school_parent(bad_parent):
    graph_a = _school_graph(f"Submission A {bad_parent}")
    graph_b = _school_graph(f"Submission B {bad_parent}")
    kwargs = {
        "school_id": graph_a["school"].id,
        "assignment": graph_a["assignment"],
        "enrollment": graph_a["enrollment"],
    }
    kwargs[bad_parent] = graph_b[bad_parent]

    submission = Submission(**kwargs)
    with pytest.raises(ValidationError):
        submission.save()

    assert not Submission.objects.filter(pk=submission.pk).exists()


def test_submission_rejects_same_school_enrollment_from_different_section():
    graph = _school_graph("Submission Lineage")
    course = Course.objects.create(
        school_id=graph["school"].id,
        code="SUB-LINEAGE-2",
        name="Second Course",
    )
    second_section = Section.objects.create(
        school_id=graph["school"].id,
        course=course,
        term="2026-FALL",
    )
    second_enrollment = Enrollment.objects.create(
        school_id=graph["school"].id,
        section=second_section,
        student=graph["student"],
    )

    with pytest.raises(ValidationError, match="assignment section"):
        Submission.objects.create(
            school_id=graph["school"].id,
            assignment=graph["assignment"],
            enrollment=second_enrollment,
        )


def test_partial_teacher_assignment_repoint_leaves_storage_unchanged():
    graph_a = _school_graph("Teacher Partial A")
    graph_b = _school_graph("Teacher Partial B")
    row = TeacherAssignment.objects.create(
        school_id=graph_a["school"].id,
        section=graph_a["section"],
        staff=graph_a["staff"],
    )

    row.staff = graph_b["staff"]
    with pytest.raises(ValidationError):
        row.save(update_fields=["staff"])

    row.refresh_from_db()
    assert row.staff_id == graph_a["staff"].id
    assert row.school_id == graph_a["school"].id


def test_partial_assignment_category_repoint_leaves_storage_unchanged():
    graph_a = _school_graph("Category Partial A")
    graph_b = _school_graph("Category Partial B")
    row = graph_a["category"]

    row.section = graph_b["section"]
    with pytest.raises(ValidationError):
        row.save(update_fields=["section"])

    row.refresh_from_db()
    assert row.section_id == graph_a["section"].id


def test_partial_assignment_repoint_leaves_storage_unchanged():
    graph_a = _school_graph("Assignment Partial A")
    graph_b = _school_graph("Assignment Partial B")
    row = graph_a["assignment"]

    row.category = graph_b["category"]
    with pytest.raises(ValidationError):
        row.save(update_fields=["category"])

    row.refresh_from_db()
    assert row.category_id == graph_a["category"].id


def test_partial_submission_repoint_leaves_storage_unchanged():
    graph_a = _school_graph("Submission Partial A")
    graph_b = _school_graph("Submission Partial B")
    row = Submission.objects.create(
        school_id=graph_a["school"].id,
        assignment=graph_a["assignment"],
        enrollment=graph_a["enrollment"],
    )

    row.enrollment = graph_b["enrollment"]
    with pytest.raises(ValidationError):
        row.save(update_fields=["enrollment"])

    row.refresh_from_db()
    assert row.enrollment_id == graph_a["enrollment"].id


def test_full_same_school_reparenting_succeeds_for_all_models():
    graph_a = _school_graph("Full Reparent A")
    graph_b = _school_graph("Full Reparent B")

    teacher_assignment = TeacherAssignment.objects.create(
        school_id=graph_a["school"].id,
        section=graph_a["section"],
        staff=graph_a["staff"],
    )
    submission = Submission.objects.create(
        school_id=graph_a["school"].id,
        assignment=graph_a["assignment"],
        enrollment=graph_a["enrollment"],
    )

    teacher_assignment.school_id = graph_b["school"].id
    teacher_assignment.section = graph_b["section"]
    teacher_assignment.staff = graph_b["staff"]
    teacher_assignment.save(update_fields=["school_id", "section", "staff"])

    submission.school_id = graph_b["school"].id
    submission.assignment = graph_b["assignment"]
    submission.enrollment = graph_b["enrollment"]
    submission.save(update_fields=["school_id", "assignment", "enrollment"])

    teacher_assignment.refresh_from_db()
    submission.refresh_from_db()
    assert teacher_assignment.school_id == graph_b["school"].id
    assert submission.school_id == graph_b["school"].id
