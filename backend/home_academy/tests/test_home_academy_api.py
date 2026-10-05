from datetime import date

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from core.models import Family, Guardian, School, Student, UserAccount, UserRole
from home_academy.models import HomeAcademyEnrollment, HomeAcademyProgram, Offering, OfferingEnrollment
from finance.models import FinanceObligation
from households.models import Guardian as HouseholdGuardian, Household
from ledger.models import Charge
from subscriptions.models import SchoolModule

pytestmark = pytest.mark.django_db


def make_school(name):
    return School.objects.create(name=name)


def make_student(school, suffix, family=None):
    family = family or Family.objects.create(
        school=school,
        family_name=f"Family {suffix}",
    )
    return Student.objects.create(
        school=school,
        family=family,
        student_number=f"HA-{suffix}",
        first_name="Student",
        last_name=suffix,
        dob=date(2012, 1, 1),
        status="ACTIVE",
    )


def make_user(school, suffix, role_code=None, guardian=None):
    user = UserAccount.objects.create_user(
        username=f"ha-{suffix}",
        email=f"ha-{suffix}@example.test",
        password="test-pass",
        school=school,
        guardian=guardian,
    )
    if role_code:
        UserRole.objects.create(school=school, user=user, role_code=role_code)
    return user


def enable_home_academy(school):
    return SchoolModule.objects.create(
        school=school,
        module_key="home_academy",
        status="active",
    )


def auth_client(user, school):
    client = APIClient()
    client.force_authenticate(user=user)
    return client, {"HTTP_X_SCHOOL_ID": str(school.id)}


@pytest.fixture(autouse=True)
def seed_home_academy_permissions():
    call_command("seed_permissions", verbosity=0)


def test_disabled_module_fails_closed():
    school = make_school("Disabled")
    user = make_user(school, "disabled", role_code="REGISTRAR")
    client, headers = auth_client(user, school)

    response = client.get("/api/v1/home-academy/offerings/", **headers)

    assert response.status_code == 403
    assert response.json()["code"] == "MODULE_NOT_ENABLED"


def test_registrar_can_read_enabled_home_academy():
    school = make_school("Enabled")
    enable_home_academy(school)
    user = make_user(school, "registrar", role_code="REGISTRAR")
    client, headers = auth_client(user, school)

    response = client.get("/api/v1/home-academy/offerings/", **headers)

    assert response.status_code == 200
    assert response.json() == []


def test_cross_school_program_cannot_be_used_to_create_enrollment():
    school_a = make_school("School A")
    school_b = make_school("School B")
    enable_home_academy(school_a)
    enable_home_academy(school_b)
    user = make_user(school_a, "registrar-a", role_code="REGISTRAR")
    student_a = make_student(school_a, "A")
    program_b = HomeAcademyProgram.objects.create(
        school_id=school_b.id,
        public_program_name="School B Home Academy",
    )
    client, headers = auth_client(user, school_a)

    response = client.post(
        "/api/v1/home-academy/enrollments/",
        {
            "student_id": str(student_a.id),
            "program": program_b.id,
            "status": "homeschool_affiliate",
            "school_of_record_status": "parent_is_record",
            "diploma_eligibility_status": "not_eligible",
        },
        format="json",
        **headers,
    )

    assert response.status_code == 404
    assert HomeAcademyEnrollment.objects.filter(school_id=school_a.id).count() == 0


def test_parent_can_check_only_linked_child_eligibility():
    school = make_school("Family Scope")
    enable_home_academy(school)

    family_a = Family.objects.create(school=school, family_name="Family A")
    family_b = Family.objects.create(school=school, family_name="Family B")
    own_student = make_student(school, "Own", family=family_a)
    other_student = make_student(school, "Other", family=family_b)

    guardian = Guardian.objects.create(
        school=school,
        family=family_a,
        first_name="Parent",
        last_name="One",
        email="parent-one@example.test",
        relationship="GUARDIAN",
        portal_access=True,
    )
    parent = make_user(school, "parent", role_code="PARENT", guardian=guardian)

    program = HomeAcademyProgram.objects.create(
        school_id=school.id,
        public_program_name="Family Scope Home Academy",
    )
    HomeAcademyEnrollment.objects.create(
        school_id=school.id,
        student_id=own_student.id,
        household_id=family_a.id,
        program=program,
    )
    offering = Offering.objects.create(
        school_id=school.id,
        program=program,
        offering_type="academic_course",
        title="Biology",
        homeschool_seat_cap=5,
        total_capacity=10,
        requires_academic_anchor=False,
        requires_admin_approval=False,
        blocks_if_forms_missing=False,
    )

    client, headers = auth_client(parent, school)

    own_response = client.get(
        f"/api/v1/home-academy/offerings/{offering.id}/students/{own_student.id}/eligibility/",
        **headers,
    )
    other_response = client.get(
        f"/api/v1/home-academy/offerings/{offering.id}/students/{other_student.id}/eligibility/",
        **headers,
    )

    assert own_response.status_code == 200
    assert other_response.status_code == 404


