"""Application-owned request logs must not retain caller-controlled URL values."""
import json
from types import SimpleNamespace
from unittest.mock import patch

from django.http import HttpResponse
from django.test import Client, RequestFactory, SimpleTestCase, override_settings
from django.urls import path

from core.observability.middleware import RequestCorrelationMiddleware
from crown_api.middleware.performance import PerformanceMiddleware


def _ok(request, family_ref):
    return HttpResponse(status=204)


urlpatterns = [path("observability/family/<str:family_ref>/", _ok)]


class RequestObservabilityPrivacyTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.private_value = "synthetic-parent@example.invalid"

    def test_request_log_uses_resolved_template_and_preserves_response(self):
        request = self.factory.get(f"/family/{self.private_value}/?token=synthetic-token")
        response = HttpResponse("unchanged", status=202)

        def respond(incoming):
            incoming.resolver_match = SimpleNamespace(route="family/<str:family_ref>/")
            return response

        with self.assertLogs("crown.request", level="INFO") as captured:
            actual = RequestCorrelationMiddleware(respond)(request)

        payload = json.loads(captured.records[0].getMessage())
        self.assertEqual(payload["path"], "/family/<str:family_ref>/")
        self.assertEqual(payload["status_code"], 202)
        self.assertNotIn(self.private_value, captured.output[0])
        self.assertNotIn("synthetic-token", captured.output[0])
        self.assertIs(actual, response)
        self.assertEqual(actual.content, b"unchanged")
        self.assertEqual(actual["X-Correlation-ID"], request.correlation_id)

    def test_unresolved_request_log_uses_fixed_marker(self):
        request = self.factory.get(f"/missing/{self.private_value}/")
        with self.assertLogs("crown.request", level="INFO") as captured:
            RequestCorrelationMiddleware(lambda request: HttpResponse(status=404))(request)
        payload = json.loads(captured.records[0].getMessage())
        self.assertEqual(payload["path"], "/<unresolved>")
        self.assertNotIn(self.private_value, captured.output[0])

    def test_slow_request_log_uses_route_template(self):
        request = self.factory.patch(f"/family/{self.private_value}/")
        request.resolver_match = SimpleNamespace(route="family/<str:family_ref>/")
        response = HttpResponse(status=403)
        with patch("crown_api.middleware.performance.time.perf_counter", side_effect=[0, 2]):
            with self.assertLogs("crown.performance", level="WARNING") as captured:
                actual = PerformanceMiddleware(lambda request: response)(request)
        self.assertIn("path=/family/<str:family_ref>/", captured.output[0])
        self.assertIn("method=PATCH status=403", captured.output[0])
        self.assertNotIn(self.private_value, captured.output[0])
        self.assertIs(actual, response)
        self.assertEqual(actual["X-Response-Time-ms"], "2000.00")

    def test_unresolved_slow_request_log_uses_fixed_marker(self):
        request = self.factory.get(f"/missing/{self.private_value}/")
        with patch("crown_api.middleware.performance.time.perf_counter", side_effect=[0, 2]):
            with self.assertLogs("crown.performance", level="WARNING") as captured:
                PerformanceMiddleware(lambda request: HttpResponse(status=404))(request)
        self.assertIn("path=/<unresolved>", captured.output[0])
        self.assertNotIn(self.private_value, captured.output[0])

    @override_settings(
        ROOT_URLCONF=__name__,
        MIDDLEWARE=["core.observability.middleware.RequestCorrelationMiddleware"],
    )
    def test_django_client_resolves_template_before_request_is_logged(self):
        with self.assertLogs("crown.request", level="INFO") as captured:
            response = Client().get(f"/observability/family/{self.private_value}/")
        self.assertEqual(response.status_code, 204)
        payload = json.loads(captured.records[0].getMessage())
        self.assertEqual(payload["path"], "/observability/family/<str:family_ref>/")
        self.assertNotIn(self.private_value, captured.output[0])
