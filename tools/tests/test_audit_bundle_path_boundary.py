"""Boundary tests for manifest-selected audit evidence files."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from solomon_governance_c1 import verify_audit_pack_integrity as audit


class AuditBundlePathBoundaryTests(unittest.TestCase):
    def test_accepts_exact_required_file_names(self):
        hashes = {name: "f" * 64 for name in audit.REQUIRED_FILES}
        self.assertEqual(audit.validated_artifact_names(hashes), sorted(hashes))

    def test_rejects_traversal_and_unexpected_manifest_entries(self):
        expected = {name: "f" * 64 for name in audit.REQUIRED_FILES}
        for unexpected in ("../outside.txt", "/tmp/outside.txt", "folder/nested.txt"):
            with self.subTest(path=unexpected), self.assertRaises(SystemExit):
                audit.validated_artifact_names({**expected, unexpected: "0" * 64})
        with self.assertRaises(SystemExit):
            audit.validated_artifact_names({"00_OVERVIEW.txt": "f" * 64})
        with self.assertRaises(SystemExit):
            audit.validated_artifact_names(["00_OVERVIEW.txt"])

    def test_rejects_linked_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside.txt"
            outside.write_text("not part of the bundle", encoding="utf-8")
            target = root / "linked.txt"
            try:
                target.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable on test platform")
            with self.assertRaises(SystemExit):
                audit.require_regular_file(target)
            audit.require_regular_file(outside)

    def test_rejects_missing_and_directory_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(SystemExit):
                audit.require_regular_file(root / "missing.txt")
            with self.assertRaises(SystemExit):
                audit.require_regular_file(root)


if __name__ == "__main__":
    unittest.main()
