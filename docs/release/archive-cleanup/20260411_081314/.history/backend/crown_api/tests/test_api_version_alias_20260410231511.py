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

    def test_support_routes_do_not_expose_double_v1_prefix(self):
        """Support endpoints should exist on /api/ and /api/v1/, but not /api/v1/v1/."""
        client = Client()

        versioned = client.get("/api/v1/support/tickets/")
        alias = client.get("/api/support/tickets/")
        doubled = client.get("/api/v1/v1/support/tickets/")

        assert versioned.status_code == alias.status_code
        assert doubled.status_code == 404

    def test_integrity_reports_current_required_checks(self):
        """Integrity endpoint should reflect the live required branch-protection check set."""
        from crown_api.views_integrity import integrity

        rf = RequestFactory()
        response = integrity(rf.get("/api/integrity/"))
        data = json.loads(response.content.decode("utf-8"))

        assert data["required_checks"] == [
            "changes",
            "demo-proof-static",
            "lockdown-gate",
            "meta-check-job-if",
            "phase1-contract",
            "phase3-runtime-proof",
            "proof-ceremony",
            "rc-promotion-gate",
            "spine-audit",
            "test",
            "verify-immutable-tags",
            "CodeQL",
            "contract-gate",
            "pytest-gate",
            "secret-scan",
            "dependency-review",
            "Backend Python Dependency Audit",
            "Frontend Node Dependency Audit",
        ]

    def test_student360_uses_spectacular_auto_schema(self):
        """APIView-based endpoints should expose drf-spectacular AutoSchema for schema export."""
        from drf_spectacular.openapi import AutoSchema as SpectacularAutoSchema
        from student360.api.views import StudentSelfOverview

        assert isinstance(StudentSelfOverview.schema, SpectacularAutoSchema)
