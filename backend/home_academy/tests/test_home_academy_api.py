from datetime import date

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from core.models import AcademicYear, Family, GradeLevel, Guardian, School, Student, StudentIdentityLink, UserAccount, UserRole
from academics.models import Course, Term, TranscriptEntry
from home_academy.models import (
    FinancialAidRule,
    HomeAcademyEnrollment,
    HomeAcademyProgram,
    Offering,
    OfferingEnrollment,
    TranscriptPostingRule,
)
from finance.models import FinanceObligation
from households.models import Guardian as HouseholdGuardian, Household, Student as CompatibilityStudent
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


def test_registration_persists_school_controlled_financial_aid_classification():
    school = make_school("Aid")
    enable_home_academy(school)
    registrar = make_user(school, "aid-registrar", role_code="REGISTRAR")
    student = make_student(school, "Aid")
    program = HomeAcademyProgram.objects.create(
        school_id=school.id,
        public_program_name="Aid Home Academy",
    )
    academy_enrollment = HomeAcademyEnrollment.objects.create(
        school_id=school.id,
        student_id=student.id,
        household_id=student.family_id,
        program=program,
    )
    offering = Offering.objects.create(
        school_id=school.id,
        program=program,
        offering_type="academic_course",
        title="Aid Biology",
        homeschool_seat_cap=5,
        total_capacity=10,
        requires_academic_anchor=False,
        requires_admin_approval=False,
        blocks_if_forms_missing=False,
    )
    rule = FinancialAidRule.objects.create(
        school_id=school.id,
        charge_type="course_fee",
        aid_eligible=True,
        active=True,
    )

    client, headers = auth_client(registrar, school)
    response = client.post(
        "/api/v1/home-academy/offering-enrollments/",
        {
            "student_id": str(student.id),
            "offering": offering.id,
            "home_academy_enrollment": academy_enrollment.id,
            "form_status": "complete",
            "payment_status": "not_required",
            "admin_approved": True,
        },
        format="json",
        **headers,
    )

    assert response.status_code == 201
    registration = OfferingEnrollment.objects.get(pk=response.json()["id"])
    assert registration.aid_eligible is True
    assert registration.financial_aid_rule_id == rule.id


def test_completed_registration_posts_transcript_only_through_verified_identity_mapping():
    school = make_school("Transcript")
    enable_home_academy(school)
    registrar = make_user(school, "transcript-registrar", role_code="REGISTRAR")

    family = Family.objects.create(school=school, family_name="Transcript Family")
    core_student = make_student(school, "Transcript", family=family)
    compatibility_household = Household.objects.create(
        school_id=school.id,
        name="Transcript Household",
    )
    compatibility_student = CompatibilityStudent.objects.create(
        school_id=school.id,
        household=compatibility_household,
        first_name="Student",
        last_name="Transcript",
        grade_level="10",
        is_active=True,
    )
    StudentIdentityLink.objects.create(
        school=school,
        core_student=core_student,
        compatibility_student=compatibility_student,
        source=StudentIdentityLink.SOURCE_MANUAL,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
        evidence_reference="home-academy-test-verified-link",
    )

    academic_year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date=date(2026, 8, 1),
        end_date=date(2027, 6, 1),
        is_current=True,
    )
    term = Term.objects.create(
        school_id=school.id,
        academic_year=academic_year,
        code="FALL",
        name="Fall",
        school_year="2026-2027",
    )
    course = Course.objects.create(
        school_id=school.id,
        code="BIO-HA",
        name="Biology",
        credits="1.00",
    )

    program = HomeAcademyProgram.objects.create(
        school_id=school.id,
        public_program_name="Transcript Home Academy",
    )
    academy_enrollment = HomeAcademyEnrollment.objects.create(
        school_id=school.id,
        student_id=core_student.id,
        household_id=family.id,
        program=program,
        status="homeschool_school_of_record",
        school_of_record_status="school_is_record",
    )
    offering = Offering.objects.create(
        school_id=school.id,
        program=program,
        offering_type="academic_course",
        title="Biology",
        school_year="2026-2027",
        term="fall",
        academic_course_id=course.id,
        academic_term_id=term.id,
        credit_bearing=True,
        transcript_eligible=True,
        homeschool_seat_cap=5,
        total_capacity=10,
        requires_academic_anchor=False,
        requires_admin_approval=False,
        blocks_if_forms_missing=False,
    )
    TranscriptPostingRule.objects.create(
        offering=offering,
        requires_registrar_approval=True,
        transcript_category="Science",
        credit_value="1.00",
        grade_source="Home Academy final",
        active=True,
    )
    registration = OfferingEnrollment.objects.create(
        school_id=school.id,
        student_id=core_student.id,
        offering=offering,
        home_academy_enrollment=academy_enrollment,
        status="active",
        eligibility_status="eligible",
        form_status="complete",
        payment_status="not_required",
        roster_status="active",
    )

    client, headers = auth_client(registrar, school)
    complete_url = f"/api/v1/home-academy/offering-enrollments/{registration.id}/complete/"
    post_url = f"/api/v1/home-academy/offering-enrollments/{registration.id}/post-transcript/"

    completed = client.post(
        complete_url,
        {"final_letter_grade": "A", "final_percentage": "94.50"},
        format="json",
        **headers,
    )
    first_post = client.post(post_url, {}, format="json", **headers)
    second_post = client.post(post_url, {}, format="json", **headers)

    assert completed.status_code == 200
    assert completed.json()["transcript_posting_status"] == "pending_registrar"
    assert first_post.status_code == 200
    assert second_post.status_code == 200
    registration.refresh_from_db()
    assert registration.transcript_posting_status == "posted"
    assert registration.transcript_entry_id is not None
    assert TranscriptEntry.objects.filter(
        pk=registration.transcript_entry_id,
        school_id=school.id,
        student=compatibility_student,
        course=course,
        term=term,
        final_letter_grade="A",
    ).count() == 1
    assert TranscriptEntry.objects.filter(
        school_id=school.id,
        student=compatibility_student,
        course=course,
        term=term,
    ).count() == 1