def test_enrollment_write_derives_household_from_canonical_student():
    school = make_school("Canonical")
    enable_home_academy(school)
    user = make_user(school, "canonical-registrar", role_code="REGISTRAR")
    student = make_student(school, "Canonical")
    program = HomeAcademyProgram.objects.create(
        school_id=school.id,
        public_program_name="Canonical Home Academy",
    )
    client, headers = auth_client(user, school)

    response = client.post(
        "/api/v1/home-academy/enrollments/",
        {
            "student_id": str(student.id),
            "program": program.id,
            "household_id": "00000000-0000-0000-0000-000000000001",
            "status": "homeschool_affiliate",
            "school_of_record_status": "parent_is_record",
            "diploma_eligibility_status": "not_eligible",
        },
        format="json",
        **headers,
    )

    assert response.status_code == 201
    enrollment = HomeAcademyEnrollment.objects.get(pk=response.json()["id"])
    assert enrollment.student_id == student.id
    assert enrollment.household_id == student.family_id


def test_activation_posts_one_canonical_finance_obligation_and_is_idempotent():
    school = make_school("Billing")
    enable_home_academy(school)
    registrar = make_user(school, "billing-registrar", role_code="REGISTRAR")

    family = Family.objects.create(school=school, family_name="Billing Family")
    student = make_student(school, "Billing", family=family)
    core_guardian = Guardian.objects.create(
        school=school,
        family=family,
        first_name="Billing",
        last_name="Parent",
        email="billing-parent@example.test",
        relationship="GUARDIAN",
        portal_access=True,
    )
    parent = make_user(school, "billing-parent", role_code="PARENT", guardian=core_guardian)

    compatibility_household = Household.objects.create(
        school_id=school.id,
        name="Billing Compatibility Household",
    )
    HouseholdGuardian.objects.create(
        school_id=school.id,
        household=compatibility_household,
        account=parent,
        first_name="Billing",
        last_name="Parent",
        email=parent.email,
        is_primary=True,
    )

    program = HomeAcademyProgram.objects.create(
        school_id=school.id,
        public_program_name="Billing Home Academy",
    )
    academy_enrollment = HomeAcademyEnrollment.objects.create(
        school_id=school.id,
        student_id=student.id,
        household_id=family.id,
        program=program,
    )
    offering = Offering.objects.create(
        school_id=school.id,
        program=program,
        offering_type="academic_course",
        title="Biology",
        price="125.00",
        school_year="2026-2027",
        homeschool_seat_cap=5,
        total_capacity=10,
        requires_academic_anchor=False,
        requires_admin_approval=True,
        blocks_if_forms_missing=False,
    )
    registration = OfferingEnrollment.objects.create(
        school_id=school.id,
        student_id=student.id,
        offering=offering,
        home_academy_enrollment=academy_enrollment,
        form_status="complete",
        payment_status="pending",
    )

    client, headers = auth_client(registrar, school)
    url = f"/api/v1/home-academy/offering-enrollments/{registration.id}/activate/"

    first = client.post(url, {}, format="json", **headers)
    second = client.post(url, {}, format="json", **headers)

    assert first.status_code == 200
    assert second.status_code == 200
    registration.refresh_from_db()
    assert registration.status == "active"
    assert registration.finance_obligation_id is not None
    assert FinanceObligation.objects.filter(
        pk=registration.finance_obligation_id,
        school=school,
        amount_cents=12500,
    ).count() == 1
    assert FinanceObligation.objects.filter(school=school).count() == 1
    assert Charge.objects.filter(school_id=school.id).count() == 1
