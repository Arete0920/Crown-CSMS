"""Real Git fixtures for the security history verifier; no private keys used."""
import pathlib
import subprocess
import tempfile
import unittest


VERIFIER = pathlib.Path(__file__).resolve().parents[1] / "verify_remediated_git_bundle.sh"


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


if __name__ == "__main__":
    unittest.main()
