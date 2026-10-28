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
