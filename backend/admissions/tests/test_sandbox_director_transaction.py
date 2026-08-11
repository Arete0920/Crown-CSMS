from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from admissions.models import AdmissionsApplication, AdmissionsAuditEvent, AdmissionsDecision
from core.models import Guardian
from sandbox_demo.admissions_seed import seed_heritage_admissions_scenario
from sandbox_demo.catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS
from sandbox_demo.permissions import ensure_sandbox_role_permissions
from sandbox_demo.services import ensure_demo_school, ensure_persona_user


pytestmark = pytest.mark.django_db


def setup_director():
    school = ensure_demo_school(SANDBOX_SCHOOLS["heritage-core"])
    director = ensure_persona_user(school, SANDBOX_PERSONAS["admissions_director"])
    ensure_sandbox_role_permissions("REGISTRAR")
    seeded = seed_heritage_admissions_scenario()
    client = APIClient()
    client.force_authenticate(director)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return school, director, client, seeded


def test_admissions_director_reviews_contact_checklist_decides_and_metrics_move():
    school, _director, client, seeded = setup_director()
    application_id = seeded["admissions_demo_application_id"]
    year_id = seeded["admissions_demo_academic_year_id"]

    review = client.post(
        "/api/admissions/review-update/",
        {"application_id": application_id},
        format="json",
    )
    assert review.status_code == 200, review.data
    assert review.data["guardian"]["email"] == "micah.carter.parent@heritage.example.org"
    assert review.data["checklist"]["essay_received"] is True
    assert review.data["checklist"]["recommendations_received"] >= 2
    assert review.data["checklist"]["transcript_received"] is True
    assert Guardian.objects.filter(
        school=school,
        family__family_name="Carter Admissions Demo Family",
        email="micah.carter.parent@heritage.example.org",
    ).exists()
    assert AdmissionsAuditEvent.objects.filter(
        entity_type=AdmissionsAuditEvent.ENTITY_APPLICATION,
        entity_id=str(application_id),
        action="REVIEW_CHECKLIST_CONTACT_UPDATED",
    ).exists()

    before = client.get(f"/api/admissions/metrics/?school_id={school.id}&year_id={year_id}")
    assert before.status_code == 200, before.data
    accepted_before = before.data["metrics"]["accepted_count"]

    decided = client.post(
        "/api/admissions/decision/",
        {"application_id": application_id, "decision": "ACCEPTED"},
        format="json",
    )
    assert decided.status_code == 200, decided.data
    assert decided.data["status"] == AdmissionsApplication.STATUS_ACCEPTED
    assert AdmissionsDecision.objects.filter(
        application_id=application_id,
        decision_status=AdmissionsDecision.DECISION_ACCEPTED,
    ).exists()
    assert AdmissionsAuditEvent.objects.filter(
        entity_type=AdmissionsAuditEvent.ENTITY_DECISION,
        action="DECISION_MADE",
    ).exists()

    after_decision = client.get(f"/api/admissions/metrics/?school_id={school.id}&year_id={year_id}")
    assert after_decision.status_code == 200
    assert after_decision.data["metrics"]["accepted_count"] == accepted_before + 1

    application = AdmissionsApplication.objects.get(pk=application_id)
    assert application.status == AdmissionsApplication.STATUS_ACCEPTED


def test_admissions_mutations_require_edit_permission():
    school = ensure_demo_school(SANDBOX_SCHOOLS["heritage-core"])
    parent = ensure_persona_user(school, SANDBOX_PERSONAS["parent"])
    seeded = seed_heritage_admissions_scenario()
    client = APIClient()
    client.force_authenticate(parent)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))

    for path, body in [
        ("/api/admissions/review-update/", {"application_id": seeded["admissions_demo_application_id"]}),
        ("/api/admissions/decision/", {"application_id": seeded["admissions_demo_application_id"], "decision": "ACCEPTED"}),
        ("/api/admissions/enroll/", {"application_id": seeded["admissions_demo_application_id"]}),
    ]:
        response = client.post(path, body, format="json")
        assert response.status_code == 403, (path, response.data)
