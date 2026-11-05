from __future__ import annotations

from datetime import date

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from admissions.models import AdmissionsApplication
from applications.models import Applicant, ApplicationEvent, EnrollmentContract, EnrollmentContractStatus
from enrollment_conversion_wizard.models import EnrollmentConversionWizardSession
from core.models import Enrollment as CoreEnrollment, Student as CoreStudent, StudentIdentityLink
from households.models import Student

from sandbox_demo.catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS
from sandbox_demo.parent_enrollment import seed_parent_enrollment_scenario
from sandbox_demo.services import ensure_demo_school, ensure_persona_user


pytestmark = pytest.mark.django_db


def _setup():
    school = ensure_demo_school(SANDBOX_SCHOOLS["heritage-core"])
    parent = ensure_persona_user(school, SANDBOX_PERSONAS["parent"])
    ensure_persona_user(school, SANDBOX_PERSONAS["school_admin"])
    seeded = seed_parent_enrollment_scenario()
    return school, parent, seeded["parent_enrollment_application_id"]


def _client(parent, school):
    client = APIClient()
    client.force_authenticate(parent)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return client



def _dev_parent_overview_runtime(settings, monkeypatch):
    """Exercise the narrowly scoped Heritage DEV parent continuity path."""
    settings.DEBUG = False
    settings.ENVIRONMENT = "dev"
    settings.CROWN_ENV = "dev"
    settings.DJANGO_ENV = ""
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    monkeypatch.setenv("CROWN_SANDBOX_ALLOW_OPEN_SESSION", "true")
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("CROWN_ENV", "dev")
    monkeypatch.setenv("DJANGO_ENV", "")
    monkeypatch.delenv("WEBSITE_HOSTNAME", raising=False)


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_parent_enrollment_api_completes_real_records_without_external_payment(settings, monkeypatch):
    _dev_parent_overview_runtime(settings, monkeypatch)
    school, parent, application_id = _setup()
    client = _client(parent, school)

    before = client.get(f"/api/v1/sandbox/parent/enrollment/?application_id={application_id}")
    assert before.status_code == 200, before.data
    assert before.data["lifecycle_stage"] == "accepted"
    assert before.data["contract_status"] == "sent"
    assert before.data["deposit_status"] == "invoiced"
    assert before.data["demo_payment_processed"] is False

    missing_terms = client.post(
        "/api/v1/sandbox/parent/enrollment/",
        {"application_id": application_id, "accepted_terms": False},
        format="json",
    )
    assert missing_terms.status_code == 400

    completed = client.post(
        "/api/v1/sandbox/parent/enrollment/",
        {"application_id": application_id, "accepted_terms": True},
        format="json",
    )
    assert completed.status_code == 200, completed.data
    assert completed.data["lifecycle_stage"] == "enrolled"
    assert completed.data["contract_status"] == "countersigned"
    assert completed.data["deposit_status"] == "paid"
    assert completed.data["applicant_to_student_status"] == "completed"
    assert completed.data["classroom_readiness_status"] == "completed"
    assert completed.data["parent_portal_activation_status"] == "completed"
    assert completed.data["child_id"]
    assert completed.data["demo_payment_processed"] is False

    contract = EnrollmentContract.objects.get(application_id=application_id)
    assert contract.status == EnrollmentContractStatus.COUNTERSIGNED
    assert contract.signed_at is not None
    assert contract.countersigned_at is not None

    event_types = set(
        ApplicationEvent.objects.filter(application_id=application_id).values_list("event_type", flat=True)
    )
    assert {
        "parent_enrollment_agreement_signed",
        "sandbox_demo_deposit_simulated",
        "enrollment_confirmed",
        "classroom_readiness_completed",
        "parent_portal_activated",
    }.issubset(event_types)
    simulated = ApplicationEvent.objects.get(
        application_id=application_id,
        event_type="sandbox_demo_deposit_simulated",
    )
    assert simulated.payload["payment_processed"] is False

    assert Student.objects.filter(id=completed.data["child_id"], school_id=school.id).exists()
    identity = StudentIdentityLink.objects.get(
        school_id=school.id,
        compatibility_student_id=completed.data["child_id"],
    )
    applicant = Applicant.objects.get(application_id=application_id)
    assert identity.verification_status == StudentIdentityLink.STATUS_VERIFIED
    assert identity.evidence_reference == f"application:{application_id}:applicant:{applicant.id}"
    assert identity.core_student.school_id == school.id
    assert identity.core_student.dob == date(2013, 2, 15)
    canonical_enrollment = CoreEnrollment.objects.get(
        school_id=school.id, student=identity.core_student,
    )
    assert canonical_enrollment.status == "ENROLLED"
    assert canonical_enrollment.academic_year.name == "2026-2027"
    assert canonical_enrollment.grade_level.code == "7"
    assert AdmissionsApplication.objects.filter(
        school=school,
        status=AdmissionsApplication.STATUS_ENROLLED,
        notes_internal__contains=f"canonical_application_id={application_id}",
    ).exists()
    assert EnrollmentConversionWizardSession.objects.filter(
        school=school,
        status=EnrollmentConversionWizardSession.STATUS_VERIFIED,
    ).exists()

    repeat = client.post(
        "/api/v1/sandbox/parent/enrollment/",
        {"application_id": application_id, "accepted_terms": True},
        format="json",
    )
    assert repeat.status_code == 200
    assert repeat.data["lifecycle_stage"] == "enrolled"
    assert CoreEnrollment.objects.filter(
        school_id=school.id, student=identity.core_student,
    ).count() == 1
    assert StudentIdentityLink.objects.filter(
        school_id=school.id, compatibility_student_id=completed.data["child_id"],
    ).count() == 1
    reread = client.get(
        f"/api/v1/sandbox/parent/enrollment/?application_id={application_id}"
    )
    assert reread.status_code == 200, reread.data
    assert reread.data["applicant_to_student_status"] == "completed"
    assert reread.data["classroom_readiness_status"] == "completed"
    assert reread.data["parent_portal_activation_status"] == "completed"
    overview = client.get("/api/v1/parent360/me/overview/")
    assert overview.status_code == 200, overview.data
    row = next(
        row for row in overview.data["admissions_continuity"]["applications"]
        if row["application_id"] == str(application_id)
    )
    assert row["applicant_to_student_status"] == "completed"
    assert row["classroom_readiness_status"] == "completed"
    assert row["parent_portal_activation_status"] == "completed"
    assert ApplicationEvent.objects.filter(
        application_id=application_id,
        event_type="enrollment_confirmed",
    ).count() == 1


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=False)
def test_parent_enrollment_api_is_disabled_outside_open_sandbox():
    school, parent, application_id = _setup()
    client = _client(parent, school)
    response = client.post(
        "/api/v1/sandbox/parent/enrollment/",
        {"application_id": application_id, "accepted_terms": True},
        format="json",
    )
    assert response.status_code == 403
    assert response.data["code"] == "sandbox_open_session_required"


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_parent_enrollment_api_rejects_non_parent_persona():
    school, _parent, application_id = _setup()
    teacher = ensure_persona_user(school, SANDBOX_PERSONAS["teacher"])
    client = _client(teacher, school)
    response = client.post(
        "/api/v1/sandbox/parent/enrollment/",
        {"application_id": application_id, "accepted_terms": True},
        format="json",
    )
    assert response.status_code == 403
    assert response.data["code"] == "heritage_parent_required"


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_parent_enrollment_missing_dob_fails_closed_without_core_writes():
    school, parent, application_id = _setup()
    applicant = Applicant.objects.get(application_id=application_id)
    applicant.dob = None
    applicant.save(update_fields=["dob", "updated_at"])
    client = _client(parent, school)

    response = client.post(
        "/api/v1/sandbox/parent/enrollment/",
        {"application_id": application_id, "accepted_terms": True},
        format="json",
    )
    assert response.status_code == 409, response.data
    assert response.data["code"] == "verified_date_of_birth_required"
    assert not CoreStudent.objects.filter(
        school_id=school.id,
        student_number__startswith=f"APP-{str(application_id).replace('-', '')[:6]}",
    ).exists()
    assert not ApplicationEvent.objects.filter(
        application_id=application_id, event_type="enrollment_confirmed",
    ).exists()
    reread = client.get(
        f"/api/v1/sandbox/parent/enrollment/?application_id={application_id}"
    )
    assert reread.status_code == 200
    assert reread.data["lifecycle_stage"] == "accepted"


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_parent_enrollment_readback_does_not_certify_deleted_identity(settings, monkeypatch):
    _dev_parent_overview_runtime(settings, monkeypatch)
    school, parent, application_id = _setup()
    client = _client(parent, school)
    done = client.post(
        "/api/v1/sandbox/parent/enrollment/",
        {"application_id": application_id, "accepted_terms": True},
        format="json",
    )
    assert done.status_code == 200, done.data
    identity = StudentIdentityLink.objects.get(
        school_id=school.id, compatibility_student_id=done.data["child_id"],
    )
    identity.delete()
    reread = client.get(
        f"/api/v1/sandbox/parent/enrollment/?application_id={application_id}"
    )
    assert reread.status_code == 200
    assert reread.data["lifecycle_stage"] == "enrolled"
    assert reread.data["applicant_to_student_status"] == "in_progress"
    assert reread.data["classroom_readiness_status"] == "in_progress"
    assert reread.data["parent_portal_activation_status"] == "in_progress"
    overview = client.get("/api/v1/parent360/me/overview/")
    assert overview.status_code == 200, overview.data
    row = next(
        row for row in overview.data["admissions_continuity"]["applications"]
        if row["application_id"] == str(application_id)
    )
    assert row["applicant_to_student_status"] == "in_progress"
    assert row["classroom_readiness_status"] == "in_progress"
    assert row["parent_portal_activation_status"] == "in_progress"


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_parent_synthetic_scenario_can_reset_after_verified_enrollment():
    school, parent, old_id = _setup()
    client = _client(parent, school)
    done = client.post(
        "/api/v1/sandbox/parent/enrollment/",
        {"application_id": old_id, "accepted_terms": True},
        format="json",
    )
    assert done.status_code == 200, done.data
    old_child_id = done.data["child_id"]
    old_core_id = StudentIdentityLink.objects.get(
        compatibility_student_id=old_child_id,
    ).core_student_id

    seeded = seed_parent_enrollment_scenario()
    assert seeded["parent_enrollment_application_id"] != str(old_id)
    assert not Student.objects.filter(pk=old_child_id).exists()
    assert not CoreStudent.objects.filter(pk=old_core_id).exists()
    before = client.get(
        "/api/v1/sandbox/parent/enrollment/",
        {"application_id": seeded["parent_enrollment_application_id"]},
    )
    assert before.status_code == 200
    assert before.data["lifecycle_stage"] == "accepted"
