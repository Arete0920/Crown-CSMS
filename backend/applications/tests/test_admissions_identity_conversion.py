from datetime import date

import pytest
from django.db import transaction

from applications.models import Application, ApplicationStatus
from applications.views_admissions_identity import _verified_admissions_context
from core.models import (
    Family,
    HouseholdFamilyLink,
    School,
    Student as CoreStudent,
    StudentIdentityLink,
)
from households.models import Household, Student as CompatibilityStudent


pytestmark = pytest.mark.django_db


def _identity_fixture(*, student_number="S-1001", evidence="application:test"):
    school = School.objects.create(name="Identity School")
    household = Household.objects.create(
        school_id=school.id,
        name="Identity Household",
    )
    family = Family.objects.create(
        school=school,
        family_name="Identity Family",
    )
    HouseholdFamilyLink.objects.create(
        school=school,
        household_id=household.id,
        family=family,
        source=HouseholdFamilyLink.SOURCE_ADMISSIONS,
    )
    application = Application.objects.create(
        school_id=school.id,
        household=household,
        status=ApplicationStatus.SUBMITTED,
    )
    compatibility_student = CompatibilityStudent.objects.create(
        school_id=school.id,
        household=household,
        first_name="Ada",
        last_name="Lovelace",
        grade_level="5",
        is_active=True,
    )
    applicant = application.applicants.create(
        school_id=school.id,
        student=compatibility_student,
        first_name="Ada",
        last_name="Lovelace",
        grade_applying_for="5",
        dob=date(2015, 3, 10),
    )
    core_student = CoreStudent.objects.create(
        school=school,
        family=family,
        student_number=student_number,
        first_name="Ada",
        last_name="Lovelace",
        dob=date(2015, 3, 10),
        status="ACTIVE",
    )
    StudentIdentityLink.objects.create(
        school=school,
        core_student=core_student,
        compatibility_student=compatibility_student,
        source=StudentIdentityLink.SOURCE_ADMISSIONS,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
        evidence_reference=evidence,
    )
    return (
        school,
        household,
        family,
        application,
        applicant,
        compatibility_student,
        core_student,
    )


def test_verified_context_accepts_explicit_bridge_and_authoritative_identity():
    school, _, family, application, applicant, _, core_student = _identity_fixture()

    with transaction.atomic():
        context, error = _verified_admissions_context(
            school=school,
            application_id=application.id,
        )

    assert error is None
    assert context is not None
    assert context.family.id == family.id
    assert len(context.identities) == 1
    assert context.identities[0].applicant.id == applicant.id
    assert context.identities[0].core_student.id == core_student.id


def test_verified_context_fails_closed_without_student_bridge():
    school = School.objects.create(name="No Bridge School")
    household = Household.objects.create(
        school_id=school.id,
        name="No Bridge Household",
    )
    family = Family.objects.create(
        school=school,
        family_name="No Bridge Family",
    )
    HouseholdFamilyLink.objects.create(
        school=school,
        household_id=household.id,
        family=family,
        source=HouseholdFamilyLink.SOURCE_ADMISSIONS,
    )
    application = Application.objects.create(
        school_id=school.id,
        household=household,
        status=ApplicationStatus.SUBMITTED,
    )
    application.applicants.create(
        school_id=school.id,
        first_name="Grace",
        last_name="Hopper",
        grade_applying_for="6",
        dob=date(2014, 12, 9),
    )

    with transaction.atomic():
        context, error = _verified_admissions_context(
            school=school,
            application_id=application.id,
        )

    assert context is None
    assert error is not None
    assert error.status_code == 409
    assert error.data["code"] == "student_identity_link_required"


def test_verified_context_rejects_fabricated_app_student_number():
    school, _, _, application, _, _, _ = _identity_fixture(
        student_number="APP-ABC123-01"
    )

    with transaction.atomic():
        context, error = _verified_admissions_context(
            school=school,
            application_id=application.id,
        )

    assert context is None
    assert error is not None
    assert error.status_code == 409
    assert error.data["code"] == "authoritative_student_number_required"


def test_verified_context_rejects_dob_mismatch():
    school, _, _, application, applicant, _, _ = _identity_fixture()
    applicant.dob = date(2015, 3, 11)
    applicant.save(update_fields=["dob", "updated_at"])

    with transaction.atomic():
        context, error = _verified_admissions_context(
            school=school,
            application_id=application.id,
        )

    assert context is None
    assert error is not None
    assert error.status_code == 409
    assert error.data["code"] == "student_dob_verification_required"


def test_canonical_routes_use_identity_safe_conversion_views():
    from crown_api import api_v1_urls

    assert (
        api_v1_urls.admissions_enrollment_state_update.__module__
        == "applications.views_admissions_identity"
    )
    assert (
        api_v1_urls.admissions_lifecycle_chain_update.__module__
        == "applications.views_admissions_identity"
    )
