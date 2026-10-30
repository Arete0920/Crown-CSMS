"""Real-Git tests for the DEV deployment's manual exact-main guard.

No GitHub, Azure, credentials, or network calls are performed. Local bare
repositories model protected main and an older accepted rc commit.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile
import textwrap
import unittest


WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "deploy-dev.yml"


def _git(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _step_script(workflow: str) -> str:
    # Extract the executed shell command; tests run the actual YAML script rather
    # than duplicating its conditional logic in a mocked function.
    match = re.search(
        r"(?ms)^      - name: Verify accepted DEV source\n(.*?)(?=^      - name: |\Z)",
        workflow,
    )
    if match is None:
        raise AssertionError("DEV source verification step missing")
    body = match.group(1)
    block = re.search(r"(?ms)^        run: \|\n((?:^          .*\n|^\n)+)", body)
    if block is None:
        raise AssertionError("DEV source verification script missing")
    return textwrap.dedent(block.group(1))


class DevDeployExactMainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.origin = root / "origin.git"
        self.checkout = root / "checkout"
        self.origin.mkdir()
        self.checkout.mkdir()
        _git("init", "--bare", "-q", cwd=self.origin)
        _git("init", "-q", cwd=self.checkout)
        _git("config", "user.name", "CROWN Test", cwd=self.checkout)
        _git("config", "user.email", "crown@example.test", cwd=self.checkout)
        _git("checkout", "-b", "main", cwd=self.checkout)
        _git("remote", "add", "origin", str(self.origin), cwd=self.checkout)
        (self.checkout / "proof.txt").write_text("first\n", encoding="utf-8")
        _git("add", "proof.txt", cwd=self.checkout)
        _git("commit", "-qm", "accepted old commit", cwd=self.checkout)
        self.old = _git("rev-parse", "HEAD", cwd=self.checkout)
        (self.checkout / "proof.txt").write_text("second\n", encoding="utf-8")
        _git("commit", "-qam", "accepted new main", cwd=self.checkout)
        self.main = _git("rev-parse", "HEAD", cwd=self.checkout)
        _git("push", "-q", "origin", "main", cwd=self.checkout)
        self.workflow = WORKFLOW.read_text(encoding="utf-8")
        self.script = _step_script(self.workflow)

    def _run_guard(self, target: str, event: str, requested: str = "",
                   ref: str = "refs/heads/main") -> subprocess.CompletedProcess:
        _git("checkout", "--detach", "-q", target, cwd=self.checkout)
        with tempfile.TemporaryDirectory() as output:
            env = dict(os.environ, GITHUB_EVENT_NAME=event, GITHUB_REF=ref,
                       REQUESTED_REF=requested, GITHUB_OUTPUT=str(Path(output) / "output"),
                       GITHUB_ENV=str(Path(output) / "env"))
            return subprocess.run(["bash", "-euo", "pipefail", "-c", self.script],
                                  cwd=self.checkout, env=env,
                                  capture_output=True, text=True)

    def test_manual_old_sha_is_rejected_even_if_ancestor_of_main(self):
        result = self._run_guard(self.old, "workflow_dispatch", self.old)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("never an ancestor", result.stderr)

    def test_manual_current_main_is_accepted(self):
        result = self._run_guard(self.main, "workflow_dispatch", self.main)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_exact_commit_input_is_rejected(self):
        result = self._run_guard(self.main, "workflow_dispatch")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not match approved exact SHA", result.stderr)

    def test_ancestor_rc_push_is_rejected(self):
        result = self._run_guard(self.old, "push", self.old,
                                 ref="refs/heads/rc/stale")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("protected-main manual dispatch", result.stderr)

    def test_historic_main_dispatch_wrong_ref_is_rejected(self):
        result = self._run_guard(self.main, "workflow_dispatch", self.main,
                                 ref="refs/heads/rc/stale")
        self.assertNotEqual(result.returncode, 0)

    def test_source_check_runs_before_azure_login(self):
        self.assertLess(self.workflow.index("- name: Verify accepted DEV source"),
                        self.workflow.index("- name: Azure Login"))


if __name__ == "__main__":
    unittest.main()
