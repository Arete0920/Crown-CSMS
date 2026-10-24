"""Production-like two-school authorization regressions for legacy academics.

Synthetic school/record identities only. Tenant enforcement is deliberately on
even though the root test conftest defaults it off for older shape-contract tests.
"""
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from core.models import Family, HouseholdFamilyLink, School, Student, UserRole
from crown_api.models import (
    AttendanceRecord, Course, GradeRecord, Household, HouseholdMember,
    Person, UserPersonLink,
)
from crown_api.models_households import ROLE_GUARDIAN


@pytest.fixture(autouse=True)
def production_tenant_enforcement(settings):
    settings.TENANT_HEADER_REQUIRED = True
    settings.CROWN_DEV_OPEN_API = False
    settings.CROWN_ENV = "dev"


@pytest.fixture
def records(db):
    school_a = School.objects.create(name="Synthetic Attendance School A")
    school_b = School.objects.create(name="Synthetic Attendance School B")
    family_a = Family.objects.create(school=school_a, family_name="Synthetic A")
    family_b = Family.objects.create(school=school_b, family_name="Synthetic B")
    student_a = Student.objects.create(
        school=school_a, family=family_a, student_number="A-1",
        first_name="Student", last_name="A", dob=date(2016, 1, 1), status="ACTIVE",
    )
    student_b = Student.objects.create(
        school=school_b, family=family_b, student_number="B-1",
        first_name="Student", last_name="B", dob=date(2017, 1, 1), status="ACTIVE",
    )
    course = Course.objects.create(course_code="SYNTH-TENANT-101", name="Synthetic")
    AttendanceRecord.objects.create(
        student=student_a, course=course, date=date(2026, 8, 1),
        status=AttendanceRecord.STATUS_PRESENT, notes_public="PRIVATE SCHOOL A",
    )
    AttendanceRecord.objects.create(
        student=student_b, course=course, date=date(2026, 8, 1),
        status=AttendanceRecord.STATUS_ABSENT, notes_public="PRIVATE SCHOOL B",
    )
    GradeRecord.objects.create(
        student=student_a, course=course, period="Q1",
        assignment_name="A only", score=99, score_max=100,
        notes_public="PRIVATE GRADE A",
    )
    GradeRecord.objects.create(
        student=student_b, course=course, period="Q1",
        assignment_name="B only", score=11, score_max=100,
        notes_public="PRIVATE GRADE B",
    )
    Account = get_user_model()
    staff = Account.objects.create_user(username="synthetic-reader-a", school=school_a, is_staff=True)
    UserRole.objects.create(user=staff, school=school_a, role_code="REGISTRAR")
    parent = Account.objects.create_user(username="synthetic-guardian-a", school=school_a)
    UserRole.objects.create(user=parent, school=school_a, role_code="PARENT")
    household_a = Household.objects.create(household_name="Synthetic household A")
    person_a = Person.objects.create(first_name="Parent", last_name="A")
    UserPersonLink.objects.create(user=parent, person=person_a)
    HouseholdMember.objects.create(
        household=household_a, person=person_a,
        role=ROLE_GUARDIAN, is_primary=True,
    )
    HouseholdFamilyLink.objects.create(
        school=school_a, household_id=household_a.id,
        family=family_a, source=HouseholdFamilyLink.SOURCE_ADMISSIONS,
    )
    return {
        "school_a": school_a, "school_b": school_b,
        "student_a": student_a, "student_b": student_b,
        "staff": staff, "parent": parent,
    }


@pytest.mark.parametrize("record", ["attendance", "grades"])
def test_staff_can_read_only_selected_school(records, record):
    client = APIClient()
    client.force_login(records["staff"])
    school_a, school_b = records["school_a"], records["school_b"]
    student_a, student_b = records["student_a"], records["student_b"]
    path = lambda student: f"/api/students/{student.pk}/{record}/"

    own = client.get(path(student_a), HTTP_X_SCHOOL_ID=str(school_a.pk))
    assert own.status_code == 200, own.content[:250]
    assert len(own.json()) == 1
    assert "PRIVATE SCHOOL B" not in str(own.content)
    assert "PRIVATE GRADE B" not in str(own.content)

    foreign_id = client.get(path(student_b), HTTP_X_SCHOOL_ID=str(school_a.pk))
    assert foreign_id.status_code == 404
    assert "PRIVATE" not in str(foreign_id.content)

    unauthorized_header = client.get(path(student_b), HTTP_X_SCHOOL_ID=str(school_b.pk))
    assert unauthorized_header.status_code == 404
    assert "PRIVATE" not in str(unauthorized_header.content)


@pytest.mark.parametrize("record", ["attendance", "grades"])
def test_real_simplejwt_cannot_read_foreign_student(records, record):
    client = APIClient()
    token = AccessToken.for_user(records["staff"])
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    selected = str(records["school_a"].pk)
    own = client.get(
        f"/api/v1/students/{records['student_a'].pk}/{record}/",
        HTTP_X_SCHOOL_ID=selected,
    )
    assert own.status_code == 200, own.content[:250]

    cross = client.get(
        f"/api/v1/students/{records['student_b'].pk}/{record}/",
        HTTP_X_SCHOOL_ID=selected,
    )
    assert cross.status_code == 404
    assert "PRIVATE" not in str(cross.content)


@pytest.mark.parametrize("record", ["attendance", "grades"])
def test_parent_requires_matching_household_and_school(records, record):
    client = APIClient()
    client.force_login(records["parent"])
    selected = str(records["school_a"].pk)
    own = client.get(
        f"/api/students/{records['student_a'].pk}/{record}/",
        HTTP_X_SCHOOL_ID=selected,
    )
    assert own.status_code == 200, own.content[:250]

    other = client.get(
        f"/api/students/{records['student_b'].pk}/{record}/",
        HTTP_X_SCHOOL_ID=selected,
    )
    assert other.status_code == 404


@pytest.mark.parametrize("record", ["attendance", "grades"])
def test_inactive_school_and_invalid_header_fail_closed(records, record):
    client = APIClient()
    client.force_login(records["staff"])
    own = f"/api/students/{records['student_a'].pk}/{record}/"
    response = client.get(own, HTTP_X_SCHOOL_ID="invalid-school")
    assert response.status_code == 400

    school_a = records["school_a"]
    school_a.is_active = False
    school_a.save(update_fields=["is_active"])
    denied = client.get(own, HTTP_X_SCHOOL_ID=str(school_a.pk))
    assert denied.status_code == 404
