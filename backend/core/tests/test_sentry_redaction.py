import ast
import json
import unittest
from pathlib import Path

from core.observability.sentry import before_send


def test_before_send_removes_request_payload_and_sensitive_headers():
    event = {
        "request": {
            "data": {"password": "secret", "student_name": "Example Student"},
            "cookies": {"sessionid": "secret"},
            "query_string": "token=secret",
            "headers": {
                "Authorization": "Bearer secret",
                "Cookie": "sessionid=secret",
                "X-Api-Key": "secret",
                "User-Agent": "pytest",
            },
        },
        "user": {
            "id": "internal-user-id",
            "email": "person@example.test",
            "username": "person",
        },
    }

    sanitized = before_send(event, {})

    assert "data" not in sanitized["request"]
    assert "cookies" not in sanitized["request"]
    assert "query_string" not in sanitized["request"]
    assert sanitized["request"]["headers"]["Authorization"] == "[Filtered]"
    assert sanitized["request"]["headers"]["Cookie"] == "[Filtered]"
    assert sanitized["request"]["headers"]["X-Api-Key"] == "[Filtered]"
    assert sanitized["request"]["headers"]["User-Agent"] == "pytest"
    assert sanitized["user"] == {"id": "internal-user-id"}


class SentryOperationsHeaderRedactionTests(unittest.TestCase):
    operations_headers = (
        "X-Admin-Ops-Secret",
        "X-Ops-Secret",
        "X-DevOps-Secret",
        "X-Crown-Ops-Secret",
    )

    def test_operations_headers_are_filtered_case_insensitively(self):
        for name in self.operations_headers:
            for header in (name, name.lower(), name.upper()):
                with self.subTest(header=header):
                    event = {
                        "request": {
                            "headers": {
                                header: "synthetic-ops-credential-not-live",
                                "User-Agent": "synthetic-client",
                            },
                        },
                    }

                    sanitized = before_send(event, {})

                    self.assertEqual(
                        sanitized["request"]["headers"][header], "[Filtered]"
                    )
                    self.assertEqual(
                        sanitized["request"]["headers"]["User-Agent"],
                        "synthetic-client",
                    )

    def test_serialized_event_omits_each_operations_credential(self):
        values = {
            name: f"synthetic-credential-{index}-not-live"
            for index, name in enumerate(self.operations_headers)
        }
        event = {
            "request": {"headers": values.copy()},
            "release": "synthetic-release",
        }

        sanitized = before_send(event, {})
        serialized = json.dumps(sanitized)

        for name, value in values.items():
            with self.subTest(header=name):
                self.assertEqual(
                    sanitized["request"]["headers"][name], "[Filtered]"
                )
                self.assertNotIn(value, serialized)
        self.assertEqual(sanitized["release"], "synthetic-release")


class SentryTransactionRedactionTests(unittest.TestCase):
    def test_transaction_headers_and_request_payload_are_minimized(self):
        event = {
            "type": "transaction",
            "transaction": "synthetic-crown-request",
            "request": {
                "headers": {
                    "X-Admin-Ops-Secret": "synthetic-transaction-ops-secret",
                    "User-Agent": "synthetic-client",
                },
                "data": {"test_payload": "synthetic-private-body"},
                "cookies": {"sessionid": "synthetic-cookie"},
                "query_string": "token=synthetic-query",
            },
        }
        sanitized = before_send(event, {})
        self.assertEqual(sanitized["request"]["headers"]["X-Admin-Ops-Secret"], "[Filtered]")
        self.assertEqual(sanitized["request"]["headers"]["User-Agent"], "synthetic-client")
        self.assertNotIn("data", sanitized["request"])
        self.assertNotIn("cookies", sanitized["request"])
        self.assertNotIn("query_string", sanitized["request"])
        for secret in (
            "synthetic-transaction-ops-secret",
            "synthetic-private-body",
            "synthetic-cookie",
            "synthetic-query",
        ):
            self.assertNotIn(secret, json.dumps(sanitized))
        self.assertEqual(sanitized["transaction"], "synthetic-crown-request")

    def test_non_mapping_headers_are_dropped_fail_closed(self):
        for headers in (
            [["X-DevOps-Secret", "synthetic-malformed-secret"]],
            "X-DevOps-Secret: synthetic-malformed-secret",
            None,
        ):
            with self.subTest(headers_type=type(headers).__name__):
                sanitized = before_send({"request": {"headers": headers}}, {})
                self.assertEqual(sanitized["request"]["headers"], {})
                self.assertNotIn("synthetic-malformed-secret", json.dumps(sanitized))

    def test_production_sentry_registers_transaction_filter(self):
        settings_path = Path(__file__).resolve().parents[2] / "crown_api" / "settings.py"
        source = ast.parse(settings_path.read_text(encoding="utf-8"))
        calls = [
            node for node in ast.walk(source)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "init"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "sentry_sdk"
        ]
        self.assertEqual(len(calls), 1)
        options = {keyword.arg: keyword.value for keyword in calls[0].keywords}
        self.assertIn("before_send_transaction", options)
        self.assertIsInstance(options["before_send_transaction"], ast.Name)
        self.assertEqual(options["before_send_transaction"].id, "before_send")


