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
                   ref: str = "refs/heads/main",
                   workflow_sha: str | None = None) -> subprocess.CompletedProcess:
        _git("checkout", "--detach", "-q", target, cwd=self.checkout)
        with tempfile.TemporaryDirectory() as output:
            env = dict(os.environ, GITHUB_EVENT_NAME=event, GITHUB_REF=ref,
                       GITHUB_SHA=workflow_sha or target,
                       WORKFLOW_SHA=workflow_sha or target,
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

    def test_old_workflow_dispatch_cannot_authorize_new_main_checkout(self):
        result = self._run_guard(self.main, "workflow_dispatch", self.main,
                                 workflow_sha=self.old)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("workflow identity", result.stderr)

    def test_source_check_runs_before_azure_login(self):
        self.assertLess(self.workflow.index("- name: Verify accepted DEV source"),
                        self.workflow.index("- name: Azure Login"))


    def test_dev_deploy_requires_read_only_zero_pending_inventory_before_mutations(self):
        """Ordinary DEV deployment cannot apply schema or advance with unknown migrations."""
        workflow = WORKFLOW.read_text(encoding="utf-8")
        source = (WORKFLOW.parents[2] / "scripts" / "ops" /
                  "run_dev_inquiry_migration.py").read_text(encoding="utf-8")
        gate = workflow.split(
            "      - name: Verify zero pending DEV migrations using read-only PostgreSQL connection",
            1,
        )[1].split("      - name: Set up Docker Buildx", 1)[0]
        self.assertIn("--inspect-all-migrations", gate)
        self.assertIn("remaining_pending", gate)
        self.assertIn('result["remaining_pending"] != 0', gate)
        self.assertIn('result.get("schema_change_authorized") is not False', gate)
        self.assertNotIn("--apply-reviewed", gate)
        self.assertNotIn('run_dev_inquiry_migration.py --expected-sha "$EXPECTED_SOURCE_SHA"', workflow)
        # An invented check-only flag is not enough: the inventory connection
        # itself must be read-only so accidental DDL fails at the DB boundary.
        self.assertIn('default_transaction_read_only=on', source)
        self.assertIn('if inventory_only:', source)
        self.assertLess(
            workflow.index("      - name: Reverify protected main before DEV migration"),
            workflow.index("      - name: Verify zero pending DEV migrations using read-only PostgreSQL connection"),
        )
        self.assertLess(
            workflow.index("      - name: Verify zero pending DEV migrations using read-only PostgreSQL connection"),
            workflow.index("      - name: Build and push Docker image"),
        )

    def test_dev_image_build_precedes_runtime_setting_and_activation(self):
        """Never advertise the new SHA before its artifact is built and pushed."""
        workflow = WORKFLOW.read_text(encoding="utf-8")
        def location(step):
            return workflow.index("      - name: " + step)
        self.assertLess(location("Bake BUILD_SHA into artifact"), location("Build and push Docker image"))
        self.assertLess(location("Build and push Docker image"), location("Apply appsettings (allowlisted only)"))
        self.assertLess(location("Apply appsettings (allowlisted only)"),
                        location("Deploy to Azure Web App (managed identity pull)"))
        self.assertLess(location("Verify zero pending DEV migrations using read-only PostgreSQL connection"),
                        location("Apply appsettings (allowlisted only)"))
        # Preserve existing exact-main guards and approved manual-only activation.
        self.assertIn('  workflow_dispatch:', workflow)
        self.assertNotIn('  schedule:', workflow)
        self.assertIn('  group: crown-api-dev-deploy', workflow)
        self.assertIn('  cancel-in-progress: false', workflow)


    def test_dev_migration_inventory_report_parser_denies_nonzero_and_unknown(self):
        """Execute the actual workflow receipt classifier without Azure or DB access."""
        import json
        import sys

        workflow = WORKFLOW.read_text(encoding="utf-8")
        marker = """          python - "$report" <<'PY'\n"""
        self.assertEqual(workflow.count(marker), 1)
        body = workflow.split(marker, 1)[1].split("\n          PY", 1)[0]
        script = textwrap.dedent(body)
        expected = "a" * 40
        good = {
            "status": "COLLECTED",
            "mode": "inventory_all_read_only",
            "source_sha": expected,
            "inventory_scope": "enabled_django_app_graph",
            "schema_change_authorized": False,
            "operational_certified": False,
            "remaining_pending": 0,
        }
        cases = [
            ("clean", good, True),
            ("pending", {**good, "remaining_pending": 1}, False),
            ("unknown-plan", {**good, "remaining_pending": None}, False),
            ("boolean-count", {**good, "remaining_pending": False}, False),
            ("unreviewed", {**good, "schema_change_authorized": True}, False),
            ("untrusted-source", {**good, "source_sha": "b" * 40}, False),
            ("incorrect-mode", {**good, "mode": "migrate"}, False),
            ("not-certified", {**good, "operational_certified": True}, False),
            ("missing-status", {k: v for k, v in good.items() if k != "status"}, False),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            for name, payload, should_pass in cases:
                with self.subTest(name=name):
                    path.write_text(json.dumps(payload), encoding="utf-8")
                    completed = subprocess.run(
                        [sys.executable, "-c", script, str(path)],
                        env={**os.environ, "EXPECTED_SOURCE_SHA": expected},
                        capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(completed.returncode == 0, should_pass,
                                     completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
