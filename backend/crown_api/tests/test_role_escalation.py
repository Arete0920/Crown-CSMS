"""
Security tests: Role escalation prevention.

Verifies that a normal user cannot elevate their own role or another user's
role through the API. These tests exercise permission-layer hardening
(Stage 1 Security Hardening — OWASP A01:2021 Broken Access Control).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from core.models import School

User = get_user_model()


class RoleEscalationTests(TestCase):
    """Ensure regular users cannot elevate privileges through API endpoints."""

    def setUp(self):
        self.normal_user = User.objects.create_user(
            username="normal@test.com",
            email="normal@test.com",
            password="testpass123!",
        )
        self.school = School.objects.create(name="Role Escalation Test School")
        self.client = Client()
        self.client.force_login(self.normal_user)

    # ------------------------------------------------------------------
    # /api/v1/users/me/ — self-escalation via PATCH
    # ------------------------------------------------------------------

    def test_user_cannot_self_escalate_role_via_patch(self):
        """PATCH /api/v1/users/me/ with role=admin must return 400 or 403."""
        response = self.client.patch(
            "/api/v1/users/me/",
            data='{"role": "admin"}',
            content_type="application/json",
        )
        self.assertIn(
            response.status_code,
            (400, 403, 404, 405),
            msg=f"Expected 400/403/404/405, got {response.status_code}. "
                "Endpoint must reject role escalation attempts.",
        )

    def test_user_cannot_self_escalate_role_via_put(self):
        """PUT /api/v1/users/me/ with role=director must return 400 or 403."""
        response = self.client.put(
            "/api/v1/users/me/",
            data='{"role": "director"}',
            content_type="application/json",
        )
        self.assertIn(
            response.status_code,
            (400, 403, 404, 405),
            msg=f"Expected 400/403/404/405, got {response.status_code}.",
        )

    # ------------------------------------------------------------------
    # Unauthenticated escalation attempt
    # ------------------------------------------------------------------

    def test_unauthenticated_request_cannot_escalate(self):
        """Anonymous PATCH to a user endpoint must not return 2xx (privilege granted)."""
        anon_client = Client()
        response = anon_client.patch(
            "/api/v1/users/me/",
            data='{"role": "admin"}',
            content_type="application/json",
        )
        self.assertNotIn(
            response.status_code,
            range(200, 300),
            msg=f"Anonymous user role escalation unexpectedly succeeded "
                f"with HTTP {response.status_code}.",
        )

    # ------------------------------------------------------------------
    # Cross-user escalation attempt via director actions
    # ------------------------------------------------------------------

    def test_normal_user_cannot_call_director_actions(self):
        """A valid school-scoped POST by a non-director must be permission denied."""
        school_id = str(self.school.id)
        response = self.client.post(
            "/api/director/actions/",
            data={
                "action": "POST_ACCEPTED_AWARDS",
                "school_id": school_id,
                "ids": ["00000000-0000-0000-0000-000000000001"],
            },
            content_type="application/json",
            HTTP_X_SCHOOL_ID=school_id,
        )
        self.assertIn(
            response.status_code,
            (401, 403),
            msg=f"Expected 401/403 permission denial for director actions, "
                f"got {response.status_code}.",
        )

    # ------------------------------------------------------------------
    # ALLOW_DEMO_ROLE_HEADER must be disabled in production
    # ------------------------------------------------------------------

    def test_demo_role_header_flag_is_disabled(self):
        """ALLOW_DEMO_ROLE_HEADER must be False unconditionally."""
        from django.conf import settings
        self.assertFalse(
            getattr(settings, "ALLOW_DEMO_ROLE_HEADER", False),
            "ALLOW_DEMO_ROLE_HEADER must be False in all environments — "
            "it bypasses role enforcement.",
        )
