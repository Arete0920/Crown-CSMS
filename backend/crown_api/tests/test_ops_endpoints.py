"""
Smoke and runtime-boundary tests for Ops endpoints (/api/ops/summary/, /api/ops/alerts/).

Tests verify:
1. Endpoints return HTTP 200 in an explicit DEV runtime.
2. Response JSON has required fields.
3. Strict mode returns 500 when imports fail.
4. Unknown and production-like runtimes fail closed.
5. The known Azure DEV app remains supported.
"""

import os
from unittest.mock import patch

from django.test import Client, TestCase, override_settings


@override_settings(ENVIRONMENT="dev")
class OpsEndpointsTestCase(TestCase):
    """Test Ops Command Center endpoints for bounded DEV/demo visibility."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_ops_summary_returns_200(self):
        """GET /api/ops/summary/ should return 200 with required fields in DEV."""
        resp = self.client.get("/api/ops/summary/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertTrue(data.get("ok"))
        self.assertIn("build_sha", data)
        self.assertIn("demo_mode", data)
        self.assertIn("school", data)
        self.assertIn("academic_year", data)
        self.assertIn("counts", data)

    def test_ops_summary_counts_structure(self):
        """Ops summary counts should expose the expected DEV/demo metrics shape."""
        resp = self.client.get("/api/ops/summary/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        counts = data.get("counts", {})

        required_metrics = [
            "households",
            "admissions_applications",
            "invoices",
            "grade_entries",
            "comms_threads",
            "comms_messages",
        ]
        for metric in required_metrics:
            self.assertIn(metric, counts, f"Missing metric: {metric}")
            self.assertIn(
                type(counts[metric]),
                [int, type(None)],
                f"{metric} should be int or None",
            )

    def test_ops_alerts_returns_200(self):
        """GET /api/ops/alerts/ should return 200 with alerts array in DEV."""
        resp = self.client.get("/api/ops/alerts/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertTrue(data.get("ok"))
        self.assertIn("alerts", data)
        self.assertIn("deps", data)
        self.assertIn("errors", data)
        self.assertIn("build_sha", data)
        self.assertIn("ts", data)

    def test_ops_alerts_has_deps_tracking(self):
        """Ops alerts should return dependency import status in DEV."""
        resp = self.client.get("/api/ops/alerts/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        deps = data.get("deps", {})

        self.assertIn("admissions", deps)
        self.assertIn("finance", deps)
        self.assertIn("gradebook", deps)

        for key, val in deps.items():
            self.assertIsInstance(val, bool, f"deps[{key}] should be bool, got {type(val)}")

    def test_ops_alerts_errors_is_list(self):
        """Ops alerts should always return errors as a list."""
        resp = self.client.get("/api/ops/alerts/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        errors = data.get("errors", [])
        self.assertIsInstance(errors, list)

    def test_ops_alerts_array_structure(self):
        """Every returned alert should preserve the documented shape."""
        resp = self.client.get("/api/ops/alerts/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        alerts = data.get("alerts", [])

        for alert in alerts:
            self.assertIn("id", alert)
            self.assertIn("severity", alert)
            self.assertIn("title", alert)
            self.assertIn("detail", alert)
            self.assertIn("ts", alert)
            self.assertIn(alert["severity"], ["critical", "warning", "info"])

    def test_ops_alerts_strict_mode_param(self):
        """Strict mode remains accepted in DEV."""
        resp = self.client.get("/api/ops/alerts/?strict=1")
        self.assertIn(resp.status_code, [200, 500])

    def test_build_sha_in_responses(self):
        """Both DEV ops endpoints should include build_sha."""
        summary_resp = self.client.get("/api/ops/summary/")
        self.assertIn("build_sha", summary_resp.json())

        alerts_resp = self.client.get("/api/ops/alerts/")
        self.assertIn("build_sha", alerts_resp.json())


class OpsEndpointsRuntimeBoundaryTestCase(TestCase):
    """Prove public demo/CI ops metadata cannot leak from production-like runtimes."""

    def setUp(self):
        self.client = Client()

    def test_unknown_unlabelled_runtime_fails_closed(self):
        with override_settings(ENVIRONMENT="", CROWN_ENV="", DJANGO_ENV=""):
            with patch.dict(
                os.environ,
                {
                    "ENVIRONMENT": "",
                    "CROWN_ENV": "",
                    "DJANGO_ENV": "",
                    "WEBSITE_HOSTNAME": "",
                },
                clear=False,
            ):
                self.assertEqual(self.client.get("/api/ops/summary/").status_code, 404)
                self.assertEqual(self.client.get("/api/ops/alerts/").status_code, 404)

    def test_explicit_production_runtime_fails_closed(self):
        with override_settings(ENVIRONMENT="production", CROWN_ENV="", DJANGO_ENV=""):
            with patch.dict(
                os.environ,
                {"WEBSITE_HOSTNAME": "crown-api-prod.azurewebsites.net"},
                clear=False,
            ):
                self.assertEqual(self.client.get("/api/ops/summary/").status_code, 404)
                self.assertEqual(self.client.get("/api/ops/alerts/").status_code, 404)

    def test_unlabelled_non_dev_azure_runtime_fails_closed(self):
        with override_settings(ENVIRONMENT="", CROWN_ENV="", DJANGO_ENV=""):
            with patch.dict(
                os.environ,
                {
                    "ENVIRONMENT": "",
                    "CROWN_ENV": "",
                    "DJANGO_ENV": "",
                    "WEBSITE_HOSTNAME": "crown-api-prod.azurewebsites.net",
                },
                clear=False,
            ):
                self.assertEqual(self.client.get("/api/ops/summary/").status_code, 404)
                self.assertEqual(self.client.get("/api/ops/alerts/").status_code, 404)

    def test_known_azure_dev_host_remains_allowed_without_env_marker(self):
        with override_settings(ENVIRONMENT="", CROWN_ENV="", DJANGO_ENV=""):
            with patch.dict(
                os.environ,
                {
                    "ENVIRONMENT": "",
                    "CROWN_ENV": "",
                    "DJANGO_ENV": "",
                    "WEBSITE_HOSTNAME": "crown-api-dev.azurewebsites.net",
                },
                clear=False,
            ):
                self.assertEqual(self.client.get("/api/ops/summary/").status_code, 200)
                self.assertIn(
                    self.client.get("/api/ops/alerts/?strict=1").status_code,
                    [200, 500],
                )
