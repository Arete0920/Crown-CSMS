from datetime import date
from uuid import uuid4

import pytest
from django.db import transaction

from admissions.models import AdmissionsApplication

from applications.models import Application, ApplicationStatus
from applications.views_admissions_identity import (
    _verified_admissions_context, _upsert_verified_legacy_admissions,
)
from core.models import (
    AcademicYear, Enrollment as CoreEnrollment, Family, GradeLevel,
    HouseholdFamilyLink,
    School,
    Student as CoreStudent,
    StudentIdentityLink,
)
from households.models import Household, Student as CompatibilityStudent


pytestmark = pytest.mark.django_db


def _identity_fixture(*, student_number="S-1001", evidence=None):
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
        evidence_reference=(
            f"application:{application.id}:applicant:{applicant.id}"
            if evidence is None else evidence
        ),
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


@pytest.mark.parametrize(
    "mutation",
    ("different_application", "different_applicant", "manual_source"),
)
def test_verified_context_rejects_unbound_or_nonadmissions_evidence(mutation):
    school, _, _, application, applicant, _, core_student = _identity_fixture()
    link = StudentIdentityLink.objects.get(core_student=core_student)
    if mutation == "different_application":
        link.evidence_reference = f"application:{uuid4()}:applicant:{applicant.id}"
    elif mutation == "different_applicant":
        link.evidence_reference = f"application:{application.id}:applicant:{uuid4()}"
    else:
        link.source = StudentIdentityLink.SOURCE_MANUAL
    link.save(update_fields=["source", "evidence_reference", "updated_at"])

    with transaction.atomic():
        context, error = _verified_admissions_context(
            school=school,
            application_id=application.id,
        )

    assert context is None
    assert error is not None
    assert error.status_code == 409
    assert error.data["code"] == "student_identity_evidence_required"
    assert error.data["applicant_id"] == str(applicant.id)


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


def _legacy_sync_fixture():
    school, _, family, application, applicant, _, core_student = _identity_fixture()
    year = AcademicYear.objects.create(
        school=school, name="2026-2027", start_date=date(2026, 8, 15),
        end_date=date(2027, 6, 15), is_current=True,
    )
    grade = GradeLevel.objects.create(
        school=school, code=applicant.grade_applying_for,
        label="Grade 5", sort_order=5,
    )
    CoreEnrollment.objects.create(
        school=school, student=core_student, academic_year=year,
        grade_level=grade, start_date=year.start_date, status="ENROLLED",
    )
    with transaction.atomic():
        context, error = _verified_admissions_context(
            school=school, application_id=application.id,
        )
    assert error is None and context is not None
    return school, family, application, applicant, core_student, year, context


def test_verified_legacy_sync_creates_new_attributed_row_and_replays():
    school, family, application, _, student, year, context = _legacy_sync_fixture()
    with transaction.atomic():
        first, error = _upsert_verified_legacy_admissions(
            school=school, context=context, actor_user=None,
            target_status=AdmissionsApplication.STATUS_ACCEPTED,
            academic_year=year,
        )
        second, repeat_error = _upsert_verified_legacy_admissions(
            school=school, context=context, actor_user=None,
            target_status=AdmissionsApplication.STATUS_ACCEPTED,
            academic_year=year,
        )
    assert error is None and repeat_error is None
    assert first["application_ids"] == second["application_ids"]
    rows = list(AdmissionsApplication.objects.filter(student=student, academic_year=year))
    assert len(rows) == 1
    assert rows[0].school_id == school.id
    assert rows[0].family_id == family.id
    assert rows[0].status == AdmissionsApplication.STATUS_ACCEPTED
    assert rows[0].notes_internal == f"canonical_application_id={application.id}"


@pytest.mark.parametrize(
    "historical_notes",
    (
        "",
        "legacy unrelated observation",
        "canonical_application_id=00000000-0000-4000-8000-000000000001",
        "canonical_application_id=not-a-uuid",
        "canonical_application_id={matching}\\ncanonical_application_id={matching}",
        "canonical_application_id={matching} ;canonical_application_id=foreign",
    ),
)
def test_verified_legacy_sync_rejects_unowned_or_ambiguous_history(historical_notes):
    school, family, application, _, student, year, context = _legacy_sync_fixture()
    notes = historical_notes.replace("{matching}", str(application.id))
    historical = AdmissionsApplication.objects.create(
        school=school, academic_year=year, family=family, student=student,
        status=AdmissionsApplication.STATUS_ACCEPTED, notes_internal=notes,
    )
    with transaction.atomic():
        result, error = _upsert_verified_legacy_admissions(
            school=school, context=context, actor_user=None,
            target_status=AdmissionsApplication.STATUS_ENROLLED,
            academic_year=year,
        )
    assert result is None
    assert error is not None and error.status_code == 409
    assert error.data["code"] == "historical_admissions_provenance_conflict"
    historical.refresh_from_db()
    assert historical.status == AdmissionsApplication.STATUS_ACCEPTED
    assert historical.notes_internal == notes
    assert AdmissionsApplication.objects.filter(student=student).count() == 1


