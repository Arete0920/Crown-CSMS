import json
import unittest

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
