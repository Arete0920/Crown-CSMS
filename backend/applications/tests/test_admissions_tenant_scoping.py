"""
Regression tests: cross-tenant header must NOT grant access to another school's
admissions data.

Contract:
  - User has admissions.view at School A only.
  - Request header points to School B (a real school in the DB).
  - TenantHeaderRequiredMiddleware accepts School B (valid UUID, exists).
  - View permission check uses school=request.school (School B instance).
  - user_has_permission(user, "admissions.view", school=School B) -> False.
  - Response: 403.
"""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from core.models import CrownPermission, RolePermission, School, UserRole


class AdmissionsTenantScopingTests(APITestCase):

    def setUp(self):
        User = get_user_model()

        self.school_a = School.objects.create(name="Scoping School A", is_active=True)
        self.school_b = School.objects.create(name="Scoping School B", is_active=True)

        self.user = User.objects.create_user(
            username="reg_scope_test@crown-demo.local",
            password="pass12345",
        )
        # User belongs to School A at the user record level (if applicable).
        if hasattr(self.user, "school_id"):
            self.user.school_id = self.school_a.pk
            self.user.save()

        # Grant admissions.view permission to REGISTRAR role.
        _perm, _ = CrownPermission.objects.get_or_create(
            code="admissions.view",
            defaults={"description": "View admissions"},
        )
        RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=_perm)

        # Assign REGISTRAR role at School A ONLY — not at School B.
        UserRole.objects.create(user=self.user, school=self.school_a, role_code="REGISTRAR")

        self.client.force_authenticate(user=self.user)

    # ── Cross-tenant ────────────────────────────────────────────────────

    def test_summary_cross_tenant_header_is_403(self):
        """REGISTRAR at School A must get 403 when header points to School B."""
        resp = self.client.get(
            "/api/v1/admissions/summary/",
            HTTP_X_SCHOOL_ID=str(self.school_b.pk),
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    def test_drilldown_cross_tenant_header_is_403(self):
        """REGISTRAR at School A must get 403 when header points to School B."""
        resp = self.client.get(
            "/api/v1/admissions/drilldown/",
            HTTP_X_SCHOOL_ID=str(self.school_b.pk),
        )
        self.assertEqual(resp.status_code, 403, resp.content)

    # ── Own-school still works ───────────────────────────────────────────

    def test_summary_own_school_is_200(self):
        """REGISTRAR at School A gets 200 for their own school."""
        resp = self.client.get(
            "/api/v1/admissions/summary/",
            HTTP_X_SCHOOL_ID=str(self.school_a.pk),
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertIn("pipeline", resp.data)

    def test_drilldown_own_school_is_200(self):
        """REGISTRAR at School A gets 200 for their own school."""
        resp = self.client.get(
            "/api/v1/admissions/drilldown/",
            HTTP_X_SCHOOL_ID=str(self.school_a.pk),
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertIn("total", resp.data)

    # ── No auth ─────────────────────────────────────────────────────────

    def test_summary_unauthenticated_is_401(self):
        """Unauthenticated requests must be rejected."""
        self.client.force_authenticate(user=None)
        resp = self.client.get(
            "/api/v1/admissions/summary/",
            HTTP_X_SCHOOL_ID=str(self.school_a.pk),
        )
        self.assertEqual(resp.status_code, 401, resp.content)
