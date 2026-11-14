from __future__ import annotations

from datetime import date

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from admissions.models import AdmissionsApplication, AdmissionsAuditEvent
from applications.models import Application, Applicant, ApplicationEvent, EnrollmentContract, EnrollmentContractStatus
from applications.services import has_verified_student_enrollments
from enrollment_conversion_wizard.models import EnrollmentConversionWizardSession
from core.models import AcademicYear, CrownPermission, Enrollment as CoreEnrollment, Family, RolePermission, Student as CoreStudent, StudentIdentityLink
from households.models import Household, Student

from sandbox_demo.catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS
from sandbox_demo.parent_enrollment import SandboxParentEnrollmentError, seed_parent_enrollment_scenario
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
    _assert_continuity(completed.data, "completed")
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
    assert identity.core_student.student_number == f"HCA-DEMO-{application_id.replace('-', '')}"
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
    _assert_continuity(reread.data, "completed")
    overview = client.get("/api/v1/parent360/me/overview/")
    assert overview.status_code == 200, overview.data
    rows = overview.data["admissions_continuity"]["applications"]
    row = next(item for item in rows if item["application_id"] == str(application_id))
    _assert_continuity(row, "completed")
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


def _post_parent_enrollment(client, application_id, *, accepted_terms=True):
    payload = {"application_id": application_id, "accepted_terms": accepted_terms}
    return client.post("/api/v1/sandbox/parent/enrollment/", payload, format="json")


def _assert_continuity(data, expected):
    for key in ("applicant_to_student_status", "classroom_readiness_status",
                "parent_portal_activation_status"):
        assert data[key] == expected


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_parent_enrollment_missing_dob_fails_closed_without_core_writes():
    school, parent, application_id = _setup()
    applicant = Applicant.objects.get(application_id=application_id)
    applicant.dob = None
    applicant.save(update_fields=["dob", "updated_at"])
    client = _client(parent, school)

    response = _post_parent_enrollment(client, application_id)
    assert response.status_code == 409, response.data
    assert response.data["code"] == "verified_date_of_birth_required"
    assert not CoreStudent.objects.filter(
        school_id=school.id,
        student_number=f"HCA-DEMO-{application_id.replace('-', '')}",
    ).exists()
    assert not ApplicationEvent.objects.filter(
        application_id=application_id, event_type="enrollment_confirmed",
    ).exists()
    reread = client.get(f"/api/v1/sandbox/parent/enrollment/?application_id={application_id}")
    assert reread.status_code == 200
    assert reread.data["lifecycle_stage"] == "accepted"


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_parent_enrollment_readback_does_not_certify_deleted_identity(settings, monkeypatch):
    _dev_parent_overview_runtime(settings, monkeypatch)
    school, parent, application_id = _setup()
    client = _client(parent, school)
    done = _post_parent_enrollment(client, application_id)
    assert done.status_code == 200, done.data
    identity = StudentIdentityLink.objects.get(
        school_id=school.id, compatibility_student_id=done.data["child_id"],
    )
    identity.delete()
    reread = client.get(f"/api/v1/sandbox/parent/enrollment/?application_id={application_id}")
    assert reread.status_code == 200
    assert reread.data["lifecycle_stage"] == "enrolled"
    _assert_continuity(reread.data, "in_progress")
    overview = client.get("/api/v1/parent360/me/overview/")
    assert overview.status_code == 200, overview.data
    rows = overview.data["admissions_continuity"]["applications"]
    row = next(item for item in rows if item["application_id"] == str(application_id))
    _assert_continuity(row, "in_progress")


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_parent_synthetic_scenario_can_reset_after_verified_enrollment():
    school, parent, old_id = _setup()
    client = _client(parent, school)
    done = _post_parent_enrollment(client, old_id)
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

