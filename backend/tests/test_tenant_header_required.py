import json
from dataclasses import FrozenInstanceError

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import APIClient

from core.models import School
from core.tenant_header_middleware import TenantHeaderRequiredMiddleware
from core.tenant_models import get_current_school

User = get_user_model()


class TenantHeaderRequiredTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.school = School.objects.create(name="Primary School")
        self.other_school = School.objects.create(name="Other School")
        self.user = User.objects.create_user(
            username="tenant-user",
            email="tenant-user@example.com",
            password="test-password",
            school=self.school,
        )

    @staticmethod
    def _json(response):
        return json.loads(response.content)

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_health_exempt_no_header(self):
        c = APIClient()
        r = c.get("/api/v1/health/")
        self.assertNotEqual(r.status_code, 400)

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_auth_exempt_no_header(self):
        c = APIClient()
        r = c.post("/api/v1/auth/token/", {})
        self.assertNotIn(b"X-School-Id", r.content)

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_other_api_requires_header(self):
        c = APIClient()
        r = c.get("/api/v1/academics/courses/")
        self.assertEqual(r.status_code, 400)
        self.assertIn("X-School-Id", str(r.content))

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_options_request_no_header_allowed(self):
        c = APIClient()
        r = c.options("/api/v1/academics/courses/")
        self.assertNotEqual(r.status_code, 400, "OPTIONS request blocked by middleware")

    def _capture_response(self, request):
        context = request.crown_tenant
        return JsonResponse(
            {
                "school_id": request.school_id,
                "tenant_school_id": str(request.tenant_school_id),
                "school_name": request.school.name,
                "tenant_school_name": request.tenant_school.name,
                "source": context.source,
                "principal_school_id": str(context.principal_school_id),
                "override_requested": context.override_requested,
                "override_authorized": context.override_authorized,
                "override_id": str(getattr(request, "_crown_school_override_id", "")),
            }
        )

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_matching_header_binds_canonical_and_compatibility_attributes(self):
        request = self.factory.get(
            "/api/v1/test/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        request.user = self.user

        response = TenantHeaderRequiredMiddleware(self._capture_response)(request)

        self.assertEqual(response.status_code, 200)
        data = self._json(response)
        self.assertEqual(data["school_id"], str(self.school.id))
        self.assertEqual(data["tenant_school_id"], str(self.school.id))
        self.assertEqual(data["school_name"], self.school.name)
        self.assertEqual(data["tenant_school_name"], self.school.name)
        self.assertEqual(data["source"], "header")
        self.assertFalse(data["override_requested"])
        self.assertFalse(data["override_authorized"])
        self.assertIsNone(get_current_school())

        with self.assertRaises(FrozenInstanceError):
            request.crown_tenant.school_id = self.other_school.id

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_authenticated_user_school_is_fallback_when_header_absent(self):
        request = self.factory.get("/api/v1/test/")
        request.user = self.user

        response = TenantHeaderRequiredMiddleware(self._capture_response)(request)

        self.assertEqual(response.status_code, 200)
        data = self._json(response)
        self.assertEqual(data["school_id"], str(self.school.id))
        self.assertEqual(data["source"], "user")
        self.assertEqual(data["principal_school_id"], str(self.school.id))
        self.assertIsNone(get_current_school())

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_ordinary_user_conflicting_header_is_denied(self):
        request = self.factory.get(
            "/api/v1/test/",
            HTTP_X_SCHOOL_ID=str(self.other_school.id),
        )
        request.user = self.user

        response = TenantHeaderRequiredMiddleware(self._capture_response)(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self._json(response)["code"], "tenant_access_denied")
        self.assertIsNone(get_current_school())

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_unassigned_non_staff_principal_cannot_select_tenant(self):
        unassigned = User.objects.create_user(
            username="unassigned-user",
            email="unassigned@example.com",
            password="test-password",
            school=None,
        )
        request = self.factory.get(
            "/api/v1/test/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        request.user = unassigned

        response = TenantHeaderRequiredMiddleware(self._capture_response)(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self._json(response)["code"], "tenant_access_denied")
        self.assertIsNone(get_current_school())

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_staff_cross_school_override_is_bound_for_audit(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        request = self.factory.get(
            "/api/v1/test/",
            HTTP_X_SCHOOL_ID=str(self.other_school.id),
        )
        request.user = self.user

        response = TenantHeaderRequiredMiddleware(self._capture_response)(request)

        self.assertEqual(response.status_code, 200)
        data = self._json(response)
        self.assertEqual(data["school_id"], str(self.other_school.id))
        self.assertTrue(data["override_requested"])
        self.assertTrue(data["override_authorized"])
        self.assertEqual(data["override_id"], str(self.other_school.id))
        self.assertIsNone(get_current_school())

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_inactive_school_fails_closed_for_authorized_override(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        self.other_school.is_active = False
        self.other_school.save(update_fields=["is_active"])
        request = self.factory.get(
            "/api/v1/test/",
            HTTP_X_SCHOOL_ID=str(self.other_school.id),
        )
        request.user = self.user

        response = TenantHeaderRequiredMiddleware(self._capture_response)(request)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self._json(response)["code"], "invalid_tenant")
        self.assertIsNone(get_current_school())

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_context_is_cleared_when_downstream_raises(self):
        request = self.factory.get(
            "/api/v1/test/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        request.user = self.user

        def raise_error(_request):
            self.assertEqual(get_current_school().id, self.school.id)
            raise RuntimeError("downstream failure")

        middleware = TenantHeaderRequiredMiddleware(raise_error)
        with self.assertRaisesRegex(RuntimeError, "downstream failure"):
            middleware(request)

        self.assertIsNone(get_current_school())
