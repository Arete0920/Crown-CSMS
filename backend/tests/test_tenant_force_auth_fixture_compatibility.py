"""Prove test-fixture compatibility without broadening runtime tenant authority."""

import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.test import RequestFactory, TestCase, override_settings

from core.models import School, UserRole
from core.tenant_header_middleware import TenantHeaderRequiredMiddleware


User = get_user_model()


class TenantForceAuthFixtureCompatibilityTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.school = School.objects.create(name="Forced Fixture School")
        self.other_school = School.objects.create(name="Forced Fixture Other School")

    @staticmethod
    def _json(response):
        return json.loads(response.content)

    @staticmethod
    def _capture_context(request):
        context = request.crown_tenant
        return JsonResponse(
            {
                "school_id": str(context.school_id),
                "principal_school_id": (
                    str(context.principal_school_id)
                    if context.principal_school_id
                    else None
                ),
                "actor_type": context.actor_type,
                "source": context.source,
                "override_requested": context.override_requested,
                "override_authorized": context.override_authorized,
            }
        )

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_unassigned_drf_force_fixture_may_select_header_tenant(self):
        forced_user = User.objects.create_user(
            username="forced-unassigned",
            email="forced-unassigned@example.com",
            password="test-password",
            school=None,
        )
        request = self.factory.get(
            "/api/v1/test/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        request.user = AnonymousUser()
        request._force_auth_user = forced_user

        response = TenantHeaderRequiredMiddleware(self._capture_context)(request)

        self.assertEqual(response.status_code, 200)
        data = self._json(response)
        self.assertEqual(data["school_id"], str(self.school.id))
        self.assertIsNone(data["principal_school_id"])
        self.assertEqual(data["actor_type"], "drf_force")
        self.assertFalse(data["override_requested"])
        self.assertFalse(data["override_authorized"])

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_assigned_drf_force_fixture_still_cannot_cross_tenants(self):
        forced_user = User.objects.create_user(
            username="forced-assigned",
            email="forced-assigned@example.com",
            password="test-password",
            school=self.school,
        )
        request = self.factory.get(
            "/api/v1/test/",
            HTTP_X_SCHOOL_ID=str(self.other_school.id),
        )
        request.user = AnonymousUser()
        request._force_auth_user = forced_user

        response = TenantHeaderRequiredMiddleware(self._capture_context)(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self._json(response)["code"], "tenant_access_denied")

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_single_role_school_is_valid_principal_fallback(self):
        user = User.objects.create_user(
            username="role-school-user",
            email="role-school-user@example.com",
            password="test-password",
            school=None,
        )
        UserRole.objects.create(user=user, school=self.school, role_code="TEACHER")
        request = self.factory.get("/api/v1/test/")
        request.user = user

        response = TenantHeaderRequiredMiddleware(self._capture_context)(request)

        self.assertEqual(response.status_code, 200)
        data = self._json(response)
        self.assertEqual(data["school_id"], str(self.school.id))
        self.assertEqual(data["principal_school_id"], str(self.school.id))
        self.assertEqual(data["source"], "user_role")
        self.assertFalse(data["override_requested"])

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_multiple_role_schools_remain_ambiguous_without_explicit_context(self):
        user = User.objects.create_user(
            username="multi-role-user",
            email="multi-role-user@example.com",
            password="test-password",
            school=None,
        )
        UserRole.objects.create(user=user, school=self.school, role_code="TEACHER")
        UserRole.objects.create(user=user, school=self.other_school, role_code="DIRECTOR")
        request = self.factory.get("/api/v1/test/")
        request.user = user

        response = TenantHeaderRequiredMiddleware(self._capture_context)(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._json(response)["code"], "missing_tenant")
