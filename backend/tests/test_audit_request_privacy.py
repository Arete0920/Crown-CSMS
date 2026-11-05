"""Exercise automatic audit privacy through real Django URL resolution."""
import json
from types import SimpleNamespace
from unittest.mock import patch

from django.db import DatabaseError
from django.http import JsonResponse
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import path

from audit.middleware import AuditMiddleware
from audit.models import AuditLog
from crown_api.auth_middleware import _audit_early_director_response


def synthetic_response(request, **kwargs):
    return JsonResponse({"ok": True, "value": "PRIVATE_RESPONSE"})


def denied_response(request):
    return JsonResponse({"detail": "Denied"}, status=403)


urlpatterns = [
    path("accounts/reset/<str:uidb64>/<str:token>/", synthetic_response),
    path("static-audit/", synthetic_response),
    path("denied-audit/", denied_response),
]


@override_settings(
    ROOT_URLCONF=__name__,
    MIDDLEWARE=["audit.middleware.AuditMiddleware"],
    ALLOWED_HOSTS=["testserver"],
)
class AutomaticAuditPrivacyTests(TestCase):
    def test_resolved_route_withholds_dynamic_values_query_headers_and_bodies(self):
        response = Client().post(
            "/accounts/reset/PRIVATE_PERSON/PRIVATE_TOKEN/?token=PRIVATE_QUERY",
            data=json.dumps({"password": "PRIVATE_BODY"}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer PRIVATE_HEADER",
        )
        self.assertEqual(response.status_code, 200)
        receipt = AuditLog.objects.get()
        self.assertEqual(receipt.model, "/accounts/reset/<str:uidb64>/<str:token>/")
        self.assertEqual(receipt.metadata, {"status_code": 200})
        self.assertIsNone(receipt.user_id)
        self.assertNotIn("PRIVATE", receipt.model + json.dumps(receipt.metadata))

    def test_unmatched_sensitive_path_is_not_persisted(self):
        response = Client().post("/PRIVATE_UNKNOWN_PATH/")
        self.assertEqual(response.status_code, 404)
        receipt = AuditLog.objects.get()
        self.assertEqual(receipt.model, "/<unresolved>")
        self.assertEqual(receipt.metadata["status_code"], 404)

    def test_static_route_and_failed_write_evidence_remain_compatible(self):
        client = Client()
        client.post("/static-audit/")
        client.post("/denied-audit/")
        self.assertTrue(AuditLog.objects.filter(
            model="/static-audit/", action="POST",
            metadata__status_code=200,
        ).exists())
        self.assertTrue(AuditLog.objects.filter(
            model="/denied-audit/", action="POST",
            metadata__status_code=403,
        ).exists())

    def test_get_does_not_create_an_automatic_audit(self):
        self.assertEqual(Client().get("/static-audit/").status_code, 200)
        self.assertFalse(AuditLog.objects.exists())

    def test_storage_failure_preserves_response_and_emits_sanitized_signal(self):
        request = RequestFactory().post("/PRIVATE_PATH/", {"password": "PRIVATE_BODY"})
        request.user = SimpleNamespace(id=None)
        expected = JsonResponse({"private": "PRIVATE_RESPONSE"})
        with patch(
            "audit.middleware.AuditLog.objects.create",
            side_effect=DatabaseError("PRIVATE_DATABASE_DETAIL"),
        ), self.assertLogs("audit.request_logging", level="ERROR") as captured:
            actual = AuditMiddleware(lambda request: expected)(request)
        self.assertIs(actual, expected)
        self.assertEqual(len(captured.records), 1)
        record = captured.records[0]
        self.assertEqual(record.audit_event, "request_audit_write_failed")
        self.assertEqual(record.audit_failure_type, "DatabaseError")
        self.assertIsNone(record.exc_info)
        self.assertNotIn("PRIVATE", repr(record.__dict__))
        self.assertFalse(AuditLog.objects.exists())

    def test_early_director_denials_keep_only_fixed_registered_aliases(self):
        for path_value in ("/api/director/actions/", "/api/v1/director/actions/"):
            with self.subTest(path=path_value):
                request = RequestFactory().post(path_value)
                response = JsonResponse({"detail": "Unauthorized"}, status=401)
                self.assertIs(_audit_early_director_response(request, response), response)
                self.assertTrue(AuditLog.objects.filter(
                    model=path_value, action="POST", metadata__status_code=401,
                ).exists())

    def test_early_director_suffix_cannot_copy_private_prefix_into_audit(self):
        request = RequestFactory().post("/PRIVATE_PREFIX/director/actions/")
        response = JsonResponse({"detail": "Unauthorized"}, status=401)
        _audit_early_director_response(request, response)
        receipt = AuditLog.objects.get()
        self.assertEqual(receipt.model, "/<unresolved>")
        self.assertNotIn("PRIVATE", json.dumps(receipt.metadata) + receipt.model)

    def test_early_director_storage_failure_is_observable_without_private_detail(self):
        request = RequestFactory().post("/PRIVATE_PREFIX/director/actions/")
        response = JsonResponse({"detail": "Unauthorized"}, status=401)
        with patch(
            "crown_api.auth_middleware.AuditLog.objects.create",
            side_effect=DatabaseError("PRIVATE_DATABASE_DETAIL"),
        ), self.assertLogs("audit.request_logging", level="ERROR") as captured:
            actual = _audit_early_director_response(request, response)
        self.assertIs(actual, response)
        self.assertNotIn("PRIVATE", repr(captured.records[0].__dict__))
