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
from crown_api.models_households import ROLE_GUARDIAN, ROLE_AUTHORIZED_PICKUP


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


@pytest.mark.django_db
def test_school_owned_terms_and_sections_are_isolated(records):
    from core.models import AcademicYear
    from academics.models import Course as AcademicCourse
    from academics.models import Section as AcademicSection
    from academics.models import Term as AcademicTerm

    a, b = records["school_a"], records["school_b"]
    def term_for(school, suffix):
        year = AcademicYear.objects.create(
            school=school, name=f"2026-{suffix}",
            start_date=date(2026, 8, 1), end_date=date(2027, 6, 30),
        )
        return AcademicTerm.objects.create(
            school_id=school.pk, academic_year=year,
            code=f"FALL-{suffix}", name=f"Fall {suffix}",
            start_date=date(2026, 8, 15),
        )

    term_a = term_for(a, "A")
    term_b = term_for(b, "B")
    course_a = AcademicCourse.objects.create(
        school_id=a.pk, code="MATH-A", name="Math A",
    )
    course_b = AcademicCourse.objects.create(
        school_id=b.pk, code="MATH-B", name="Math B",
    )
    section_a = AcademicSection.objects.create(
        school_id=a.pk, term_ref=term_a, course=course_a, term=term_a.code,
    )
    AcademicSection.objects.create(
        school_id=b.pk, term_ref=term_b, course=course_b, term=term_b.code,
    )

    client = APIClient()
    client.force_login(records["staff"])
    headers = {"HTTP_X_SCHOOL_ID": str(a.pk)}
    terms = client.get("/api/v1/terms/", **headers)
    assert terms.status_code == 200
    assert {row["term_id"] for row in terms.json()} == {str(term_a.pk)}
    own_sections = client.get(f"/api/v1/terms/{term_a.pk}/sections/", **headers)
    assert own_sections.status_code == 200
    assert {row["section_id"] for row in own_sections.json()} == {str(section_a.pk)}
    foreign_sections = client.get(f"/api/v1/terms/{term_b.pk}/sections/", **headers)
    assert foreign_sections.status_code == 404


@pytest.mark.django_db
def test_unowned_legacy_scheduling_terms_cannot_cross_school(records):
    from crown_api.models_scheduling_core import Term as LegacyTerm

    legacy = LegacyTerm.objects.create(code="UNOWNED-2026", name="Unowned Synthetic Term")
    client = APIClient()
    client.force_login(records["staff"])
    headers = {"HTTP_X_SCHOOL_ID": str(records["school_a"].pk)}
    terms = client.get("/api/v1/terms/", **headers)
    assert terms.status_code == 200
    assert terms.json() == []
    result = client.get(f"/api/v1/terms/{legacy.pk}/sections/", **headers)
    assert result.status_code == 404


@pytest.mark.django_db
def test_matching_email_without_verified_person_link_never_authorizes_guardian(records):
    # The legacy Person directory is unowned by school. Email equality alone
    # must never grant household-derived attendance or grade access.
    person = records["parent"].person_link.person
    person.email = "reused-guardian@example.invalid"
    person.save(update_fields=["email"])

    Account = get_user_model()
    unlinked = Account.objects.create_user(
        username="synthetic-email-only",
        email="reused-guardian@example.invalid",
        school=records["school_a"],
    )
    UserRole.objects.create(
        user=unlinked, school=records["school_a"], role_code="PARENT",
    )
    client = APIClient()
    client.force_login(unlinked)
    headers = {"HTTP_X_SCHOOL_ID": str(records["school_a"].pk)}
    for record in ("attendance", "grades"):
        response = client.get(
            f"/api/v1/students/{records['student_a'].pk}/{record}/",
            **headers,
        )
        assert response.status_code == 404
        assert "PRIVATE" not in str(response.content)


