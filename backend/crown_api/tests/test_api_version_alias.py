"""
Test that /api/v1 and /api paths return consistent responses.
Guards against routing drift.
"""
import pytest
from django.test import Client


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
