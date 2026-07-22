import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.test import RequestFactory, TestCase, override_settings
from rest_framework.exceptions import NotFound, ValidationError

from core.models import School, UserRole
from core.tenant_header_middleware import TenantHeaderRequiredMiddleware
from crown_api.audit_models import AuditEvent
from crown_api.dashboards.tenant import get_dashboard_school_id

User = get_user_model()


class TenantDecisionAuditTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.school_a = School.objects.create(name="Audit School A")
        self.school_b = School.objects.create(name="Audit School B")
        self.user = User.objects.create_user(
            username="tenant-audit-user",
            email="tenant-audit-user@example.com",
            password="test-password",
            school=self.school_a,
        )

    @staticmethod
    def _ok(_request):
        return JsonResponse({"ok": True})

    def _request(self, school_id):
        request = self.factory.get(
            "/api/v1/academics/courses/",
            HTTP_X_SCHOOL_ID=str(school_id),
            HTTP_X_REQUEST_ID="tenant-decision-test",
        )
        request.user = self.user
        return request

    @staticmethod
    def _response_payload(response):
        return json.loads(response.content.decode("utf-8"))

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_denied_override_persists_structured_decision_evidence(self):
        response = TenantHeaderRequiredMiddleware(self._ok)(self._request(self.school_b.id))

        self.assertEqual(response.status_code, 404)
        event = AuditEvent.objects.get(action="tenant.context.decision")
        self.assertEqual(event.school_id, self.school_b.id)
        self.assertEqual(event.meta["principal_school_id"], str(self.school_a.id))
        self.assertEqual(event.meta["selected_school_id"], str(self.school_b.id))
        self.assertEqual(event.meta["source"], "header")
        self.assertTrue(event.meta["override_requested"])
        self.assertFalse(event.meta["override_authorized"])
        self.assertEqual(event.meta["outcome"], "denied")
        self.assertEqual(event.meta["reason"], "override_not_authorized")
        self.assertEqual(event.meta["route"], "/api/v1/academics/courses/")
        self.assertEqual(event.meta["method"], "GET")
        self.assertEqual(event.meta["correlation_id"], "tenant-decision-test")

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_denied_override_remains_denied_when_audit_cannot_persist(self):
        with patch(
            "core.tenant_header_middleware.audit_tenant_decision",
            side_effect=RuntimeError("audit unavailable"),
        ):
            response = TenantHeaderRequiredMiddleware(self._ok)(self._request(self.school_b.id))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self._response_payload(response)["code"], "tenant_access_denied")

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_authorized_support_override_persists_decision_before_business_logic(self):
        UserRole.objects.create(school=self.school_a, user=self.user, role_code="SUPPORT")

        response = TenantHeaderRequiredMiddleware(self._ok)(self._request(self.school_b.id))

        self.assertEqual(response.status_code, 200)
        event = AuditEvent.objects.get(action="tenant.context.decision")
        self.assertEqual(event.school_id, self.school_b.id)
        self.assertEqual(event.meta["outcome"], "authorized")
        self.assertEqual(event.meta["reason"], "explicit_cross_school_override")
        self.assertTrue(event.meta["override_requested"])
        self.assertTrue(event.meta["override_authorized"])

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_authorized_override_fails_closed_when_audit_cannot_persist(self):
        UserRole.objects.create(school=self.school_a, user=self.user, role_code="SUPPORT")

        with patch(
            "core.tenant_header_middleware.audit_tenant_decision",
            side_effect=RuntimeError("audit unavailable"),
        ):
            response = TenantHeaderRequiredMiddleware(self._ok)(self._request(self.school_b.id))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(self._response_payload(response)["code"], "tenant_audit_unavailable")


class DashboardCanonicalTenantTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.school_a = School.objects.create(name="Dashboard School A")
        self.school_b = School.objects.create(name="Dashboard School B")
        self.user = User.objects.create_user(
            username="dashboard-context-user",
            email="dashboard-context-user@example.com",
            password="test-password",
            school=self.school_a,
            is_staff=True,
        )

    def _request(self, school_id=None):
        headers = {}
        if school_id is not None:
            headers["HTTP_X_SCHOOL_ID"] = str(school_id)
        request = self.factory.get("/api/v1/dashboards/summary/", **headers)
        request.user = self.user
        return request

    def test_dashboard_still_requires_explicit_header_with_principal_fallback(self):
        with self.assertRaises(ValidationError):
            get_dashboard_school_id(self._request())

    def test_ordinary_staff_status_does_not_authorize_cross_school_dashboard(self):
        request = self._request(self.school_b.id)
        with self.assertRaises(NotFound):
            get_dashboard_school_id(request)
        self.assertTrue(request.crown_tenant.override_requested)
        self.assertFalse(request.crown_tenant.override_authorized)

    def test_support_role_authorizes_cross_school_dashboard_through_canonical_context(self):
        UserRole.objects.create(school=self.school_a, user=self.user, role_code="SUPPORT")
        request = self._request(self.school_b.id)

        school_id = get_dashboard_school_id(request)

        self.assertEqual(school_id, self.school_b.id)
        self.assertTrue(request.crown_tenant.override_requested)
        self.assertTrue(request.crown_tenant.override_authorized)
