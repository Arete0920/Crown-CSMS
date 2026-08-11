from __future__ import annotations

from datetime import date

from django.db import transaction
from django.utils import timezone

from admissions.models import AdmissionsApplication
from applications.models import Application, Applicant, ApplicationEvent, ApplicationStatus, EnrollmentContract, EnrollmentContractStatus
from core.models import AcademicYear, Family, GradeLevel, School, Student, UserAccount
from households.models import Household
from .catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS
from .permissions import ensure_sandbox_role_permissions

SCHOOL_ID = SANDBOX_SCHOOLS["heritage-core"].id
FAMILY_NAME = "Mercer Enrollment Conversion Demo Family"
HOUSEHOLD_NAME = FAMILY_NAME
STUDENT_NUMBER = "HCA-ENR-001"
STUDENT_FIRST = "Taylor"
STUDENT_LAST = "Mercer"
GRADE_CODE = "8"


def reset_heritage_admissions_conversion_scenario() -> None:
    school = School.objects.filter(pk=SCHOOL_ID).first()
    if school is None: return
    canonical_apps = list(Application.objects.filter(school_id=SCHOOL_ID, applicants__first_name=STUDENT_FIRST, applicants__last_name=STUDENT_LAST).select_related("household").distinct())
    household_ids = {app.household_id for app in canonical_apps if app.household_id}
    for app in canonical_apps: app.delete()
    if household_ids: Household.objects.filter(school_id=SCHOOL_ID, id__in=household_ids, applications__isnull=True).delete()
    family = Family.objects.filter(school=school, family_name=FAMILY_NAME).first()
    if family is not None:
        AdmissionsApplication.objects.filter(school=school, family=family).delete(); Student.objects.filter(school=school, family=family, student_number=STUDENT_NUMBER).delete(); family.delete()


@transaction.atomic
def seed_heritage_admissions_conversion_scenario() -> dict[str, str]:
    school = School.objects.get(pk=SCHOOL_ID)
    director = UserAccount.objects.get(school=school, username=SANDBOX_PERSONAS["admissions_director"].email)
    ensure_sandbox_role_permissions(SANDBOX_PERSONAS["admissions_director"].role_code); reset_heritage_admissions_conversion_scenario()
    year = AcademicYear.objects.filter(school=school, is_current=True).order_by("-start_date").first()
    if year is None: year = AcademicYear.objects.create(school=school, name="2026-2027", start_date=date(2026, 8, 15), end_date=date(2027, 6, 15), is_current=True)
    grade = GradeLevel.objects.filter(school=school, code=GRADE_CODE).first()
    family = Family.objects.create(school=school, family_name=FAMILY_NAME, address_line1="800 Enrollment Way", city="Fairview", state="PA", zip_code="19000", status="ACTIVE")
    core_student = Student.objects.create(school=school, family=family, student_number=STUDENT_NUMBER, first_name=STUDENT_FIRST, last_name=STUDENT_LAST, dob=date(2012, 3, 14), status="APPLICANT", current_grade_level=grade)
    household = Household.objects.create(school_id=SCHOOL_ID, name=HOUSEHOLD_NAME, address1="800 Enrollment Way", city="Fairview", state="PA", postal_code="19000", is_active=True)
    canonical = Application.objects.create(school_id=SCHOOL_ID, household=household, status=ApplicationStatus.DECIDED, submitted_at=timezone.now(), decided_at=timezone.now())
    applicant = Applicant.objects.create(school_id=SCHOOL_ID, application=canonical, first_name=STUDENT_FIRST, last_name=STUDENT_LAST, grade_applying_for=GRADE_CODE, source="church_referral", flags={"sandbox_demo": True, "conversion_ready": True})
    ApplicationEvent.objects.create(school_id=SCHOOL_ID, application=canonical, event_type="application_submitted", payload={"via": "sandbox_admissions_conversion", "applicant_id": str(applicant.id)})
    ApplicationEvent.objects.create(school_id=SCHOOL_ID, application=canonical, event_type="decision_made", payload={"decision": "accepted", "updated_by": director.email})
    contract = EnrollmentContract.objects.create(school_id=SCHOOL_ID, application=canonical, version=1, status=EnrollmentContractStatus.COUNTERSIGNED, line_items=[{"label": "Grade 8 Published Tuition", "category": "tuition", "amount_cents": 995000}], contract_totals={"gross_tuition_cents": 995000, "net_family_obligation_cents": 995000}, net_amount_cents=995000, currency="USD", responsible_payer="fictional.guardian@heritage.example.org", note="Protected fictional sandbox contract; no external payment is processed.", issued_at=timezone.now(), signed_at=timezone.now(), countersigned_at=timezone.now(), created_by=director.email)
    ApplicationEvent.objects.create(school_id=SCHOOL_ID, application=canonical, event_type="enrollment_state_updated", payload={"contract_status": "countersigned", "deposit_status": "paid", "note": "Protected fictional sandbox readiness; no provider transaction.", "transition_reason": "sandbox_admissions_conversion_seed", "updated_by": director.email, "demo_payment_processed": False})
    legacy = AdmissionsApplication.objects.create(school=school, academic_year=year, family=family, student=core_student, status=AdmissionsApplication.STATUS_ACCEPTED, gpa="3.80", test_score=91, essay_received=True, recommendations_received=2, transcript_received=True, notes_internal=f"Protected sandbox enrollment-ready applicant. canonical_application_id={canonical.id}")
    legacy.submitted_at = legacy.created_at; legacy.save(update_fields=["submitted_at", "updated_at"])
    return {"admissions_conversion_legacy_application_id": str(legacy.id), "admissions_conversion_canonical_application_id": str(canonical.id), "admissions_conversion_contract_id": str(contract.id), "admissions_conversion_student_id": str(core_student.id), "admissions_conversion_director_email": director.email}
