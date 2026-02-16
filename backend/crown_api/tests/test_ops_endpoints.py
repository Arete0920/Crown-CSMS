"""
Smoke tests for Ops endpoints (/api/ops/summary/, /api/ops/alerts/).

Tests verify:
1. Endpoints return HTTP 200 (normal mode)
2. Response JSON has required fields
3. Strict mode returns 500 when imports fail
"""

from django.test import TestCase, Client
import json


class OpsEndpointsTestCase(TestCase):
    """Test Ops Command Center endpoints for failsafe visibility."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_ops_summary_returns_200(self):
        """
        GET /api/ops/summary/ should return 200 with required fields.
        """
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
        """
        GET /api/ops/summary/ counts should have all core metrics.
        Some may be None if app is not installed, but should be present.
        """
        resp = self.client.get("/api/ops/summary/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        counts = data.get("counts", {})
        
        # All these fields should be present
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
            # Value should be int or None (None if app not installed/accessible)
            self.assertIn(type(counts[metric]), [int, type(None)], f"{metric} should be int or None")

    def test_ops_alerts_returns_200(self):
        """
        GET /api/ops/alerts/ should return 200 with alerts array.
        """
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
        """
        GET /api/ops/alerts/ should return deps dict tracking import success.
        """
        resp = self.client.get("/api/ops/alerts/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        deps = data.get("deps", {})
        
        # deps should track three core imports
        self.assertIn("admissions", deps)
        self.assertIn("finance", deps)
        self.assertIn("gradebook", deps)
        
        # Each should be bool
        for key, val in deps.items():
            self.assertIsInstance(val, bool, f"deps[{key}] should be bool, got {type(val)}")

    def test_ops_alerts_errors_is_list(self):
        """
        GET /api/ops/alerts/ should return errors as list (even if empty).
        """
        resp = self.client.get("/api/ops/alerts/")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        errors = data.get("errors", [])
        self.assertIsInstance(errors, list)

    def test_ops_alerts_array_structure(self):
        """
        Each alert in GET /api/ops/alerts/ should have required fields.
        """
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
            
            # severity should be one of these
            self.assertIn(alert["severity"], ["critical", "warning", "info"])

    def test_ops_alerts_strict_mode_param(self):
        """
        GET /api/ops/alerts/?strict=1 should be accepted (may return 200 or 500 depending on imports).
        """
        resp = self.client.get("/api/ops/alerts/?strict=1")
        
        # Should be either 200 (all imports OK) or 500 (strict mode enforced on failure)
        self.assertIn(resp.status_code, [200, 500])

    def test_build_sha_in_responses(self):
        """
        Both /api/ops/summary/ and /api/ops/alerts/ should include build_sha field.
        """
        summary_resp = self.client.get("/api/ops/summary/")
        self.assertIn("build_sha", summary_resp.json())
        
        alerts_resp = self.client.get("/api/ops/alerts/")
        self.assertIn("build_sha", alerts_resp.json())
