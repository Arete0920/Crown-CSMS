"""Fictional Heritage enrollment-conversion proof fixture.

Never select/reset records by a student's name alone. Older unmarked fixture
records are intentionally left intact and require an isolated demo reset.
"""
from __future__ import annotations

from datetime import date

from django.db import transaction
from django.utils import timezone

from admissions.models import AdmissionsApplication
from applications.models import (
    Application, Applicant, ApplicationEvent, ApplicationStatus,
    EnrollmentContract, EnrollmentContractStatus,
)
from core.models import (
    AcademicYear, Enrollment as CoreEnrollment, Family, GradeLevel,
    HouseholdFamilyLink, School, Student, StudentIdentityLink, UserAccount,
)
from households.models import Household, Student as CompatibilityStudent
from .catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS
from .permissions import ensure_sandbox_role_permissions


SCHOOL_ID = SANDBOX_SCHOOLS["heritage-core"].id
FAMILY_NAME = "Mercer Enrollment Conversion Demo Family"
HOUSEHOLD_NAME = FAMILY_NAME
STUDENT_NUMBER = "HCA-ENR-001"
STUDENT_FIRST = "Taylor"
STUDENT_LAST = "Mercer"
GRADE_CODE = "8"
STUDENT_DOB = date(2012, 3, 14)
FIXTURE_MARKER = "heritage-enrollment-conversion-v2"


@transaction.atomic
def reset_heritage_admissions_conversion_scenario() -> None:
    """Delete only a fully proven fixture; refuse mixed/unmarked relationships."""
    school = School.objects.filter(pk=SCHOOL_ID).first()
    if school is None:
        return
    marked = list(
        Applicant.objects.select_related("application__household", "student")
        .filter(school_id=SCHOOL_ID, flags__heritage_conversion_fixture=FIXTURE_MARKER)
        .order_by("pk")[:2]
    )
    if not marked:
        return
    if len(marked) != 1:
        raise ValueError("Ambiguous marked Heritage fixture; do not delete.")

    applicant = marked[0]
    application = applicant.application
    household = application.household
    compatibility = applicant.student
    family = Family.objects.filter(school=school, family_name=FAMILY_NAME).first()
    core = Student.objects.filter(school=school, student_number=STUDENT_NUMBER).first()
    if (
        family is None or core is None or compatibility is None
        or application.school_id != school.pk
        or household.school_id != school.pk
        or household.name != HOUSEHOLD_NAME
        or applicant.application_id != application.id
        or applicant.first_name != STUDENT_FIRST
        or applicant.last_name != STUDENT_LAST
        or applicant.dob != STUDENT_DOB
        or applicant.grade_applying_for != GRADE_CODE
        or compatibility.school_id != school.pk
        or compatibility.household_id != household.pk
        or core.family_id != family.id
        or core.dob != STUDENT_DOB
        or core.first_name != STUDENT_FIRST
        or core.last_name != STUDENT_LAST
        or application.applicants.count() != 1
        or household.applications.count() != 1
        or household.students.count() != 1
        or family.students.count() != 1
    ):
        raise ValueError("Heritage fixture has unexpected identity relationships; manual review required.")

    associations = list(
        HouseholdFamilyLink.objects.filter(
            school=school, household_id=household.pk, family=family
        )[:2]
    )
    links = list(
        StudentIdentityLink.objects.filter(
            school=school, core_student=core,
            compatibility_student=compatibility,
            source=StudentIdentityLink.SOURCE_ADMISSIONS,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
            evidence_reference=f"application:{application.id}:applicant:{applicant.id}",
        )[:2]
    )
    legacy = list(
        AdmissionsApplication.objects.filter(
            school=school, family=family, student=core,
            notes_internal__contains=f"canonical_application_id={application.id}",
        )[:2]
    )
    enrollments = list(CoreEnrollment.objects.filter(school=school, student=core)[:2])
    if (
        len(associations) != 1 or len(links) != 1 or len(legacy) != 1
        or len(enrollments) != 1
        or enrollments[0].academic_year_id != legacy[0].academic_year_id
        or enrollments[0].status != "ENROLLED"
        or AdmissionsApplication.objects.filter(school=school, student=core).count() != 1
        or StudentIdentityLink.objects.filter(core_student=core).count() != 1
    ):
        raise ValueError("Heritage fixture is not fully proven; historical records preserved.")

    # Deletions are only for this exact, explicitly marked fictional fixture.
    # The surrounding atomic transaction rolls back on any protected relation.
    legacy[0].delete()
    enrollments[0].delete()
    links[0].delete()
    application.delete()
    compatibility.delete()
    associations[0].delete()
    household.delete()
    core.delete()
    family.delete()


