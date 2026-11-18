"""Boundary tests for manifest-selected audit evidence files."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from solomon_governance_c1 import verify_audit_pack_integrity as audit
from solomon_governance_c1 import generate_audit_pack as generator


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


    def test_runtime_generator_rejects_traversal_before_force_deletion(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "runtime"
            outside = base / "outside"
            outside.mkdir()
            sentinel = outside / "keep.txt"
            sentinel.write_text("DO NOT REMOVE", encoding="utf-8")
            with patch.object(generator, "RUNTIME_PACK_ROOT", root):
                for bundle_id in (
                    "../outside", "../../outside", "safe/../../outside",
                    r"..\\outside", "/tmp/outside", ".", "..", "a" * 81,
                ):
                    with self.subTest(bundle_id=bundle_id):
                        self.assertEqual(generator.generate_runtime_bundle(bundle_id, force=True), 1)
                        self.assertEqual(sentinel.read_text(encoding="utf-8"), "DO NOT REMOVE")
                        self.assertFalse(root.exists())
                self.assertEqual(
                    generator.validated_runtime_bundle_path("20260515T182250Z"),
                    root / "20260515T182250Z",
                )

    def test_runtime_generator_rejects_symlink_force_target(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "runtime"
            root.mkdir()
            outside = base / "outside"
            outside.mkdir()
            marker = outside / "keep.txt"
            marker.write_text("DO NOT REMOVE", encoding="utf-8")
            link = root / "linked"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable on test platform")
            with patch.object(generator, "RUNTIME_PACK_ROOT", root):
                with self.assertRaises(ValueError):
                    generator.validated_runtime_bundle_path("linked")
                self.assertEqual(generator.generate_runtime_bundle("linked", force=True), 1)
            self.assertTrue(link.is_symlink())
            self.assertEqual(marker.read_text(encoding="utf-8"), "DO NOT REMOVE")


    def test_runtime_generator_rejects_linked_root_before_force_deletion(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            external = base / "external"
            external.mkdir()
            sentinel = external / "keep.txt"
            sentinel.write_text("DO NOT REMOVE", encoding="utf-8")
            linked_root = base / "runtime"
            try:
                linked_root.symlink_to(external, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable on test platform")
            with patch.object(generator, "RUNTIME_PACK_ROOT", linked_root):
                self.assertEqual(generator.generate_runtime_bundle("keep", force=True), 1)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "DO NOT REMOVE")


if __name__ == "__main__":
    unittest.main()
