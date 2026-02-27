"""
Wizard Discovery Endpoint Contract Test — Crown2026
====================================================
Validates GET /api/v1/wizards/ — the single source of truth for frontend alignment.

Checks:
  1. Unauthenticated request → 401 (not 404, which would mean the URL isn't wired)
  2. Authenticated request → 200 with correct envelope shape
  3. Every wizard in wizard_registry.WIZARDS appears in the response
  4. All entries have required keys and correct types
  5. slugs are unique — no double-registration
"""

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from crown_api.wizard_registry import WIZARDS

User = get_user_model()

DISCOVERY_URL = "/api/v1/wizards/"


def _authed_client():
    user = User.objects.create_user(username="wiz_disc_test", password="pw")
    c = APIClient()
    c.force_authenticate(user=user)
    return c


class TestWizardDiscoveryAuth(TestCase):
    """Unauthenticated request must return 401, not 404."""

    def test_requires_auth(self):
        c = APIClient()
        r = c.get(DISCOVERY_URL)
        self.assertEqual(
            r.status_code, 401,
            f"Expected 401 (auth gate), got {r.status_code} — "
            "404 means the URL isn't wired; 200 means auth is missing.",
        )


class TestWizardDiscoveryShape(TestCase):
    """Authenticated request returns correct envelope and entry shape."""

    def setUp(self):
        self.client = _authed_client()
        self.data = self.client.get(DISCOVERY_URL).json()

    def test_status_200(self):
        r = self.client.get(DISCOVERY_URL)
        self.assertEqual(r.status_code, 200)

    def test_envelope_key(self):
        self.assertIn("wizards", self.data)
        self.assertIsInstance(self.data["wizards"], list)

    def test_entry_required_fields(self):
        for entry in self.data["wizards"]:
            for field in ("key", "slug", "title", "enabled"):
                self.assertIn(field, entry, f"Entry missing field '{field}': {entry}")
            self.assertIsInstance(entry["key"], str)
            self.assertIsInstance(entry["slug"], str)
            self.assertIsInstance(entry["title"], str)
            self.assertIsInstance(entry["enabled"], bool)

    def test_no_empty_strings(self):
        for entry in self.data["wizards"]:
            self.assertTrue(entry["key"],  f"Empty key in {entry}")
            self.assertTrue(entry["slug"], f"Empty slug in {entry}")


class TestWizardDiscoveryCompleteness(TestCase):
    """
    Every entry in wizard_registry.WIZARDS must appear in the response.
    This prevents silent omissions if list_wizards() has a bug.
    """

    def setUp(self):
        self.client = _authed_client()
        r = self.client.get(DISCOVERY_URL)
        self.assertEqual(r.status_code, 200)
        self.wizards = r.json()["wizards"]

    def test_count_matches_registry(self):
        self.assertEqual(
            len(self.wizards), len(WIZARDS),
            f"Response has {len(self.wizards)} wizards; registry has {len(WIZARDS)}.",
        )

    def test_slugs_unique(self):
        slugs = [w["slug"] for w in self.wizards]
        self.assertEqual(len(slugs), len(set(slugs)), f"Duplicate slugs found: {slugs}")

    def test_keys_unique(self):
        keys = [w["key"] for w in self.wizards]
        self.assertEqual(len(keys), len(set(keys)), f"Duplicate keys found: {keys}")

    def test_expected_slugs_present(self):
        """Derive expected slugs from registry and confirm they all appear."""
        expected = {w["url_prefix"].split("/")[2] for w in WIZARDS}
        actual   = {w["slug"] for w in self.wizards}
        missing  = expected - actual
        self.assertFalse(missing, f"Slugs present in registry but missing from response: {missing}")