@transaction.atomic
def seed_heritage_admissions_conversion_scenario() -> dict[str, str]:
    school = School.objects.get(pk=SCHOOL_ID)
    director = UserAccount.objects.get(
        school=school, username=SANDBOX_PERSONAS["admissions_director"].email
    )
    ensure_sandbox_role_permissions(SANDBOX_PERSONAS["admissions_director"].role_code)
    reset_heritage_admissions_conversion_scenario()

    # Legacy fixtures created before marker-based cleanup are never claimed by
    # name; require a new isolated sandbox rather than deleting those records.
    if (
        Family.objects.filter(school=school, family_name=FAMILY_NAME).exists()
        or Student.objects.filter(school=school, student_number=STUDENT_NUMBER).exists()
        or Household.objects.filter(school_id=SCHOOL_ID, name=HOUSEHOLD_NAME).exists()
    ):
        raise ValueError("Unmarked Heritage enrollment fixture exists; use a fresh isolated sandbox.")

    year, _ = AcademicYear.objects.get_or_create(
        school=school, name="2026-2027",
        defaults={
            "start_date": date(2026, 8, 15),
            "end_date": date(2027, 6, 15),
            "is_current": True,
        },
    )
    grade, _ = GradeLevel.objects.get_or_create(
        school=school, code=GRADE_CODE,
        defaults={"label": "Grade 8", "sort_order": 8},
    )
    family = Family.objects.create(
        school=school, family_name=FAMILY_NAME,
        address_line1="800 Enrollment Way", city="Fairview",
        state="PA", zip_code="19000", status="ACTIVE",
    )
    core = Student.objects.create(
        school=school, family=family, student_number=STUDENT_NUMBER,
        first_name=STUDENT_FIRST, last_name=STUDENT_LAST,
        dob=STUDENT_DOB, status="APPLICANT", current_grade_level=grade,
    )
    household = Household.objects.create(
        school_id=SCHOOL_ID, name=HOUSEHOLD_NAME,
        address1="800 Enrollment Way", city="Fairview", state="PA",
        postal_code="19000", is_active=True,
    )
    HouseholdFamilyLink.objects.create(
        school=school, household_id=household.pk, family=family,
        source=HouseholdFamilyLink.SOURCE_ADMISSIONS,
    )
    compatibility = CompatibilityStudent.objects.create(
        school_id=SCHOOL_ID, household=household,
        first_name=STUDENT_FIRST, last_name=STUDENT_LAST,
        grade_level=GRADE_CODE, is_active=True,
    )
    canonical = Application.objects.create(
        school_id=SCHOOL_ID, household=household,
        status=ApplicationStatus.DECIDED,
        submitted_at=timezone.now(), decided_at=timezone.now(),
    )
    applicant = Applicant.objects.create(
        school_id=SCHOOL_ID, application=canonical, student=compatibility,
        first_name=STUDENT_FIRST, last_name=STUDENT_LAST,
        dob=STUDENT_DOB, grade_applying_for=GRADE_CODE,
        source="church_referral",
        flags={
            "sandbox_demo": True, "conversion_ready": True,
            "heritage_conversion_fixture": FIXTURE_MARKER,
        },
    )
    StudentIdentityLink.objects.create(
        school=school, core_student=core, compatibility_student=compatibility,
        source=StudentIdentityLink.SOURCE_ADMISSIONS,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
        evidence_reference=f"application:{canonical.id}:applicant:{applicant.id}",
    )
    canonical_enrollment = CoreEnrollment.objects.create(
        school=school, student=core, academic_year=year,
        grade_level=grade, start_date=year.start_date, status="ENROLLED",
    )
    ApplicationEvent.objects.create(
        school_id=SCHOOL_ID, application=canonical, event_type="application_submitted",
        payload={"via": "sandbox_admissions_conversion", "applicant_id": str(applicant.id)},
    )
    ApplicationEvent.objects.create(
        school_id=SCHOOL_ID, application=canonical, event_type="decision_made",
        payload={"decision": "accepted", "updated_by": director.email},
    )
    contract = EnrollmentContract.objects.create(
        school_id=SCHOOL_ID, application=canonical, version=1,
        status=EnrollmentContractStatus.COUNTERSIGNED,
        line_items=[{
            "label": "Grade 8 Published Tuition", "category": "tuition",
            "amount_cents": 995000,
        }],
        contract_totals={
            "gross_tuition_cents": 995000,
            "net_family_obligation_cents": 995000,
        },
        net_amount_cents=995000, currency="USD",
        responsible_payer="fictional.guardian@heritage.example.org",
        note="Protected fictional sandbox contract; no external payment.",
        issued_at=timezone.now(), signed_at=timezone.now(),
        countersigned_at=timezone.now(), created_by=director.email,
    )
    ApplicationEvent.objects.create(
        school_id=SCHOOL_ID, application=canonical, event_type="enrollment_state_updated",
        payload={
            "contract_status": "countersigned", "deposit_status": "paid",
            "note": "Fictional readiness; no payment provider transaction.",
            "transition_reason": "sandbox_admissions_conversion_seed",
            "updated_by": director.email, "demo_payment_processed": False,
        },
    )
    legacy = AdmissionsApplication.objects.create(
        school=school, academic_year=year, family=family, student=core,
        status=AdmissionsApplication.STATUS_ACCEPTED,
        gpa="3.80", test_score=91, essay_received=True,
        recommendations_received=2, transcript_received=True,
        notes_internal=(
            f"Protected sandbox enrollment-ready applicant. "
            f"canonical_application_id={canonical.id}"
        ),
    )
    legacy.submitted_at = legacy.created_at
    legacy.save(update_fields=["submitted_at", "updated_at"])
    return {
        "admissions_conversion_legacy_application_id": str(legacy.id),
        "admissions_conversion_canonical_application_id": str(canonical.id),
        "admissions_conversion_contract_id": str(contract.id),
        "admissions_conversion_student_id": str(core.id),
        "admissions_conversion_director_email": director.email,
        "admissions_conversion_enrollment_id": str(canonical_enrollment.id),
    }
