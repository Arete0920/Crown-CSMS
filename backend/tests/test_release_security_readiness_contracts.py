"""
Release security/readiness contracts for priorities 041-045.
"""

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import override_settings
from rest_framework.test import APIClient

from core.models import School

pytestmark = pytest.mark.django_db
User = get_user_model()


def _user_for_school(school, *, prefix="release-readiness"):
    token = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"{prefix}-{token}",
        email=f"{prefix}-{token}@example.com",
        password="Passw0rd!",
        school=school,
    )


def _admissions_submit_payload(campus_name):
    return {
        "inquiry": {
            "campus": campus_name,
            "startTerm": "Fall 2026",
            "heardAbout": "website",
        },
        "family": {
            "guardians": [
                {
                    "relationship": "Mother",
                    "relationshipOther": "",
                    "guardianName": "Jane Example",
                    "email": "jane.guardian@example.com",
                    "phone": "555-010-1212",
                    "isPrimary": True,
                }
            ]
        },
        "students": [
            {
                "firstName": "Ava",
                "lastName": "Example",
                "gradeApplyingFor": "5",
                "currentSchool": "Homeschool",
            }
        ],
        "applicationFee": {
            "policyAccepted": True,
            "waiverRequested": False,
        },
    }


@override_settings(CROWN_DEMO_MODE=True)
def test_041_dangerous_toggle_demo_mode_blocks_writes():
    client = APIClient()
    response = client.post("/api/v1/academics/courses/", {}, format="json")
    assert response.status_code == 403


@override_settings(TENANT_HEADER_REQUIRED=True)
def test_041_dangerous_toggle_tenant_header_enforced_on_scoped_read():
    school = School.objects.create(name="Release Readiness School")
    user = _user_for_school(school)
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get("/api/v1/gradebook/sections/")
    assert response.status_code in (400, 403)


def test_042_csrf_public_surface_policy_contracts_hold():
    assert isinstance(settings.CSRF_TRUSTED_ORIGINS, list)
    for origin in settings.CSRF_TRUSTED_ORIGINS:
        assert origin.startswith("http")

    client = APIClient()
    health = client.get("/health/")
    assert health.status_code == 200

    health_post = client.post("/health/", {}, format="json")
    assert health_post.status_code in (200, 403, 404, 405)
    assert health_post.status_code != 500


def test_043_jwt_session_aad_contracts_fail_closed_for_bad_auth():
    client = APIClient()

    unauth = client.get("/api/auth/me/")
    assert unauth.status_code in (401, 403)

    malformed_bearer = client.get(
        "/api/auth/me/",
        HTTP_AUTHORIZATION="Bearer definitely-not-a-valid-token",
    )
    assert malformed_bearer.status_code in (401, 403)

    token_resp = client.post("/api/v1/auth/token/", {}, format="json")
    assert token_resp.status_code in (400, 401)


def test_044_security_log_presence_on_protected_failure_configuration():
    client = APIClient()
    response = client.get("/api/v1/reports/export/")

    assert response.status_code in (401, 403)
    logger_cfg = (settings.LOGGING or {}).get("loggers", {}).get("django.request", {})
    assert isinstance(logger_cfg, dict)
    assert logger_cfg.get("level") in ("WARNING", "INFO", "DEBUG", "NOTSET", None)
    handlers = logger_cfg.get("handlers", [])
    assert isinstance(handlers, list)


def test_045_admissions_submit_idempotency_replay_contract():
    school = School.objects.create(name="Release Readiness Replay School")
    client = APIClient()
    payload = _admissions_submit_payload(campus_name=school.name)
    idem = f"release-replay-{uuid.uuid4().hex}"

    first = client.post(
        "/api/v1/admissions/submit/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=idem,
    )
    assert first.status_code == 201
    first_application_id = first.data.get("application_id")
    assert first_application_id

    second = client.post(
        "/api/v1/admissions/submit/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=idem,
    )
    assert second.status_code == 200
    assert second.headers.get("X-Idempotent-Replay") == "true"
    assert second.data.get("application_id") == first_application_id


def test_045_admissions_event_replay_requires_authentication():
    client = APIClient()
    random_app = uuid.uuid4()
    response = client.get(f"/api/v1/admissions/applications/{random_app}/event-replay/")
    assert response.status_code in (401, 403)
