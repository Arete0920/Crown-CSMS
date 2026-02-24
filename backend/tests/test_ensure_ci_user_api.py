"""Test ensure_ci_user endpoint creates school deterministically."""
import os
import pytest
from uuid import UUID
from unittest.mock import patch
from django.conf import settings
from django.test import override_settings
from rest_framework.test import APIClient
from core.models import School


@pytest.mark.django_db
def test_ensure_ci_user_creates_school_deterministically():
    """
    PROOF: ensure_ci_user endpoint creates school with deterministic defaults.
    
    This test prevents regression where API-level path diverges from
    the canonical seed_helpers pattern.
    
    Context: Azure DEV Smoke calls this endpoint before any bootstrap runs.
    It must create the school if missing, using deterministic defaults.
    """
    test_school_id = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')
    
    # Ensure school doesn't exist
    School.objects.filter(id=test_school_id).delete()
    
    client = APIClient()
    
    # Mock environment variables (os.getenv) and settings
    with override_settings(ENVIRONMENT='dev', DEV_OPS_SECRET='test-secret-123'):
        with patch.dict(os.environ, {
            'CI_SMOKE_USERNAME': 'ci@test.local',
            'CI_SMOKE_PASSWORD': 'TestPassword123!',
            'CI_SMOKE_SCHOOL_ID': str(test_school_id),
        }):
            response = client.post(
                '/api/v1/system/ensure-ci-user/',
                content_type='application/json',
                HTTP_X_ADMIN_OPS_SECRET='test-secret-123'
            )
    
    # Should succeed
    assert response.status_code == 200
    data = response.json()
    assert 'access' in data
    
    # School should now exist with canonical defaults
    school = School.objects.get(id=test_school_id)
    assert school.name == 'Crown Demo School'
    assert school.timezone == 'America/New_York'
    assert school.is_active is True


@pytest.mark.django_db
def test_ensure_ci_user_idempotent_with_existing_school():
    """
    PROOF: ensure_ci_user endpoint is idempotent when school exists.
    
    Second call should not crash or create duplicates.
    """
    test_school_id = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')
    
    # Pre-create school
    School.objects.filter(id=test_school_id).delete()
    School.objects.create(
        id=test_school_id,
        name='Crown Demo School',
        timezone='America/New_York',
        is_active=True
    )
    
    client = APIClient()
    
    with override_settings(ENVIRONMENT='dev', DEV_OPS_SECRET='test-secret-123'):
        with patch.dict(os.environ, {
            'CI_SMOKE_USERNAME': 'ci@test.local',
            'CI_SMOKE_PASSWORD': 'TestPassword123!',
            'CI_SMOKE_SCHOOL_ID': str(test_school_id),
        }):
            # First call
            response1 = client.post(
                '/api/v1/system/ensure-ci-user/',
                content_type='application/json',
                HTTP_X_ADMIN_OPS_SECRET='test-secret-123'
            )
            
            # Second call (idempotent)
            response2 = client.post(
                '/api/v1/system/ensure-ci-user/',
                content_type='application/json',
                HTTP_X_ADMIN_OPS_SECRET='test-secret-123'
            )
    
    # Both should succeed
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # No duplicates
    assert School.objects.filter(id=test_school_id).count() == 1


# ---------------------------------------------------------------------------
# Security invariants — these must never regress
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_ensure_ci_user_prod_always_404():
    """
    SECURITY INVARIANT: ensure_ci_user returns 404 in prod, unconditionally.
    Even with a valid DEV_OPS_SECRET and correct header, prod must be closed.
    """
    client = APIClient()
    with override_settings(ENVIRONMENT="prod", DEV_OPS_SECRET="test-secret-123"):
        with patch.dict(os.environ, {
            "CI_SMOKE_USERNAME": "ci@test.local",
            "CI_SMOKE_PASSWORD": "TestPassword123!",
            "CI_SMOKE_SCHOOL_ID": "a5351136-98fe-4d48-add0-fa8f62d9ceff",
        }):
            resp = client.post(
                "/api/v1/system/ensure-ci-user/",
                content_type="application/json",
                HTTP_X_ADMIN_OPS_SECRET="test-secret-123",
            )
    assert resp.status_code == 404, (
        f"SECURITY REGRESSION: ensure_ci_user returned {resp.status_code} in prod — must be 404"
    )


@pytest.mark.django_db
def test_ensure_ci_user_no_ops_secret_configured_returns_404():
    """
    SECURITY INVARIANT: ensure_ci_user returns 404 when DEV_OPS_SECRET is not
    configured on the server (even in dev). Prevents accidental open access.
    """
    client = APIClient()
    with override_settings(ENVIRONMENT="dev", DEV_OPS_SECRET=""):
        resp = client.post(
            "/api/v1/system/ensure-ci-user/",
            content_type="application/json",
            HTTP_X_ADMIN_OPS_SECRET="anything",
        )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_ensure_ci_user_wrong_secret_returns_403():
    """
    SECURITY INVARIANT: ensure_ci_user returns 403 when the secret header is
    wrong (dev env, secret configured, but caller provides wrong value).
    """
    client = APIClient()
    with override_settings(ENVIRONMENT="dev", DEV_OPS_SECRET="correct-secret"):
        with patch.dict(os.environ, {
            "CI_SMOKE_USERNAME": "ci@test.local",
            "CI_SMOKE_PASSWORD": "TestPassword123!",
            "CI_SMOKE_SCHOOL_ID": "a5351136-98fe-4d48-add0-fa8f62d9ceff",
        }):
            resp = client.post(
                "/api/v1/system/ensure-ci-user/",
                content_type="application/json",
                HTTP_X_ADMIN_OPS_SECRET="wrong-secret",
            )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_ensure_ci_user_no_header_returns_403():
    """
    SECURITY INVARIANT: ensure_ci_user returns 403 when no secret header is
    provided at all (dev env, secret configured).
    """
    client = APIClient()
    with override_settings(ENVIRONMENT="dev", DEV_OPS_SECRET="correct-secret"):
        with patch.dict(os.environ, {
            "CI_SMOKE_USERNAME": "ci@test.local",
            "CI_SMOKE_PASSWORD": "TestPassword123!",
            "CI_SMOKE_SCHOOL_ID": "a5351136-98fe-4d48-add0-fa8f62d9ceff",
        }):
            resp = client.post(
                "/api/v1/system/ensure-ci-user/",
                content_type="application/json",
            )
    assert resp.status_code == 403