@pytest.mark.parametrize("tamper", ["identity_evidence", "identity_family", "academic_year"])
@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_completed_enrollment_rejects_unrelated_canonical_proof(tamper):
    school, parent, application_id = _setup()
    client = _client(parent, school)
    completed = _post_parent_enrollment(client, application_id)
    assert completed.status_code == 200, completed.data
    applicant = Applicant.objects.get(application_id=application_id)
    identity = StudentIdentityLink.objects.get(
        school_id=school.id, compatibility_student_id=applicant.student_id,
    )
    if tamper == "identity_evidence":
        identity.evidence_reference = (
            f"application:00000000-0000-0000-0000-000000000001:applicant:{applicant.id}"
        )
        identity.save(update_fields=["evidence_reference"])
    elif tamper == "identity_family":
        other_family = Family.objects.create(
            school=school, family_name="Unrelated verified family"
        )
        identity.core_student.family = other_family
        identity.core_student.save(update_fields=["family"])
    else:
        prior_year = AcademicYear.objects.create(
            school=school, name="2024-2025", start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 5), is_current=False,
        )
        enrollment = CoreEnrollment.objects.get(student=identity.core_student)
        enrollment.academic_year = prior_year
        enrollment.save(update_fields=["academic_year"])

    application = Application.objects.get(pk=application_id)
    assert not has_verified_student_enrollments(application)
    reread = client.get(f"/api/v1/sandbox/parent/enrollment/?application_id={application_id}")
    assert reread.status_code == 200, reread.data
    _assert_continuity(reread.data, "in_progress")
    replay = _post_parent_enrollment(client, application_id)
    assert replay.status_code == 409, replay.data
    assert replay.data["code"] == "canonical_enrollment_verification_failed"


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_seed_reset_preserves_same_name_application_and_other_household_student():
    school, parent, application_id = _setup()
    client = _client(parent, school)
    completed = _post_parent_enrollment(client, application_id)
    assert completed.status_code == 200, completed.data
    scenario = Application.objects.get(pk=application_id)
    unrelated_child = Student.objects.create(
        school_id=school.id,
        household=scenario.household,
        first_name="Unrelated",
        last_name="Child",
        grade_level="6",
    )
    unrelated_household = Household.objects.create(
        school_id=school.id, name="Ordinary admissions household"
    )
    unrelated_app = Application.objects.create(
        school_id=school.id, household=unrelated_household
    )
    Applicant.objects.create(
        school_id=school.id, application=unrelated_app,
        first_name="Jordan", last_name="Reed",
        grade_applying_for="7", dob=date(2013, 2, 15),
    )
    new_scenario = seed_parent_enrollment_scenario()
    assert new_scenario["parent_enrollment_application_id"] != str(application_id)
    assert not Application.objects.filter(pk=application_id).exists()
    assert Application.objects.filter(pk=unrelated_app.id).exists()
    assert Student.objects.filter(pk=unrelated_child.id).exists()
    assert Household.objects.filter(pk=scenario.household_id).exists()
    assert not Student.objects.filter(pk=completed.data["child_id"]).exists()


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_parent_reset_preserves_legacy_audit_history():
    school, parent, application_id = _setup()
    response = _post_parent_enrollment(_client(parent, school), application_id)
    assert response.status_code == 200, response.data
    legacy = AdmissionsApplication.objects.get(
        school=school,
        notes_internal__contains=f"canonical_application_id={application_id}",
    )
    receipt = AdmissionsAuditEvent.log(
        school=school, entity_type=AdmissionsAuditEvent.ENTITY_APPLICATION,
        entity_id=legacy.pk, action="TEST_HISTORICAL_RECEIPT",
    )
    with pytest.raises(SandboxParentEnrollmentError, match="reset_historical_admissions_audit_exists"):
        seed_parent_enrollment_scenario()
    assert Application.objects.filter(pk=application_id).exists()
    assert AdmissionsApplication.objects.filter(pk=legacy.pk).exists()
    assert AdmissionsAuditEvent.objects.filter(pk=receipt.pk).exists()


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_parent_reset_preserves_extra_application_event():
    school, parent, application_id = _setup()
    response = _post_parent_enrollment(_client(parent, school), application_id)
    assert response.status_code == 200, response.data
    extra = ApplicationEvent.objects.create(
        school_id=school.id, application_id=application_id,
        event_type="decision_made", payload={"decision": "accepted", "note": "later review"},
    )
    with pytest.raises(SandboxParentEnrollmentError, match="reset_application_history_not_synthetic"):
        seed_parent_enrollment_scenario()
    assert Application.objects.filter(pk=application_id).exists()
    assert ApplicationEvent.objects.filter(pk=extra.pk).exists()


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_parent_reset_refuses_added_applicant_and_preserves_all_records():
    school, _, application_id = _setup()
    application = Application.objects.get(pk=application_id)
    original = application.applicants.get()
    other = Applicant.objects.create(
        school_id=school.id, application=application,
        first_name="Unrelated", last_name="Child",
        dob=date(2014, 3, 18), grade_applying_for="6",
    )
    with pytest.raises(SandboxParentEnrollmentError, match="reset_application_history_not_synthetic"):
        seed_parent_enrollment_scenario()
    assert Application.objects.filter(pk=application.pk).exists()
    assert Applicant.objects.filter(pk=original.pk).exists()
    assert Applicant.objects.filter(pk=other.pk).exists()


@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_reset_blocks_cross_year_student_deletion_and_rolls_back():
    school, parent, application_id = _setup()
    client = _client(parent, school)
    completed = _post_parent_enrollment(client, application_id)
    assert completed.status_code == 200, completed.data
    identity = StudentIdentityLink.objects.get(
        school_id=school.id, compatibility_student_id=completed.data["child_id"]
    )
    original = CoreEnrollment.objects.get(student=identity.core_student)
    prior_year = AcademicYear.objects.create(
        school=school, name="2025-2026", start_date=date(2025, 8, 15),
        end_date=date(2026, 6, 5), is_current=False,
    )
    older = CoreEnrollment.objects.create(
        school=school, student=identity.core_student, academic_year=prior_year,
        grade_level=original.grade_level, start_date=date(2025, 8, 15),
        status="ENROLLED",
    )
    with pytest.raises(SandboxParentEnrollmentError, match="reset_student_has_external_enrollment"):
        seed_parent_enrollment_scenario()
    assert Application.objects.filter(pk=application_id).exists()
    assert CoreStudent.objects.filter(pk=identity.core_student_id).exists()
    assert CoreEnrollment.objects.filter(pk=older.pk).exists()
    assert CoreEnrollment.objects.filter(pk=original.pk).exists()

