"""Synthetic regression contracts for security-held Solomon audit bundles.

Tests neither load private-key material nor authorize historical remediation.
"""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
LIFECYCLE_PATH = REPO_ROOT / "solomon_governance_c1" / "manage_bundle_lifecycle.py"
INDEX_PATH = (
    REPO_ROOT
    / "solomon_governance_c1"
    / "governance"
    / "c1"
    / "runtime"
    / "audit_pack"
    / "SUPERSESSION_INDEX.json"
)
AFFECTED_BUNDLE = "20260515T185051Z"


def load_lifecycle():
    """Import lifecycle operations without running the CLI entry point."""
    spec = importlib.util.spec_from_file_location(
        "crown_c1_bundle_lifecycle_contract", LIFECYCLE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Missing bundle lifecycle source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_index(active="synthetic-old"):
    """Provide a minimal local-only C1 selection fixture."""
    return {
        "index_version": "1",
        "active_bundle": active,
        "certified_bundles": [
            {"bundle_id": "synthetic-old", "status": "active"}
        ],
        "superseded_bundles": [],
        "revoked_bundles": [],
    }


class AuditBundleRevocationTests(unittest.TestCase):
    """Prove compromise quarantine is fail-closed and recoverable safely."""

    def setUp(self):
        self.lifecycle = load_lifecycle()

    def test_active_revocation_clears_selection_without_replacement(self):
        data = synthetic_index()
        with mock.patch.object(self.lifecycle, "load_index", return_value=data):
            with mock.patch.object(self.lifecycle, "save_index") as save:
                self.assertEqual(
                    self.lifecycle.mark_revoked("synthetic-old", "key compromised"),
                    0,
                )
        save.assert_called_once()
        self.assertIsNone(data["active_bundle"])
        self.assertEqual(data["certified_bundles"][0]["status"], "revoked")
        self.assertEqual(data["revoked_bundles"][0]["bundle_id"], "synthetic-old")

    def test_revoked_bundle_cannot_be_recertified(self):
        data = synthetic_index(active=None)
        data["certified_bundles"][0]["status"] = "revoked"
        data["revoked_bundles"].append({"bundle_id": "synthetic-old"})
        with mock.patch.object(self.lifecycle, "load_index", return_value=data):
            with mock.patch.object(self.lifecycle, "save_index") as save:
                self.assertEqual(self.lifecycle.mark_certified("synthetic-old"), 1)
        save.assert_not_called()

    def test_quarantined_bundle_cannot_be_recertified(self):
        data = synthetic_index(active=None)
        data["certified_bundles"][0]["status"] = "quarantined"
        with mock.patch.object(self.lifecycle, "load_index", return_value=data):
            with mock.patch.object(self.lifecycle, "save_index") as save:
                self.assertEqual(self.lifecycle.mark_certified("synthetic-old"), 1)
        save.assert_not_called()

    def test_security_hold_prevents_promotion_independently(self):
        data = synthetic_index(active=None)
        data["security_hold"] = {"bundle_id": "synthetic-old"}
        with mock.patch.object(self.lifecycle, "load_index", return_value=data):
            with mock.patch.object(self.lifecycle, "save_index") as save:
                self.assertEqual(self.lifecycle.mark_certified("synthetic-old"), 1)
        save.assert_not_called()

    def test_repeated_revocation_is_idempotent(self):
        data = synthetic_index(active=None)
        data["certified_bundles"][0]["status"] = "revoked"
        data["revoked_bundles"].append({"bundle_id": "synthetic-old"})
        with mock.patch.object(self.lifecycle, "load_index", return_value=data):
            with mock.patch.object(self.lifecycle, "save_index") as save:
                self.assertEqual(self.lifecycle.mark_revoked("synthetic-old"), 0)
        self.assertEqual(len(data["revoked_bundles"]), 1)
        save.assert_not_called()

    def test_unselected_revocation_preserves_other_active_bundle(self):
        data = synthetic_index(active="synthetic-new")
        with mock.patch.object(self.lifecycle, "load_index", return_value=data):
            with mock.patch.object(self.lifecycle, "save_index") as save:
                self.assertEqual(self.lifecycle.mark_revoked("synthetic-old"), 0)
        self.assertEqual(data["active_bundle"], "synthetic-new")
        save.assert_called_once()

    def test_distinct_replacement_can_be_promoted(self):
        data = synthetic_index(active=None)
        data["certified_bundles"][0]["status"] = "revoked"
        data["revoked_bundles"].append({"bundle_id": "synthetic-old"})
        with mock.patch.object(self.lifecycle, "load_index", return_value=data):
            with mock.patch.object(self.lifecycle, "save_index") as save:
                self.assertEqual(self.lifecycle.mark_certified("synthetic-new"), 0)
        self.assertEqual(data["active_bundle"], "synthetic-new")
        self.assertEqual(data["certified_bundles"][0]["status"], "revoked")
        save.assert_called_once()

    def test_repository_index_never_selects_exposed_attestation(self):
        """Protect the committed quarantine against accidental reactivation."""
        index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        self.assertNotEqual(index["active_bundle"], AFFECTED_BUNDLE)
        records = [
            entry
            for entry in index["certified_bundles"]
            if entry["bundle_id"] == AFFECTED_BUNDLE
        ]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "quarantined")
        self.assertEqual(index["security_hold"]["bundle_id"], AFFECTED_BUNDLE)
        self.assertEqual(
            index["security_hold"]["external_trust_disposition"],
            "unverified",
        )
        # Preserve the historical claim as evidence without adopting it.
        self.assertEqual(index["cryptographic_attestation"]["status"], "ATTESTED")


if __name__ == "__main__":
    unittest.main()
