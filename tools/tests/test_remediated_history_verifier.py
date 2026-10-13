"""Real Git fixtures for the security history verifier; no private keys used."""
import pathlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


VERIFIER = pathlib.Path(__file__).resolve().parents[1] / "verify_remediated_git_bundle.sh"
ARCHIVER = VERIFIER.with_name("create_verified_git_bundle.py")
FORBIDDEN_PATH = (
    "solomon_governance_c1/governance/c1/runtime/audit_pack/"
    "20260515T185051Z/crypto_attestation/ed25519_private_key_DO_NOT_SHARE.pem"
)


class HistoryVerifierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.git("init", "-q", str(self.repo), cwd=self.root)
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.repo / "README").write_text("fixture\n")
        self.commit()

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.repo,
                              check=True, capture_output=True, text=True).stdout.strip()

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")

    def verify(self, repo=None, bundle=None):
        target = ["--bundle", str(bundle)] if bundle else ["--repo", str(repo or self.repo)]
        return subprocess.run(["bash", str(VERIFIER), *target,
                               "--forbidden-path", "secret/key.pem"],
                              capture_output=True, text=True)

    def dirty_history(self):
        path = self.repo / "secret/key.pem"
        path.parent.mkdir()
        path.write_text("ordinary fixture text\n")
        self.commit()
        dirty = self.git("rev-parse", "HEAD")
        path.unlink()
        self.commit()
        return dirty

    def assert_rejected(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("verification=success", result.stdout)

    def test_clean_repository_and_restored_bundle(self):
        self.assertEqual(self.verify().returncode, 0)
        bundle = self.root / "clean.bundle"
        self.git("bundle", "create", str(bundle), "--all")
        self.assertEqual(self.verify(bundle=bundle).returncode, 0)

    def test_current_tree_deletion_does_not_clear_history(self):
        self.dirty_history()
        self.assert_rejected(self.verify())

    def test_shallow_clone_cannot_hide_dirty_ancestry(self):
        self.dirty_history()
        shallow = self.root / "shallow"
        self.git("clone", "-q", "--depth", "1", self.repo.as_uri(), str(shallow))
        self.assert_rejected(self.verify(repo=shallow))

    def test_replacement_commit_cannot_hide_history(self):
        clean = self.git("rev-parse", "HEAD")
        dirty = self.dirty_history()
        self.git("replace", dirty, clean)
        self.assert_rejected(self.verify())

    def test_missing_tree_is_not_path_absence(self):
        tree = self.git("rev-parse", "HEAD^{tree}")
        (self.repo / ".git/objects" / tree[:2] / tree[2:]).unlink()
        self.assert_rejected(self.verify())

    def test_hidden_pull_ref_is_included(self):
        clean = self.git("rev-parse", "HEAD")
        dirty = self.dirty_history()
        self.git("update-ref", "refs/pull/7/head", dirty)
        self.git("reset", "--hard", clean)
        self.assert_rejected(self.verify())

    def archive(self, repo=None, output=None):
        return subprocess.run(
            [sys.executable, str(ARCHIVER), "--repo", str(repo or self.repo),
             "--output", str(output or self.root / "export/archive.bundle")],
            capture_output=True, text=True,
        )

    def test_archive_restores_clean_history(self):
        output = self.root / "export/archive.bundle"
        self.assertEqual(self.archive(output=output).returncode, 0)
        result = subprocess.run(
            ["bash", str(VERIFIER), "--bundle", str(output),
             "--forbidden-path", FORBIDDEN_PATH], capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0)

    def test_archive_blocks_deleted_exposure_before_creating_output(self):
        path = self.repo / FORBIDDEN_PATH
        path.parent.mkdir(parents=True)
        path.write_text("ordinary fixture text; no private material\n")
        self.commit()
        path.unlink()
        self.commit()
        self.assertNotEqual(self.archive().returncode, 0)
        self.assertFalse((self.root / "export").exists())

    def test_archive_blocks_shallow_history(self):
        shallow = self.root / "shallow"
        self.git("clone", "-q", "--depth", "1", self.repo.as_uri(), str(shallow))
        self.assertNotEqual(self.archive(repo=shallow).returncode, 0)
        self.assertFalse((self.root / "export").exists())

    def test_archive_never_overwrites_existing_output(self):
        output = self.root / "existing.bundle"
        output.write_bytes(b"preserve existing evidence")
        self.assertNotEqual(self.archive(output=output).returncode, 0)
        self.assertEqual(output.read_bytes(), b"preserve existing evidence")

    def test_archive_rejects_history_introduced_during_capture(self):
        spec = importlib.util.spec_from_file_location("archive_guard", ARCHIVER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        real_run = subprocess.run

        def drift_before_capture(args, **kwargs):
            if args[:5] == ["git", "-C", str(self.repo), "bundle", "create"]:
                path = self.repo / FORBIDDEN_PATH
                path.parent.mkdir(parents=True)
                path.write_text("ordinary drift fixture; no private material\n")
                real_run(["git", "add", "."], cwd=self.repo, check=True, capture_output=True)
                real_run(["git", "commit", "-qm", "fixture drift"],
                         cwd=self.repo, check=True, capture_output=True)
            return real_run(args, **kwargs)

        output = self.root / "export/archive.bundle"
        with mock.patch.object(module.subprocess, "run", side_effect=drift_before_capture):
            with self.assertRaises(subprocess.CalledProcessError):
                module.create_bundle(self.repo, output)
        self.assertFalse(output.exists())
        self.assertEqual(list(output.parent.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
