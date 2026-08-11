from __future__ import annotations

from datetime import date

from admissions.models import AdmissionsApplication
from core.models import AcademicYear, Family, GradeLevel, School, Student

from .catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS
from .permissions import ensure_sandbox_role_permissions
from .services import ensure_persona_user


SCHOOL_ID = SANDBOX_SCHOOLS["heritage-core"].id
FAMILY_NAME = "Carter Admissions Demo Family"
STUDENT_NUMBER = "HCA-ADM-001"
STUDENT_FIRST = "Micah"
STUDENT_LAST = "Carter"


def reset_heritage_admissions_scenario() -> None:
    school = School.objects.filter(pk=SCHOOL_ID).first()
    if not school:
        return
    family = Family.objects.filter(school=school, family_name=FAMILY_NAME).first()
    if not family:
        return
    AdmissionsApplication.objects.filter(school=school, family=family).delete()
    Student.objects.filter(school=school, family=family, student_number=STUDENT_NUMBER).delete()
    family.delete()


def seed_heritage_admissions_scenario() -> dict[str, str]:
    school = School.objects.get(pk=SCHOOL_ID)
    director = ensure_persona_user(school, SANDBOX_PERSONAS["admissions_director"])
    ensure_sandbox_role_permissions(SANDBOX_PERSONAS["admissions_director"].role_code)
    reset_heritage_admissions_scenario()

    year = AcademicYear.objects.filter(school=school, is_current=True).order_by("-start_date").first()
    if year is None:
        year = AcademicYear.objects.create(
            school=school,
            name="2026-2027",
            start_date=date(2026, 8, 15),
            end_date=date(2027, 6, 15),
            is_current=True,
        )
    grade = GradeLevel.objects.filter(school=school, code="7").first()
    family = Family.objects.create(
        school=school,
        family_name=FAMILY_NAME,
        address_line1="700 Admissions Way",
        city="Fairview",
        state="PA",
        zip_code="19000",
        status="ACTIVE",
    )
    student = Student.objects.create(
        school=school,
        family=family,
        student_number=STUDENT_NUMBER,
        first_name=STUDENT_FIRST,
        last_name=STUDENT_LAST,
        dob=date(2013, 5, 12),
        status="APPLICANT",
        current_grade_level=grade,
    )
    application = AdmissionsApplication.objects.create(
        school=school,
        academic_year=year,
        family=family,
        student=student,
        status=AdmissionsApplication.STATUS_UNDER_REVIEW,
        gpa="3.70",
        test_score=88,
        essay_received=True,
        recommendations_received=2,
        transcript_received=True,
        notes_internal="Protected sandbox applicant for Admissions Director functional-depth proof.",
    )
    application.submitted_at = application.created_at
    application.save(update_fields=["submitted_at", "updated_at"])

    return {
        "admissions_demo_application_id": str(application.id),
        "admissions_demo_academic_year_id": str(year.id),
        "admissions_demo_director_email": director.email,
        "admissions_demo_student": f"{STUDENT_FIRST} {STUDENT_LAST}",
    }
