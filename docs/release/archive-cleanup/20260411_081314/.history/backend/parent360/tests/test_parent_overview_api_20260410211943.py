from __future__ import annotations

from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import AcademicYear, Assignment, AssignmentCategory, Course, Section, Term
from core.models import Family, School, UserRole
from households.models import Guardian, Household, Student as HouseholdStudent
from servicehours.models import ServiceEntry


pytestmark = pytest.mark.django_db

PARENT360_V1_URL = "/api/v1/parent360/me/overview/"
PARENT360_URL = "/api/parent360/me/overview/"


def _make_parent_client(*, school: School, email: str = "parent@example.com"):
    user = get_user_model().objects.create_user(
        username=f"parent-{school.id}",
        password="pass1234",
        email=email,
        school=school,
    )
    UserRole.objects.get_or_create(user=user, school=school, role_code="PARENT")

    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


def _make_household_bundle(
    school: School,
    *,
    email: str = "parent@example.com",
    household_name: str = "Demo Family",
    first_name: str = "Ava",
    last_name: str = "Student",
):
    household = Household.objects.create(
        school_id=school.id,
        name=household_name,
        is_active=True,
    )
    Guardian.objects.create(
        school_id=school.id,
        household=household,
        first_name="Pat",
        last_name="Parent",
        email=email,
        is_primary=True,
    )
    child = HouseholdStudent.objects.create(
        school_id=school.id,
        household=household,
        first_name=first_name,
        last_name=last_name,
        grade_level="5",
        is_active=True,
    )
    return household, child


def _make_core_student_with_service_hours(
    school: School,
    *,
    first_name: str,
    last_name: str,
    hours: str = "4.5",
):
    family = Family.objects.create(school=school, family_name=f"{last_name} Family {school.name}")
    from core.models import Student as CoreStudent

    student = CoreStudent.objects.create(
        school=school,
        family=family,
        student_number=f"S-{school.name[:3]}-{first_name[:1]}{last_name[:1]}",
        first_name=first_name,
        last_name=last_name,
        dob=date(2014, 1, 15),
        status="ACTIVE",
    )
    ServiceEntry.objects.create(
        school=school,
        student=student,
        date=date.today(),
        hours=hours,
        status="approved",
    )
    return student


def _make_assignment_for_unenrolled_section(school: School, *, due_date: date, name: str):
    academic_year = AcademicYear.objects.create(
        school=school,
        name=f"{school.name} 2025-2026 {name}",
        start_date=date(2025, 8, 1),
        end_date=date(2026, 6, 1),
        is_current=True,
    )
    term = Term.objects.create(
        school_id=school.id,
        academic_year=academic_year,
        code=f"TERM-{name[:4]}",
        name=f"Term {name}",
        school_year="2025-2026",
    )
    course = Course.objects.create(
        school_id=school.id,
        code=f"COURSE-{name[:4]}",
        name=f"Course {name}",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term_ref=term,
        term=term.code,
    )
    category = AssignmentCategory.objects.create(
        school_id=school.id,
        section=section,
        name="Homework",
        weight_percent=100,
    )
    return Assignment.objects.create(
        school_id=school.id,
        section=section,
        category=category,
        name=name,
        points_possible=10,
        due_date=due_date,
        is_published=True,
    )


def test_parent_self_overview_v1_route_returns_200_and_household_shape():
    school = School.objects.create(name="Heritage Parent Academy")
    client, _ = _make_parent_client(school=school)
    household, child = _make_household_bundle(school)

    response = client.get(PARENT360_V1_URL)

    assert response.status_code == 200, response.content
    payload = response.json()
    assert payload["household"]["id"] == str(household.id)
    assert payload["household"]["name"] == household.name
    assert payload["children_count"] == 1
    assert payload["children"][0]["id"] == str(child.id)


def test_parent_self_overview_rejects_foreign_school_guardian_email_match():
    school = School.objects.create(name="Home School")
    other_school = School.objects.create(name="Foreign School")
    email = "shared-parent@example.com"

    _make_household_bundle(other_school, email=email, household_name="Foreign Household")
    client, _ = _make_parent_client(school=school, email=email)

    response = client.get(PARENT360_URL)

    assert response.status_code == 404, response.content


def test_parent_self_overview_service_hours_do_not_bridge_across_schools():
    school = School.objects.create(name="Home Service School")
    other_school = School.objects.create(name="Foreign Service School")
    client, _ = _make_parent_client(school=school, email="service-parent@example.com")
    _, child = _make_household_bundle(
        school,
        email="service-parent@example.com",
        household_name="Service Family",
        first_name="Jordan",
        last_name="Cross",
    )
    _make_core_student_with_service_hours(
        other_school,
        first_name=child.first_name,
        last_name=child.last_name,
        hours="6.0",
    )

    response = client.get(PARENT360_URL)

    assert response.status_code == 200, response.content
    payload = response.json()
    assert payload["children"][0]["service_hours"]["completed"] == 0


def test_parent_self_overview_ignores_assignments_for_unenrolled_sections():
    school = School.objects.create(name="Unenrolled Assignment School")
    client, _ = _make_parent_client(school=school, email="assignments-parent@example.com")
    _make_household_bundle(
        school,
        email="assignments-parent@example.com",
        household_name="Assignment Family",
    )
    _make_assignment_for_unenrolled_section(
        school,
        due_date=date(2026, 1, 10),
        name="Past Due Work",
    )
    _make_assignment_for_unenrolled_section(
        school,
        due_date=date.today(),
        name="Upcoming Work",
    )

    response = client.get(PARENT360_URL)

    assert response.status_code == 200, response.content
    payload = response.json()
    assert payload["missing_assignments_total"] == 0
    assert payload["upcoming_assignments_total"] == 0
    assert payload["children"][0]["missing_assignments"] == 0
    assert payload["children"][0]["upcoming_assignments"] == []
