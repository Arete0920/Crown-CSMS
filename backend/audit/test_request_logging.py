"""Offline tests for request audit data minimization and failure handling."""
import logging
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from audit.request_logging import record_request_audit, request_audit_route


class RequestAuditPrivacyTests(unittest.TestCase):
    def request(self, *, route="accounts/reset/<uidb64>/<token>/", method="POST"):
        return SimpleNamespace(
            method=method,
            path="/accounts/reset/private-person/PRIVATE_RESET_TOKEN/",
            user=SimpleNamespace(id="actor-id"),
            resolver_match=SimpleNamespace(route=route),
            headers={"Authorization": "Bearer PRIVATE_HEADER"},
            body=b"PRIVATE_REQUEST_BODY",
        )

    def test_dynamic_segments_are_never_taken_from_the_raw_path(self):
        request = self.request()
        self.assertEqual(
            request_audit_route(request),
            "/accounts/reset/<uidb64>/<token>/",
        )
        self.assertNotIn("PRIVATE", request_audit_route(request))

    def test_static_routes_keep_the_existing_path_contract(self):
        request = self.request(route="api/v1/billing/installment-plans/")
        self.assertEqual(
            request_audit_route(request), "/api/v1/billing/installment-plans/"
        )

    def test_missing_or_invalid_resolver_uses_fixed_unresolved_marker(self):
        for match in (None, SimpleNamespace(), SimpleNamespace(route=None),
                      SimpleNamespace(route=7)):
            with self.subTest(match=match):
                request = self.request()
                request.resolver_match = match
                self.assertEqual(request_audit_route(request), "/<unresolved>")

    def test_registered_root_route_keeps_its_static_label(self):
        self.assertEqual(request_audit_route(self.request(route="")), "/")

    def test_route_length_is_bounded_by_the_audit_model(self):
        self.assertEqual(len(request_audit_route(self.request(route="a" * 300))), 255)

    def test_explicit_server_route_does_not_read_the_raw_path(self):
        request = self.request(route=None)
        self.assertEqual(
            request_audit_route(request, route_template="/api/director/actions/"),
            "/api/director/actions/",
        )

    def test_all_mutating_methods_capture_actor_route_and_response_only(self):
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            with self.subTest(method=method):
                create = Mock()
                response = SimpleNamespace(status_code=403, content=b"PRIVATE_RESPONSE")
                self.assertTrue(record_request_audit(
                    self.request(method=method), response, create=create,
                ))
                create.assert_called_once_with(
                    user_id="actor-id",
                    action=method,
                    model="/accounts/reset/<uidb64>/<token>/",
                    metadata={"status_code": 403},
                )
                self.assertNotIn("PRIVATE", repr(create.call_args))

    def test_read_only_methods_never_write_an_automatic_audit(self):
        for method in ("GET", "HEAD", "OPTIONS"):
            with self.subTest(method=method):
                create = Mock()
                self.assertFalse(record_request_audit(
                    self.request(method=method),
                    SimpleNamespace(status_code=200), create=create,
                ))
                create.assert_not_called()

    def test_anonymous_actor_stays_null(self):
        request = self.request()
        del request.user
        create = Mock()
        record_request_audit(request, SimpleNamespace(status_code=401), create=create)
        self.assertIsNone(create.call_args.kwargs["user_id"])

    def test_storage_error_emits_a_sanitized_error_without_raising(self):
        create = Mock(side_effect=RuntimeError("PRIVATE_ERROR_DETAIL"))
        with self.assertLogs("audit.request_logging", level=logging.ERROR) as captured:
            result = record_request_audit(
                self.request(), SimpleNamespace(status_code=200), create=create,
            )
        self.assertFalse(result)
        self.assertEqual(len(captured.records), 1)
        record = captured.records[0]
        self.assertEqual(record.audit_event, "request_audit_write_failed")
        self.assertEqual(record.audit_failure_type, "RuntimeError")
        self.assertIsNone(record.exc_info)
        self.assertNotIn("PRIVATE", repr(record.__dict__))


if __name__ == "__main__":
    unittest.main()