def test_verified_legacy_sync_rejects_duplicate_historical_rows():
    school, family, application, _, student, year, context = _legacy_sync_fixture()
    for _ in range(2):
        AdmissionsApplication.objects.create(
            school=school, academic_year=year, family=family, student=student,
            status=AdmissionsApplication.STATUS_ACCEPTED,
            notes_internal=f"canonical_application_id={application.id}",
        )
    with transaction.atomic():
        result, error = _upsert_verified_legacy_admissions(
            school=school, context=context, actor_user=None,
            target_status=AdmissionsApplication.STATUS_ENROLLED,
            academic_year=year,
        )
    assert result is None
    assert error is not None and error.status_code == 409
    assert AdmissionsApplication.objects.filter(
        student=student, status=AdmissionsApplication.STATUS_ENROLLED,
    ).count() == 0


def test_verified_legacy_sync_does_not_downgrade_historical_enrollment():
    school, family, application, _, student, year, context = _legacy_sync_fixture()
    historical = AdmissionsApplication.objects.create(
        school=school, academic_year=year, family=family, student=student,
        status=AdmissionsApplication.STATUS_ENROLLED,
        notes_internal=f"canonical_application_id={application.id}",
    )
    with transaction.atomic():
        result, error = _upsert_verified_legacy_admissions(
            school=school, context=context, actor_user=None,
            target_status=AdmissionsApplication.STATUS_ACCEPTED,
            academic_year=year,
        )
    assert result is None
    assert error is not None and error.status_code == 409
    historical.refresh_from_db()
    assert historical.status == AdmissionsApplication.STATUS_ENROLLED


def test_verified_legacy_sync_rolls_back_first_member_on_second_member_conflict():
    school, family, application, _, first_core, year, context = _legacy_sync_fixture()
    household = application.household
    other_compat = CompatibilityStudent.objects.create(
        school_id=school.id, household=household, first_name="Grace",
        last_name="Hopper", grade_level="5",
    )
    other_applicant = application.applicants.create(
        school_id=school.id, student=other_compat, first_name="Grace",
        last_name="Hopper", dob=date(2015, 2, 2), grade_applying_for="5",
    )
    other_core = CoreStudent.objects.create(
        school=school, family=family, student_number="S-1002",
        first_name="Grace", last_name="Hopper", dob=other_applicant.dob,
        status="ACTIVE",
    )
    StudentIdentityLink.objects.create(
        school=school, core_student=other_core, compatibility_student=other_compat,
        source=StudentIdentityLink.SOURCE_ADMISSIONS,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
        evidence_reference=(
            f"application:{application.id}:applicant:{other_applicant.id}"
        ),
    )
    CoreEnrollment.objects.create(
        school=school, student=other_core, academic_year=year,
        grade_level=GradeLevel.objects.get(school=school, code="5"),
        start_date=year.start_date, status="ENROLLED",
    )
    conflict = AdmissionsApplication.objects.create(
        school=school, family=family, student=other_core, academic_year=year,
        status=AdmissionsApplication.STATUS_ACCEPTED,
        notes_internal="canonical_application_id=not-owned",
    )
    with transaction.atomic():
        current, error = _verified_admissions_context(
            school=school, application_id=application.id,
        )
        assert error is None and current is not None
        result, sync_error = _upsert_verified_legacy_admissions(
            school=school, context=current, actor_user=None,
            target_status=AdmissionsApplication.STATUS_ENROLLED,
            academic_year=year,
        )
    assert result is None
    assert sync_error is not None and sync_error.status_code == 409
    assert AdmissionsApplication.objects.filter(student=first_core).count() == 0
    conflict.refresh_from_db()
    assert conflict.notes_internal == "canonical_application_id=not-owned"
    assert conflict.status == AdmissionsApplication.STATUS_ACCEPTED


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
