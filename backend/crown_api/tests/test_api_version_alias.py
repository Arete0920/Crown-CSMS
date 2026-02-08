"""
Test that /api/v1 and /api paths return consistent responses.
Guards against routing drift.
"""
import importlib
import json
import sys
import types
import pytest
from django.test import Client, RequestFactory


@pytest.mark.django_db
class TestAPIVersionAlias:
    """Ensure /api/ and /api/v1/ are true aliases."""

    def test_households_endpoints_match(self):
        """Both /api/households/ and /api/v1/households/ return same status."""
        client = Client()
        
        r1 = client.get("/api/v1/households/")
        r2 = client.get("/api/households/")
        
        assert r1.status_code == r2.status_code, \
            f"/api/v1/households/ returned {r1.status_code}, /api/households/ returned {r2.status_code}"

    def test_auth_token_endpoints_match(self):
        """Both token endpoints exist and return same status for GET."""
        client = Client()
        
        # GET on token endpoint should return 405 (Method Not Allowed) for both
        r1 = client.get("/api/v1/auth/token/")
        r2 = client.get("/api/auth/token/")
        
        assert r1.status_code == r2.status_code, \
            f"/api/v1/auth/token/ returned {r1.status_code}, /api/auth/token/ returned {r2.status_code}"

    def test_health_endpoint_accessible(self):
        """Health endpoint works on both paths."""
        client = Client()
        
        r1 = client.get("/health/")
        r2 = client.get("/api/health/")
        
        assert r1.status_code == 200
        assert r2.status_code == 200

    def test_health_does_not_mask_build_sha_without_build_time(self, monkeypatch):
        """If BUILD_SHA exists but BUILD_TIME does not, /health should still return BUILD_SHA."""
        import crown_api.health_views as health_views

        # Monkeypatch BUILD_SHA environment variable
        monkeypatch.setenv("BUILD_SHA", "test-sha-1234567890")

        rf = RequestFactory()
        response = health_views.health(rf.get("/health/"))
        data = json.loads(response.content.decode("utf-8"))

        assert data["build_sha"] == "test-sha-1234567890"
