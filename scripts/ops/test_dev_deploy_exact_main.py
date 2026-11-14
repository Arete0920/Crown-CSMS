"""Real-Git tests for the DEV deployment's manual exact-main guard.

No GitHub, Azure, credentials, or network calls are performed. Local bare
repositories model protected main and an older accepted rc commit.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest


WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "deploy-dev.yml"


class DevMigrationOutputContractTests(unittest.TestCase):
    """Execute the deployed shell producer/redirection/consumer, without Azure/DB."""

    def setUp(self):
        import yaml
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        self.script = next(
            step["run"] for job in workflow["jobs"].values() for step in job["steps"]
            if step.get("name") ==
            "Verify zero pending DEV migrations using read-only PostgreSQL connection"
        )
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        wrapper = self.root / "scripts/ops/run_dev_inquiry_migration.py"
        wrapper.parent.mkdir(parents=True)
        ops = str(WORKFLOW.parents[2] / "scripts/ops")
        # Only external boundaries are mocked. Normal cases run main() directly
        # into the workflow's redirected file; injected reports test the consumer.
        wrapper.write_text(textwrap.dedent(f'''\
            import contextlib
            import io
            import os
            import sys
            from unittest.mock import patch
            sys.path.insert(0, {ops!r})
            import run_dev_inquiry_migration as migration

            def inventory(*args, **kwargs):
                assert kwargs == dict(check_only=True, inventory_only=True,
                                      hosted_blacklist_enabled=False)
                if os.environ.get("INVENTORY_FAIL") == "true":
                    raise RuntimeError("synthetic-password synthetic-secret")
                return ["synthetic.0001_pending"] * int(os.environ["PENDING"])

            source = (contextlib.nullcontext() if os.environ.get("REAL_SOURCE")
                      else patch.object(migration, "validate_source"))
            with source, patch.object(migration, "load_dev_settings", return_value=(
                "postgresql://synthetic:synthetic-password@crown-pg-dev.postgres.database.azure.com/crown?sslmode=require",
                "synthetic-secret", "crown", False
            )), patch.object(migration, "migrate_on_dev", side_effect=inventory):
                if "REPORT_OVERRIDE" in os.environ:
                    with contextlib.redirect_stdout(io.StringIO()):
                        code = migration.main(sys.argv[1:])
                    print(os.environ["REPORT_OVERRIDE"], end="")
                else:
                    code = migration.main(sys.argv[1:])
            raise SystemExit(code)
        '''), encoding="utf-8")

    def _run(self, **overrides):
        env = dict(os.environ, GITHUB_ACTIONS="true", RUNNER_TEMP=str(self.root),
                   EXPECTED_SOURCE_SHA="a" * 40, PENDING="0",
                   PATH=str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"])
        env.update(overrides)
        result = subprocess.run(["bash", "-c", self.script], cwd=self.root,
                                env=env, capture_output=True, text=True, timeout=30)
        report = (self.root / "dev-pending-migration-inventory.json").read_text(encoding="utf-8")
        return result, report

    def test_redirected_inventory_is_complete_json_and_zero_pending_passes(self):
        result, report = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(report)["remaining_pending"], 0)
        self.assertIn("PASS: zero pending migrations", result.stdout)
        self.assertEqual(len(result.stderr.splitlines()), 2)
        self.assertTrue(all(line.startswith("::add-mask::") for line in result.stderr.splitlines()))
        for secret in ("postgresql://", "synthetic-password", "synthetic-secret", "::add-mask::"):
            self.assertNotIn(secret, report)

    def test_pending_inventory_and_failed_inventory_block(self):
        for overrides in ({"PENDING": "1"}, {"INVENTORY_FAIL": "true"}):
            with self.subTest(overrides=overrides):
                result, report = self._run(**overrides)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("PASS: zero pending", result.stdout)
                packet = json.loads(report)
                self.assertEqual(packet["status"],
                                 "BLOCKED" if "INVENTORY_FAIL" in overrides else "COLLECTED")
                self.assertNotIn("synthetic-password", report)
                self.assertNotIn("synthetic-secret", report)

    def test_missing_invalid_and_unknown_reports_block(self):
        _, report = self._run()
        packet = json.loads(report)
        bad_reports = ["", "not-json", "{}", "[]", "null", "::add-mask::synthetic\n" + report]
        for field, value in (("remaining_pending", None), ("remaining_pending", "0"),
                             ("remaining_pending", False), ("remaining_pending", 1),
                             ("status", "BLOCKED"), ("mode", "migrate"),
                             ("source_sha", "bad-source"), ("source_sha", "b" * 40),
                             ("inventory_scope", "unknown"), ("schema_change_authorized", True),
                             ("operational_certified", True)):
            bad_reports.append(json.dumps(dict(packet, **{field: value})))
        missing_pending = dict(packet)
        missing_pending.pop("remaining_pending")
        bad_reports.append(json.dumps(missing_pending))
        for bad in bad_reports:
            with self.subTest(report=bad):
                result, _ = self._run(REPORT_OVERRIDE=bad)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("PASS: zero pending", result.stdout)

    def test_malformed_source_blocks_before_credentials(self):
        result, report = self._run(EXPECTED_SOURCE_SHA="malformed", REAL_SOURCE="true")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        packet = json.loads(report)
        self.assertEqual(packet["reason"], "full_source_sha_required")
        self.assertIsNone(packet["source_sha"])


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
