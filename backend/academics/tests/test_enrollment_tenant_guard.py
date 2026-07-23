import uuid

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from academics.models import Course, Enrollment, Section
from core.models import School
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
    return school, student, section


def test_enrollment_accepts_same_school_relationships():
    school, student, section = _school_graph("Same School")

    enrollment = Enrollment.objects.create(
        school_id=school.id,
        section=section,
        student=student,
    )

    enrollment.refresh_from_db()
    assert enrollment.school_id == school.id
    assert enrollment.section_id == section.id
    assert enrollment.student_id == student.id


def test_enrollment_normalizes_uuid_strings():
    school, student, section = _school_graph("UUID School")

    enrollment = Enrollment(
        school_id=str(school.id),
        section_id=str(section.id),
        student_id=str(student.id),
    )
    enrollment.save()

    enrollment.refresh_from_db()
    assert enrollment.school_id == school.id


def test_enrollment_rejects_cross_school_section_without_persistence():
    school_a, student_a, _section_a = _school_graph("Section A")
    _school_b, _student_b, section_b = _school_graph("Section B")

    with pytest.raises(ValidationError, match="section must belong to the same school"):
        Enrollment.objects.create(
            school_id=school_a.id,
            section=section_b,
            student=student_a,
        )

    assert Enrollment.objects.count() == 0


def test_enrollment_rejects_cross_school_student_without_persistence():
    school_a, _student_a, section_a = _school_graph("Student A")
    _school_b, student_b, _section_b = _school_graph("Student B")

    with pytest.raises(ValidationError, match="student must belong to the same school"):
        Enrollment.objects.create(
            school_id=school_a.id,
            section=section_a,
            student=student_b,
        )

    assert Enrollment.objects.count() == 0


def test_enrollment_fails_closed_for_missing_section():
    school, student, _section = _school_graph("Missing Section")

    enrollment = Enrollment(
        school_id=school.id,
        section_id=uuid.uuid4(),
        student=student,
    )

    with pytest.raises(ValidationError, match="Section does not exist"):
        enrollment.save()

    assert not Enrollment.objects.filter(pk=enrollment.pk).exists()


def test_enrollment_fails_closed_for_missing_student():
    school, _student, section = _school_graph("Missing Student")

    enrollment = Enrollment(
        school_id=school.id,
        section=section,
        student_id=uuid.uuid4(),
    )

    with pytest.raises(ValidationError, match="Student does not exist"):
        enrollment.save()

    assert not Enrollment.objects.filter(pk=enrollment.pk).exists()


def test_partial_section_repoint_is_rejected_and_storage_is_unchanged():
    school_a, student_a, section_a = _school_graph("Partial Section A")
    _school_b, _student_b, section_b = _school_graph("Partial Section B")
    enrollment = Enrollment.objects.create(
        school_id=school_a.id,
        section=section_a,
        student=student_a,
    )

    enrollment.section = section_b
    with pytest.raises(ValidationError):
        enrollment.save(update_fields=["section"])

    enrollment.refresh_from_db()
    assert enrollment.school_id == school_a.id
    assert enrollment.section_id == section_a.id
    assert enrollment.student_id == student_a.id


def test_partial_student_repoint_is_rejected_and_storage_is_unchanged():
    school_a, student_a, section_a = _school_graph("Partial Student A")
    _school_b, student_b, _section_b = _school_graph("Partial Student B")
    enrollment = Enrollment.objects.create(
        school_id=school_a.id,
        section=section_a,
        student=student_a,
    )

    enrollment.student = student_b
    with pytest.raises(ValidationError):
        enrollment.save(update_fields=["student"])

    enrollment.refresh_from_db()
    assert enrollment.school_id == school_a.id
    assert enrollment.section_id == section_a.id
    assert enrollment.student_id == student_a.id


def test_full_same_school_reparent_succeeds():
    school_a, student_a, section_a = _school_graph("Reparent A")
    school_b, student_b, section_b = _school_graph("Reparent B")
    enrollment = Enrollment.objects.create(
        school_id=school_a.id,
        section=section_a,
        student=student_a,
    )

    enrollment.school_id = school_b.id
    enrollment.section = section_b
    enrollment.student = student_b
    enrollment.save(update_fields=["school_id", "section", "student"])

    enrollment.refresh_from_db()
    assert enrollment.school_id == school_b.id
    assert enrollment.section_id == section_b.id
    assert enrollment.student_id == student_b.id


def test_duplicate_section_student_constraint_is_preserved():
    school, student, section = _school_graph("Duplicate")
    Enrollment.objects.create(
        school_id=school.id,
        section=section,
        student=student,
    )

    with pytest.raises(IntegrityError):
        Enrollment.objects.create(
            school_id=school.id,
            section=section,
            student=student,
        )
