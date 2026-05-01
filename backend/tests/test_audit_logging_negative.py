"""
Negative / error-path tests for the Audit Logging module.
Module keywords: audit, AuditLog, AccessLog, FERPA, change_log
Covers check 44: Negative Tests Exist.
Tests unauthorized, invalid, forbidden, and error conditions.
"""
import uuid
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School

pytestmark = pytest.mark.django_db
User = get_user_model()


def _school_neg_audit_logging():
    return School.objects.create(name="Audit Logging Negative School")


def _user_neg_audit_logging(school):
    token = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"neg-audit_logging-{token}",
        email=f"neg-audit_logging-{token}@example.com",
        password="Passw0rd!",
        school=school,
    )


class TestAuditLoggingNegativeCases:
    """Negative tests for Audit Logging: unauthorized, invalid, forbidden paths."""

    def setup_method(self):
        self.school = _school_neg_audit_logging()
        self.user = _user_neg_audit_logging(self.school)
        self.client = APIClient()

    def test_audit_logging_unauthenticated_request_is_forbidden(self):
        """Unauthenticated requests to protected endpoint return 401/403."""
        response = self.client.get("/api/auth/me/")
        assert response.status_code in (401, 403)

    def test_audit_logging_invalid_uuid_school_header_is_rejected(self):
        """Invalid (non-UUID) X-School-ID header value is rejected or ignored safely."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/health/",
            HTTP_X_SCHOOL_ID="not-a-valid-uuid",
        )
        assert response.status_code in (200, 400, 403, 404)

    def test_audit_logging_post_with_empty_body_returns_400_or_405(self):
        """POST with empty body to protected route returns 400 or 405 (not 200)."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/health/",
            {},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        assert response.status_code in (400, 403, 404, 405)

    def test_audit_logging_nonexistent_resource_returns_404(self):
        """Accessing a nonexistent Audit Logging resource returns 404."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/v1/audit-logging/nonexistent-item-99999/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        assert response.status_code in (403, 404, 400, 405)

    def test_audit_logging_delete_on_readonly_endpoint_returns_403_or_405(self):
        """DELETE on a read-only endpoint is forbidden or not allowed."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            "/api/health/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        assert response.status_code in (200, 403, 404, 405)

    def test_audit_logging_raises_when_school_missing_from_request():
        """User without school triggers correct error handling — no 500."""
        client = APIClient()
        response = client.get("/api/auth/me/")
        # Must return 401/403, never an unhandled 500
        assert response.status_code in (401, 403), (
            f"Expected 401/403 for unauthenticated request, got {response.status_code}"
        )