@pytest.mark.django_db
def test_pickup_contact_cannot_read_student_records_or_communications(records):
    """A linked pickup contact is not a guardian, even with a PARENT login role."""
    from crown_api.models import MessageThread

    household = (
        records["parent"].person_link.person.household_memberships.first().household
    )
    person = Person.objects.create(
        first_name="Pickup", last_name="Only",
        email="synthetic-pickup@example.invalid",
    )
    HouseholdMember.objects.create(
        household=household, person=person,
        role=ROLE_AUTHORIZED_PICKUP, is_primary=False,
    )
    pickup = get_user_model().objects.create_user(
        username="synthetic-pickup-only",
        email="synthetic-pickup@example.invalid",
        school=records["school_a"],
    )
    UserRole.objects.create(
        user=pickup, school=records["school_a"], role_code="PARENT",
    )
    UserPersonLink.objects.create(user=pickup, person=person)
    MessageThread.objects.create(
        household=household, subject="PRIVATE guardian conversation",
        thread_type="GENERAL", created_by=person,
    )
    client = APIClient()
    client.force_login(pickup)
    headers = {"HTTP_X_SCHOOL_ID": str(records["school_a"].pk)}
    for record_type in ("attendance", "grades"):
        denied = client.get(
            f"/api/v1/students/{records['student_a'].pk}/{record_type}/",
            **headers,
        )
        assert denied.status_code == 404
        assert "PRIVATE" not in str(denied.content)
    threads = client.get("/api/v1/threads/", **headers)
    assert threads.status_code == 200
    assert threads.json() == []


@pytest.mark.django_db
def test_parent_permission_grant_cannot_expand_private_thread_scope(records):
    from core.models import CrownPermission, RolePermission
    from crown_api.models import MessageThread

    own_household = (
        records["parent"].person_link.person.household_memberships.first().household
    )
    another_household = Household.objects.create(
        household_name="Unrelated Synthetic Household"
    )
    other_family = Family.objects.create(
        school=records["school_a"], family_name="Unrelated Synthetic Family",
    )
    HouseholdFamilyLink.objects.create(
        school=records["school_a"], family=other_family,
        household_id=another_household.pk,
        source=HouseholdFamilyLink.SOURCE_MANUAL,
    )
    own = MessageThread.objects.create(
        household=own_household, subject="PRIVATE own household",
        thread_type="GENERAL",
    )
    foreign = MessageThread.objects.create(
        household=another_household, subject="PRIVATE other household",
        thread_type="GENERAL",
    )
    permission, _ = CrownPermission.objects.get_or_create(
        code="communications.view",
        defaults={"description": "View school communications"},
    )
    RolePermission.objects.get_or_create(
        role_code="PARENT", permission=permission,
    )
    client = APIClient()
    client.force_login(records["parent"])
    headers = {"HTTP_X_SCHOOL_ID": str(records["school_a"].pk)}
    response = client.get("/api/v1/threads/", **headers)
    assert response.status_code == 200
    identifiers = {row["thread_id"] for row in response.json()}
    assert identifiers == {str(own.pk)}
    assert str(foreign.pk) not in identifiers
    denied = client.get(f"/api/v1/threads/{foreign.pk}/", **headers)
    assert denied.status_code == 404
    assert "PRIVATE other household" not in str(denied.content)


@pytest.mark.django_db
@pytest.mark.parametrize("actor", ["staff", "parent"])
@pytest.mark.parametrize("link_school", ["school_a", "school_b"])
def test_ambiguous_household_ownership_cannot_expose_private_threads(records, actor, link_school):
    """Neither staff grants nor guardian membership resolve schoolless messages."""
    from core.models import CrownPermission, RolePermission
    from crown_api.models import MessageThread

    household = records["parent"].person_link.person.household_memberships.first().household
    thread = MessageThread.objects.create(
        household=household, subject="PRIVATE ambiguous ownership",
        thread_type="GENERAL",
    )
    permission, _ = CrownPermission.objects.get_or_create(
        code="communications.view",
        defaults={"description": "View school communications"},
    )
    RolePermission.objects.get_or_create(
        role_code="REGISTRAR" if actor == "staff" else "PARENT",
        permission=permission,
    )
    client = APIClient()
    client.force_login(records[actor])
    headers = {"HTTP_X_SCHOOL_ID": str(records["school_a"].pk)}
    endpoint = "/api/v1/threads/"
    before = client.get(endpoint, **headers)
    assert before.status_code == 200
    assert {row["thread_id"] for row in before.json()} == {str(thread.pk)}
    assert client.get(f"{endpoint}{thread.pk}/", **headers).status_code == 200

    foreign_family = Family.objects.create(
        school=records["school_b"], family_name="Synthetic foreign ownership",
    )
    # Exercise both valid cross-school ownership and a malformed same-school
    # bridge pointing at a foreign family. Neither can safely attribute messages.
    HouseholdFamilyLink.objects.create(
        school=records[link_school], family=foreign_family,
        household_id=household.pk, source=HouseholdFamilyLink.SOURCE_MANUAL,
    )
    after = client.get(endpoint, **headers)
    assert after.status_code == 200
    assert after.json() == []
    denied = client.get(f"{endpoint}{thread.pk}/", **headers)
    assert denied.status_code == 404
    assert "PRIVATE" not in str(denied.content)
