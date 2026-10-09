"""Regression tests for the evidence-limited DevSecOps register guard."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from verify_devsecops_maturity import validate_registry


class MaturityRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("docs/assessment.md", "evidence/control.md"):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("synthetic evidence placeholder", encoding="utf-8")
        self.payload = {
            "schema_version": 1,
            "repository": "Arete0920/Crown-CSMS",
            "source_snapshot_sha": "a" * 40,
            "assessment_scope": "repository-and-policy-evidence-only",
            "operational_certification": False,
            "independent_assurance": False,
            "document": "docs/assessment.md",
            "domains": [
                {
                    "id": name,
                    "name": "Synthetic competency",
                    "level": "UNASSESSED",
                    "assessment_status": "PROVISIONAL",
                    "source_evidence_state": "DESIGNED",
                    "operating_evidence_state": "NOT_VERIFIED",
                    "owner_role": "Accountable owner",
                    "observed": "Repository policy exists",
                    "gap": "No operational evidence",
                    "next_proof": "Complete actual operational validation",
                    "evidence_paths": ["evidence/control.md"],
                    "open_issues": [173],
                }
                for name in (
                    "culture", "plan_develop", "build_test",
                    "release_deploy", "operate", "observe_respond",
                )
            ],
        }

    def test_provisional_register_passes(self):
        self.assertEqual(validate_registry(self.payload, self.root), [])

    def test_missing_competency_fails(self):
        self.payload["domains"].pop()
        self.assertTrue(validate_registry(self.payload, self.root))

    def test_duplicate_competency_fails(self):
        self.payload["domains"][1]["id"] = "culture"
        self.assertTrue(validate_registry(self.payload, self.root))

    def test_operating_claim_cannot_be_silently_enabled(self):
        self.payload["operational_certification"] = True
        self.payload["domains"][0]["operating_evidence_state"] = "VERIFIED"
        failures = validate_registry(self.payload, self.root)
        self.assertTrue(any("operational_certification" in message for message in failures))
        self.assertTrue(any("no live operating evidence" in message for message in failures))

    def test_unknown_source_verification_is_rejected(self):
        self.payload["domains"][0]["source_evidence_state"] = "VERIFIED_SOURCE"
        self.assertTrue(validate_registry(self.payload, self.root))

    def test_missing_evidence_file_fails(self):
        self.payload["domains"][0]["evidence_paths"] = ["evidence/absent.md"]
        self.assertTrue(validate_registry(self.payload, self.root))

    def test_path_escape_fails(self):
        self.payload["domains"][0]["evidence_paths"] = ["../outside.md"]
        self.assertTrue(validate_registry(self.payload, self.root))

    def test_forged_approval_fails(self):
        self.payload["independent_assurance"] = True
        self.assertTrue(validate_registry(self.payload, self.root))

    def test_no_issue_reference_fails(self):
        self.payload["domains"][0]["open_issues"] = []
        self.assertTrue(validate_registry(self.payload, self.root))

    def test_non_object_domain_fails_without_crash(self):
        self.payload["domains"][0] = None
        self.assertTrue(validate_registry(self.payload, self.root))


if __name__ == "__main__":
    unittest.main()