def test_parent_summary_contains_only_guardians_family():
    school = make_school("Parent Summary")
    enable_home_academy(school)
    family_a = Family.objects.create(school=school, family_name="Summary A")
    family_b = Family.objects.create(school=school, family_name="Summary B")
    own_student = make_student(school, "SummaryOwn", family=family_a)
    own_student.current_grade_level = GradeLevel.objects.create(
        school=school,
        code="7",
        label="Grade 7",
        sort_order=7,
    )
    own_student.save(update_fields=["current_grade_level"])
    other_student = make_student(school, "SummaryOther", family=family_b)
    guardian = Guardian.objects.create(
        school=school,
        family=family_a,
        first_name="Summary",
        last_name="Parent",
        email="summary-parent@example.test",
        relationship="GUARDIAN",
        portal_access=True,
    )
    parent = make_user(school, "summary-parent", role_code="PARENT", guardian=guardian)
    program = HomeAcademyProgram.objects.create(
        school_id=school.id,
        public_program_name="Summary Home Academy",
    )
    HomeAcademyEnrollment.objects.create(
        school_id=school.id,
        student_id=own_student.id,
        household_id=family_a.id,
        program=program,
    )
    HomeAcademyEnrollment.objects.create(
        school_id=school.id,
        student_id=other_student.id,
        household_id=family_b.id,
        program=program,
    )

    client, headers = auth_client(parent, school)
    response = client.get("/api/v1/home-academy/parent/summary/", **headers)

    assert response.status_code == 200
    ids = {row["id"] for row in response.json()["students"]}
    assert ids == {str(own_student.id)}
    assert response.json()["students"][0]["grade_level"] == "Grade 7"
    assert str(other_student.id) not in response.content.decode()


def test_offering_rejects_cross_school_academic_course_mapping():
    school_a = make_school("Mapping A")
    school_b = make_school("Mapping B")
    enable_home_academy(school_a)
    admin = UserAccount.objects.create_superuser(
        username="ha-mapping-admin",
        email="ha-mapping-admin@example.test",
        password="test-pass",
    )
    program = HomeAcademyProgram.objects.create(
        school_id=school_a.id,
        public_program_name="Mapping Home Academy",
    )
    foreign_course = Course.objects.create(
        school_id=school_b.id,
        code="FOREIGN",
        name="Foreign Course",
        credits="1.00",
    )
    client, headers = auth_client(admin, school_a)

    response = client.post(
        "/api/v1/home-academy/offerings/",
        {
            "program": program.id,
            "offering_type": "academic_course",
            "title": "Unsafe Mapping",
            "academic_course_id": str(foreign_course.id),
            "homeschool_seat_cap": 5,
            "requires_academic_anchor": False,
        },
        format="json",
        **headers,
    )

    assert response.status_code == 404
    assert Offering.objects.filter(school_id=school_a.id, title="Unsafe Mapping").count() == 0