class SentryUrlMinimizationTests(unittest.TestCase):
    """Guard exception and transaction telemetry against raw path/query leaks."""

    def test_exception_drops_url_and_redacts_referer_without_losing_grouping(self):
        event = {
            "release": "synthetic-release",
            "request": {
                "url": "https://example.invalid/api/students/synthetic-student-id/?token=synthetic-private-query",
                "query_string": "token=synthetic-private-query",
                "headers": {
                    "Referer": "https://example.invalid/family/synthetic-guardian?code=synthetic-referrer",
                    "User-Agent": "synthetic-client",
                },
            },
            "user": {"id": "synthetic-internal-id", "email": "synthetic-person@example.invalid"},
        }
        sanitized = before_send(event, {})
        self.assertNotIn("url", sanitized["request"])
        self.assertNotIn("query_string", sanitized["request"])
        self.assertEqual(sanitized["request"]["headers"]["Referer"], "[Filtered]")
        self.assertEqual(sanitized["request"]["headers"]["User-Agent"], "synthetic-client")
        self.assertEqual(sanitized["user"], {"id": "synthetic-internal-id"})
        for value in (
            "synthetic-student-id", "synthetic-private-query",
            "synthetic-guardian", "synthetic-referrer", "synthetic-person@example.invalid",
        ):
            self.assertNotIn(value, json.dumps(sanitized))
        self.assertEqual(sanitized["release"], "synthetic-release")

    def test_transaction_drops_raw_url_and_url_bearing_headers(self):
        event = {
            "type": "transaction",
            "transaction": "synthetic-crown-request",
            "request": {
                "url": "/api/guardians/synthetic-private-id/?token=synthetic-query",
                "headers": {
                    "X-Original-URL": "/protected/synthetic-original",
                    "x-forwarded-uri": "/api?token=synthetic-forwarded",
                    "X-Original-Uri": "/api?token=synthetic-uri",
                    "X-Rewrite-URL": "/api?token=synthetic-rewrite",
                    "Referrer": "https://example.invalid/private?key=synthetic-referrer",
                    "User-Agent": "synthetic-client",
                },
            },
        }
        sanitized = before_send(event, {})
        self.assertNotIn("url", sanitized["request"])
        self.assertEqual(sanitized["transaction"], "synthetic-crown-request")
        self.assertEqual(sanitized["request"]["headers"]["User-Agent"], "synthetic-client")
        for name, value in sanitized["request"]["headers"].items():
            if name != "User-Agent":
                self.assertEqual(value, "[Filtered]")
        for value in (
            "synthetic-private-id", "synthetic-query", "synthetic-original",
            "synthetic-forwarded", "synthetic-uri", "synthetic-rewrite", "synthetic-referrer",
        ):
            self.assertNotIn(value, json.dumps(sanitized))

    def test_non_mapping_header_payload_stays_fail_closed_with_raw_url(self):
        for headers in (
            [["Referer", "synthetic-secret"]],
            "Referer: synthetic-secret",
            None,
        ):
            with self.subTest(headers_type=type(headers).__name__):
                sanitized = before_send({
                    "request": {
                        "url": "/sensitive?token=synthetic-secret",
                        "headers": headers,
                    }
                }, {})
                self.assertEqual(sanitized["request"]["headers"], {})
                self.assertNotIn("url", sanitized["request"])