@override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
def test_one_parent_application_replayed_by_registrar_keeps_one_canonical_enrollment(settings, monkeypatch):
    """A real parent -> registrar handoff must preserve the same verified SIS identity."""
    _dev_parent_overview_runtime(settings, monkeypatch)
    school, parent, application_id = _setup()
    registrar = ensure_persona_user(school, SANDBOX_PERSONAS["admissions_director"])
    permission, _ = CrownPermission.objects.get_or_create(
        code="admissions.edit", defaults={"description": "Admissions enrollment write"},
    )
    RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=permission)

    parent_client = _client(parent, school)
    registrar_client = _client(registrar, school)
    before = parent_client.get(
        f"/api/v1/sandbox/parent/enrollment/?application_id={application_id}"
    )
    assert before.status_code == 200, before.data
    assert before.data["lifecycle_stage"] == "accepted"

    completed = _post_parent_enrollment(parent_client, application_id)
    assert completed.status_code == 200, completed.data
    assert completed.data["lifecycle_stage"] == "enrolled"
    assert completed.data["applicant_to_student_status"] == "completed"
    assert completed.data["demo_payment_processed"] is False

    applicant = Applicant.objects.get(application_id=application_id)
    identity = StudentIdentityLink.objects.get(
        school=school, compatibility_student_id=completed.data["child_id"],
    )
    assert identity.verification_status == StudentIdentityLink.STATUS_VERIFIED
    assert identity.evidence_reference == f"application:{application_id}:applicant:{applicant.id}"
    legacy = AdmissionsApplication.objects.get(
        school=school, notes_internal=f"canonical_application_id={application_id}",
    )
    assert legacy.status == AdmissionsApplication.STATUS_ENROLLED
    assert legacy.student_id == identity.core_student_id
    assert CoreEnrollment.objects.filter(
        school=school, student_id=identity.core_student_id,
        academic_year=legacy.academic_year, status="ENROLLED",
    ).count() == 1
    sessions_before = EnrollmentConversionWizardSession.objects.filter(
        school=school, status=EnrollmentConversionWizardSession.STATUS_VERIFIED,
    ).count()
    assert sessions_before >= 1

    # Parent cannot exercise the staff conversion endpoint, and registrar replay
    # must not fabricate a second enrollment, event, identity or wizard record.
    payload = {"application_id": legacy.id}
    denied = parent_client.post("/api/admissions/enroll/", payload, format="json")
    assert denied.status_code == 403, denied.data

    for _ in range(2):
        replay = registrar_client.post("/api/admissions/enroll/", payload, format="json")
        assert replay.status_code == 200, replay.data
        assert replay.data["ok"] is True
        assert replay.data["already_enrolled"] is True
        assert replay.data["canonical_application_id"] == str(application_id)
        assert replay.data["student_id"] == str(identity.core_student_id)
        assert replay.data["canonical_gate"] == "verified_identity_and_core_enrollment"

    assert AdmissionsApplication.objects.filter(
        school=school, notes_internal=f"canonical_application_id={application_id}",
    ).count() == 1
    assert CoreEnrollment.objects.filter(
        school=school, student_id=identity.core_student_id,
        academic_year=legacy.academic_year, status="ENROLLED",
    ).count() == 1
    assert StudentIdentityLink.objects.filter(
        school=school, compatibility_student_id=completed.data["child_id"],
    ).count() == 1
    assert ApplicationEvent.objects.filter(
        application_id=application_id, event_type="enrollment_confirmed",
    ).count() == 1
    assert EnrollmentConversionWizardSession.objects.filter(
        school=school, status=EnrollmentConversionWizardSession.STATUS_VERIFIED,
    ).count() == sessions_before

    reread = parent_client.get(
        f"/api/v1/sandbox/parent/enrollment/?application_id={application_id}"
    )
    assert reread.status_code == 200, reread.data
    assert reread.data["lifecycle_stage"] == "enrolled"
    assert str(reread.data["child_id"]) == str(completed.data["child_id"])
    _assert_continuity(reread.data, "completed")
    overview = parent_client.get("/api/v1/parent360/me/overview/")
    assert overview.status_code == 200, overview.data
    row = next(
        item for item in overview.data["admissions_continuity"]["applications"]
        if item["application_id"] == str(application_id)
    )
    assert row["lifecycle_stage"] == "enrolled"
    _assert_continuity(row, "completed")

