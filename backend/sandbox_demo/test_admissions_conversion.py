import pytest
from rest_framework.test import APIClient

from admissions.models import AdmissionsApplication
from applications.models import ApplicationEvent
from core.models import UserAccount
from sandbox_demo.admissions_conversion_seed import SCHOOL_ID, seed_heritage_admissions_conversion_scenario
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
