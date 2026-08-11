from __future__ import annotations

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from admissions.models import AdmissionsApplication
from applications.models import ApplicationEvent, EnrollmentContract, EnrollmentContractStatus
from enrollment_conversion_wizard.models import EnrollmentConversionWizardSession
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


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_parent_enrollment_api_completes_real_records_without_external_payment():
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
