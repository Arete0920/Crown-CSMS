"""Module 016 - Faculty Load & Scheduling evidence.

This evidence proves the current Module 016 production boundary:

1. Faculty load is calculated from the academic section registry, not HR CRUD.
2. Load totals are tenant-scoped by school.
3. Load totals can be filtered by term and academic year.
4. Duplicate teacher-section assignments are blocked by the model constraint.
5. Faculty overload conflicts are detected from explicit section and credit thresholds.
"""

from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from academics.faculty_load import faculty_load_conflicts, faculty_load_summary
from academics.models import Course, Section, TeacherAssignment, Term
from core.models import AcademicYear, School, Staff

pytestmark = pytest.mark.django_db


def _school(name: str) -> School:
    return School.objects.create(name=name, timezone="America/New_York", is_active=True)


def _year(school: School, name: str = "2026-2027") -> AcademicYear:
    return AcademicYear.objects.create(
        school=school,
        name=name,
        start_date="2026-08-15",
        end_date="2027-06-10",
        is_current=True,
    )


def _term(school: School, year: AcademicYear, code: str, order: int) -> Term:
    return Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code=code,
        name=code.replace("-", " ").title(),
        school_year=year.name,
        ordering=order,
        active=True,
    )


def _course(school: School, code: str, credits: str) -> Course:
    return Course.objects.create(
        school_id=school.id,
        code=code,
        name=f"Course {code}",
        department="Academic",
        credits=Decimal(credits),
    )


def _staff(
    school: School,
    email: str,
    first: str = "Faculty",
    last: str = "Member",
) -> Staff:
    return Staff.objects.create(
        school=school,
        first_name=first,
        last_name=last,
        email=email,
        role_type="TEACHER",
        status="ACTIVE",
    )


def _section(
    school: School,
    course: Course,
    term: Term,
    teacher_name: str = "Teacher",
) -> Section:
    return Section.objects.create(
        school_id=school.id,
        course=course,
        term_ref=term,
        term=term.code,
        teacher_name=teacher_name,
        grade_band="9-12",
    )


def _assign(school: School, section: Section, staff: Staff) -> TeacherAssignment:
    return TeacherAssignment.objects.create(
        school_id=school.id,
        section=section,
        staff=staff,
    )


def test_faculty_load_summary_counts_sections_and_credits_by_term():
    school = _school("Module 016 Load School")
    year = _year(school)
    fall = _term(school, year, "2026-FALL", 1)
    spring = _term(school, year, "2027-SPRING", 2)

    teacher_one = _staff(school, "teacher.one@example.com", first="Teacher", last="One")
    teacher_two = _staff(school, "teacher.two@example.com", first="Teacher", last="Two")

    _assign(school, _section(school, _course(school, "ENG-101", "1.00"), fall), teacher_one)
    _assign(school, _section(school, _course(school, "ENG-102", "0.50"), fall), teacher_one)
    _assign(school, _section(school, _course(school, "MATH-201", "1.25"), fall), teacher_two)
    _assign(
        school,
        _section(school, _course(school, "SCI-301", "1.00"), spring),
        teacher_one,
    )

    fall_loads = faculty_load_summary(school.id, term="2026-FALL")
    by_email = {row["staff_email"]: row for row in fall_loads}

    assert by_email["teacher.one@example.com"]["section_count"] == 2
    assert by_email["teacher.one@example.com"]["credit_load"] == Decimal("1.50")
    assert {item["course_code"] for item in by_email["teacher.one@example.com"]["sections"]} == {
        "ENG-101",
        "ENG-102",
    }

    assert by_email["teacher.two@example.com"]["section_count"] == 1
    assert by_email["teacher.two@example.com"]["credit_load"] == Decimal("1.25")
    assert {item["course_code"] for item in by_email["teacher.two@example.com"]["sections"]} == {
        "MATH-201",
    }


def test_faculty_load_summary_is_tenant_scoped():
    school_a = _school("Module 016 Tenant A")
    school_b = _school("Module 016 Tenant B")
    year_a = _year(school_a)
    year_b = _year(school_b)
    term_a = _term(school_a, year_a, "2026-FALL", 1)
    term_b = _term(school_b, year_b, "2026-FALL", 1)

    staff_a = _staff(school_a, "tenant-a-teacher@example.com", first="Tenant", last="A")
    staff_b = _staff(school_b, "tenant-b-teacher@example.com", first="Tenant", last="B")

    _assign(school_a, _section(school_a, _course(school_a, "A-101", "1.00"), term_a), staff_a)
    _assign(school_b, _section(school_b, _course(school_b, "B-101", "1.00"), term_b), staff_b)

    loads = faculty_load_summary(school_a.id, term="2026-FALL")

    assert [row["staff_email"] for row in loads] == ["tenant-a-teacher@example.com"]
    assert all(
        section["course_code"].startswith("A-")
        for row in loads
        for section in row["sections"]
    )


def test_duplicate_teacher_section_assignment_is_blocked():
    school = _school("Module 016 Duplicate Guard")
    year = _year(school)
    term = _term(school, year, "2026-FALL", 1)
    staff = _staff(school, "duplicate-guard@example.com")
    section = _section(school, _course(school, "DUP-101", "1.00"), term)

    _assign(school, section, staff)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            _assign(school, section, staff)


def test_faculty_load_conflicts_detect_section_and_credit_overload():
    school = _school("Module 016 Conflict School")
    year = _year(school)
    fall = _term(school, year, "2026-FALL", 1)

    overloaded = _staff(school, "overloaded@example.com", first="Over", last="Loaded")
    normal = _staff(school, "normal@example.com", first="Normal", last="Load")

    _assign(school, _section(school, _course(school, "LOAD-101", "1.00"), fall), overloaded)
    _assign(school, _section(school, _course(school, "LOAD-102", "1.00"), fall), overloaded)
    _assign(school, _section(school, _course(school, "LOAD-103", "1.00"), fall), overloaded)
    _assign(school, _section(school, _course(school, "LOAD-201", "1.00"), fall), normal)

    conflicts = faculty_load_conflicts(
        school.id,
        term="2026-FALL",
        max_sections=2,
        max_credits=Decimal("2.50"),
    )

    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict["staff_id"] == str(overloaded.id)
    assert conflict["section_count"] == 3
    assert conflict["credit_load"] == Decimal("3.00")
    assert set(conflict["conflict_types"]) == {"SECTION_OVERLOAD", "CREDIT_OVERLOAD"}
    assert {section["course_code"] for section in conflict["sections"]} == {
        "LOAD-101",
        "LOAD-102",
        "LOAD-103",
    }
