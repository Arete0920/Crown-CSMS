import pytest
from rest_framework.test import APIClient

from admissions.models import AdmissionsApplication
from applications.models import Application, Applicant, ApplicationEvent
from core.models import Enrollment, HouseholdFamilyLink, StudentIdentityLink, UserAccount
from households.models import Household
from sandbox_demo.admissions_conversion_seed import (
    SCHOOL_ID, FIXTURE_MARKER, reset_heritage_admissions_conversion_scenario,
    seed_heritage_admissions_conversion_scenario,
)
from sandbox_demo.services import create_sandbox_session, seed_heritage_flagship

pytestmark = pytest.mark.django_db(transaction=True)


def _client(user):
    client = APIClient(); client.force_authenticate(user=user); client.credentials(HTTP_X_SCHOOL_ID=str(SCHOOL_ID)); return client


def _seed(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    create_sandbox_session(persona_key="admissions_director", school_key_or_id="heritage-core", guidance="guided")
    create_sandbox_session(persona_key="parent", school_key_or_id="heritage-core", guidance="guided")
    return seed_heritage_admissions_conversion_scenario()


def test_admissions_director_converts_canonical_ready_applicant_and_updates_metrics(settings):
    seeded = _seed(settings); director = UserAccount.objects.get(school_id=SCHOOL_ID, username="admissions@heritage.example.org"); client = _client(director)
    response = client.post("/api/admissions/enroll/", {"application_id": seeded["admissions_conversion_legacy_application_id"]}, format="json")
    assert response.status_code == 200, response.data; assert response.data["ok"] is True; assert response.data["already_enrolled"] is False
    assert response.data["student_id"] == seeded["admissions_conversion_student_id"]; assert response.data["canonical_application_id"] == seeded["admissions_conversion_canonical_application_id"]
    assert response.data["canonical_gate"] == "contract_countersigned_and_deposit_paid_or_waived"
    legacy = AdmissionsApplication.objects.get(id=seeded["admissions_conversion_legacy_application_id"]); assert legacy.status == AdmissionsApplication.STATUS_ENROLLED
    assert ApplicationEvent.objects.filter(school_id=SCHOOL_ID, application_id=seeded["admissions_conversion_canonical_application_id"], event_type="enrollment_confirmed").exists()
    summary = client.get("/api/v1/admissions/summary/"); assert summary.status_code == 200, summary.data; assert int(summary.data["pipeline"]["by_stage"]["enrolled"]) >= 1
    replay = client.post("/api/admissions/enroll/", {"application_id": seeded["admissions_conversion_legacy_application_id"]}, format="json")
    assert replay.status_code == 200, replay.data; assert replay.data["already_enrolled"] is True; assert replay.data["student_id"] == seeded["admissions_conversion_student_id"]


def test_parent_cannot_execute_staff_enrollment_conversion(settings):
    seeded = _seed(settings); parent = UserAccount.objects.get(school_id=SCHOOL_ID, username="parent.reed@heritage.example.org")
    response = _client(parent).post("/api/admissions/enroll/", {"application_id": seeded["admissions_conversion_legacy_application_id"]}, format="json")
    assert response.status_code == 403; assert response.data["detail"] == "Permission denied."
    legacy = AdmissionsApplication.objects.get(id=seeded["admissions_conversion_legacy_application_id"]); assert legacy.status == AdmissionsApplication.STATUS_ACCEPTED


def test_seed_has_real_verified_identity_and_school_year_enrollment(settings):
    seeded = _seed(settings)
    canonical = Application.objects.get(pk=seeded["admissions_conversion_canonical_application_id"])
    applicant = canonical.applicants.get()
    assert applicant.dob is not None
    assert applicant.flags["heritage_conversion_fixture"] == FIXTURE_MARKER
    assert applicant.student_id is not None
    link = StudentIdentityLink.objects.get(compatibility_student_id=applicant.student_id)
    assert link.verification_status == StudentIdentityLink.STATUS_VERIFIED
    assert link.source == StudentIdentityLink.SOURCE_ADMISSIONS
    assert link.evidence_reference == f"application:{canonical.id}:applicant:{applicant.id}"
    assert link.core_student_id == seeded["admissions_conversion_student_id"]
    assert HouseholdFamilyLink.objects.filter(
        school_id=SCHOOL_ID, household_id=canonical.household_id,
        family_id=link.core_student.family_id,
    ).count() == 1
    assert Enrollment.objects.filter(
        pk=seeded["admissions_conversion_enrollment_id"],
        school_id=SCHOOL_ID, student_id=link.core_student_id,
        grade_level__code="8", status="ENROLLED",
    ).exists()


def test_seed_uses_exact_canonical_provenance_contract(settings):
    """Single enrollment must never adopt a descriptive or ambiguous marker."""
    seeded = _seed(settings)
    legacy = AdmissionsApplication.objects.get(
        pk=seeded["admissions_conversion_legacy_application_id"]
    )
    canonical = seeded["admissions_conversion_canonical_application_id"]
    expected_reference = f"canonical_application_id={canonical}"
    assert legacy.notes_internal == expected_reference
    # Mirrors the historical-provenance guard in the single-enroll API.
    recorded = [
        line.strip()
        for line in legacy.notes_internal.splitlines()
        if "canonical_application_id=" in line
    ]
    assert recorded == [expected_reference]


def test_marked_reset_preserves_unrelated_same_name_application(settings):
    seeded = _seed(settings)
    other_household = Household.objects.create(
        school_id=SCHOOL_ID, name="Unrelated same-name household",
    )
    unrelated = Application.objects.create(
        school_id=SCHOOL_ID, household=other_household,
    )
    sibling = Applicant.objects.create(
        school_id=SCHOOL_ID, application=unrelated,
        first_name="Taylor", last_name="Mercer", grade_applying_for="8",
    )

    reset_heritage_admissions_conversion_scenario()
    assert Application.objects.filter(pk=unrelated.pk).exists()
    assert Applicant.objects.filter(pk=sibling.pk).exists()
    assert not Application.objects.filter(
        pk=seeded["admissions_conversion_canonical_application_id"]
    ).exists()
    assert not Enrollment.objects.filter(
        pk=seeded["admissions_conversion_enrollment_id"]
    ).exists()
    assert not StudentIdentityLink.objects.filter(
        core_student_id=seeded["admissions_conversion_student_id"]
    ).exists()


def test_repeated_seed_replaces_only_explicit_fictional_fixture(settings):
    original = _seed(settings)
    later = seed_heritage_admissions_conversion_scenario()
    assert original["admissions_conversion_legacy_application_id"] != later[
        "admissions_conversion_legacy_application_id"
    ]
    assert Enrollment.objects.filter(
        pk=later["admissions_conversion_enrollment_id"]
    ).exists()
    assert not Enrollment.objects.filter(
        pk=original["admissions_conversion_enrollment_id"]
    ).exists()
    assert Applicant.objects.filter(
        school_id=SCHOOL_ID,
        flags__heritage_conversion_fixture=FIXTURE_MARKER,
    ).count() == 1


def test_marked_reset_refuses_conversion_history_and_keeps_audit(settings):
    seeded = _seed(settings)
    from admissions.services import finalize_enrollment
    from admissions.models import AdmissionsAuditEvent

    legacy_id = seeded["admissions_conversion_legacy_application_id"]
    legacy = AdmissionsApplication.objects.get(pk=legacy_id)
    converted, changed = finalize_enrollment(legacy)
    assert changed is True
    assert converted.status == AdmissionsApplication.STATUS_ENROLLED
    audit = AdmissionsAuditEvent.objects.get(
        school_id=SCHOOL_ID,
        entity_type=AdmissionsAuditEvent.ENTITY_APPLICATION,
        entity_id=str(legacy.pk),
        action="STATUS_ENROLLED",
    )
    with pytest.raises(ValueError, match="audit history"):
        reset_heritage_admissions_conversion_scenario()
    assert AdmissionsApplication.objects.filter(
        pk=legacy_id, status=AdmissionsApplication.STATUS_ENROLLED
    ).exists()
    assert AdmissionsAuditEvent.objects.filter(pk=audit.pk).exists()
    assert Enrollment.objects.filter(
        pk=seeded["admissions_conversion_enrollment_id"]
    ).exists()
    assert StudentIdentityLink.objects.filter(
        core_student_id=seeded["admissions_conversion_student_id"]
    ).exists()


def test_marked_reset_refuses_unexpected_workflow_events(settings):
    seeded = _seed(settings)
    ApplicationEvent.objects.create(
        school_id=SCHOOL_ID,
        application_id=seeded["admissions_conversion_canonical_application_id"],
        event_type="enrollment_confirmed",
        payload={"source": "fictional_history_regression"},
    )
    with pytest.raises(ValueError, match="audit history"):
        reset_heritage_admissions_conversion_scenario()
    assert Application.objects.filter(
        pk=seeded["admissions_conversion_canonical_application_id"]
    ).exists()


def test_reset_refuses_duplicate_event_of_allowed_type(settings):
    seeded = _seed(settings)
    app_id = seeded["admissions_conversion_canonical_application_id"]
    original = ApplicationEvent.objects.get(
        application_id=app_id, event_type="decision_made",
    )
    added = ApplicationEvent.objects.create(
        school_id=SCHOOL_ID,
        application_id=app_id,
        event_type="decision_made",
        payload={"decision": "accepted", "updated_by": "real_workflow"},
    )
    with pytest.raises(ValueError, match="audit history"):
        reset_heritage_admissions_conversion_scenario()
    assert ApplicationEvent.objects.filter(pk=original.pk).exists()
    assert ApplicationEvent.objects.filter(pk=added.pk).exists()
    assert AdmissionsApplication.objects.filter(
        pk=seeded["admissions_conversion_legacy_application_id"],
        status=AdmissionsApplication.STATUS_ACCEPTED,
    ).exists()


def test_reset_refuses_modified_seed_event_evidence(settings):
    seeded = _seed(settings)
    submitted = ApplicationEvent.objects.get(
        application_id=seeded["admissions_conversion_canonical_application_id"],
        event_type="application_submitted",
    )
    submitted.payload = {
        "via": "modified_workflow",
        "applicant_id": submitted.payload["applicant_id"],
    }
    submitted.save(update_fields=["payload", "updated_at"])
    with pytest.raises(ValueError, match="audit history"):
        reset_heritage_admissions_conversion_scenario()
    submitted.refresh_from_db()
    assert submitted.payload["via"] == "modified_workflow"
    assert Enrollment.objects.filter(
        pk=seeded["admissions_conversion_enrollment_id"],
    ).exists()
