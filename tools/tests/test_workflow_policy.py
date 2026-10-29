"""Negative proofs for complete workflow inventory and immutable action references."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("workflow_policy", ROOT / "tools/verify_workflow_policy.py")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class WorkflowPolicyTests(unittest.TestCase):
    def test_mutable_container_action_is_rejected(self):
        for ref in ("docker://alpine:latest", "docker://alpine:3.20", "docker://alpine"):
            self.assertFalse(policy.is_pinned_uses(ref), ref)

    def test_only_full_container_digest_is_accepted(self):
        self.assertTrue(policy.is_pinned_uses("docker://alpine@sha256:" + "a" * 64))
        self.assertFalse(policy.is_pinned_uses("docker://alpine@sha256:abc"))

    def test_mutable_action_and_short_commit_are_rejected(self):
        for ref in ("actions/checkout@v4", "actions/checkout@main", "actions/checkout@abcdef"):
            self.assertFalse(policy.is_pinned_uses(ref), ref)
        self.assertTrue(policy.is_pinned_uses("actions/checkout@" + "a" * 40))
        self.assertTrue(policy.is_pinned_uses("./.github/workflows/schema-migration-stage.yml"))

    def test_unchanged_workflow_violation_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflows = root / ".github/workflows"
            workflows.mkdir(parents=True)
            (workflows / "old.yml").write_text(
                "name: Old\npermissions:\n  contents: read\n"
                "concurrency:\n  group: old\n  cancel-in-progress: false\n"
                "jobs:\n  scan:\n    runs-on: ubuntu-latest\n    timeout-minutes: 5\n"
                "    steps:\n      - uses: actions/checkout@v4\n", encoding="utf-8")
            with patch.object(policy, "ROOT", root), patch.object(policy, "WORKFLOWS", workflows), \
                 patch.object(policy, "CANONICAL_WORKFLOW_FILES", {"old.yml"}), \
                 patch.object(policy, "PRODUCTION_DEPLOY_WORKFLOWS", set()), \
                 patch.object(sys, "argv", ["verify_workflow_policy.py"]), \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(policy.main(), 1)
                self.assertIn("unpinned uses", output.getvalue())

    def test_unregistered_yaml_workflow_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflows = root / ".github/workflows"
            workflows.mkdir(parents=True)
            (workflows / "hidden.yaml").write_text("name: Hidden\n", encoding="utf-8")
            with patch.object(policy, "ROOT", root), patch.object(policy, "WORKFLOWS", workflows), \
                 patch.object(policy, "CANONICAL_WORKFLOW_FILES", set()), \
                 patch.object(policy, "PRODUCTION_DEPLOY_WORKFLOWS", set()), \
                 patch.object(sys, "argv", ["verify_workflow_policy.py"]), \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(policy.main(), 1)
                self.assertIn("hidden.yaml", output.getvalue())

    def _production_mutex_result(self, *, extra=False, drift=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflows = root / '.github/workflows'
            workflows.mkdir(parents=True)
            names = {path.name for path in policy.PRODUCTION_IMAGE_MUTATION_WORKFLOWS}
            if extra:
                names.add('unrelated.yml')
            for name in names:
                group = 'wrong-group' if drift and name == 'prod-rollback-on-failure.yml' else policy.PRODUCTION_DEPLOY_GROUP
                (workflows / name).write_text(
                    f'name: {name}\npermissions:\n  contents: read\n'
                    f'concurrency:\n  group: {group}\n  cancel-in-progress: false\n'
                    'jobs:\n  proof:\n    runs-on: ubuntu-latest\n    timeout-minutes: 5\n'
                    '    steps:\n      - run: echo synthetic proof\n')
            with patch.object(policy, 'ROOT', root), patch.object(policy, 'WORKFLOWS', workflows), \
                 patch.object(policy, 'CANONICAL_WORKFLOW_FILES', names), \
                 patch.object(policy, 'DEV_RESET_WORKFLOWS', set()), \
                 patch.object(sys, 'argv', ['verify_workflow_policy.py']), \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                return policy.main(), output.getvalue()

    def test_only_four_known_image_writers_share_required_production_mutex(self):
        code, text = self._production_mutex_result()
        self.assertEqual(code, 0, text)

    def test_unrelated_workflow_cannot_join_production_mutex(self):
        code, text = self._production_mutex_result(extra=True)
        self.assertEqual(code, 1)
        self.assertIn('duplicate top-level concurrency group', text)

    def test_recovery_cannot_drift_outside_production_mutex(self):
        code, text = self._production_mutex_result(drift=True)
        self.assertEqual(code, 1)
        self.assertIn('production image mutation workflow must use shared concurrency group', text)

    def _dev_mutex_result(self, *, extra=False, drift=False, cancel=False, sink=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflows = root / ".github/workflows"
            workflows.mkdir(parents=True)
            names = {path.name for path in policy.DEV_RESET_WORKFLOWS}
            if extra:
                names.add("unrelated.yml")
            for name in sorted(names):
                group = "wrong-group" if drift and name == "demo-reset.yml" else policy.DEV_RESET_GROUP
                cancellation = "true" if cancel and name == "demo-reset.yml" else "false"
                step = "echo synthetic proof"
                if sink and name == "demo-reset.yml":
                    step = {
                        "tee": "curl --max-time 30 -f -sS https://example.test | tee /tmp/reset.json",
                        "echo": 'echo "$response"',
                    }[sink]
                (workflows / name).write_text(
                    f"name: {name}\npermissions:\n  contents: read\n"
                    f"concurrency:\n  group: {group}\n  cancel-in-progress: {cancellation}\n"
                    "jobs:\n  proof:\n    runs-on: ubuntu-latest\n    timeout-minutes: 5\n"
                    f"    steps:\n      - run: {step}\n",
                    encoding="utf-8",
                )
            with patch.object(policy, "ROOT", root), patch.object(policy, "WORKFLOWS", workflows), \
                 patch.object(policy, "CANONICAL_WORKFLOW_FILES", names), \
                 patch.object(policy, "PRODUCTION_IMAGE_MUTATION_WORKFLOWS", set()), \
                 patch.object(sys, "argv", ["verify_workflow_policy.py"]), \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                return policy.main(), output.getvalue()

    def test_only_two_dev_reset_entry_points_share_required_mutex(self):
        code, output = self._dev_mutex_result()
        self.assertEqual(code, 0, output)

    def test_unrelated_workflow_cannot_join_dev_reset_mutex(self):
        code, output = self._dev_mutex_result(extra=True)
        self.assertEqual(code, 1)
        self.assertIn("duplicate top-level concurrency group", output)

    def test_dev_reset_entry_point_cannot_escape_mutex(self):
        code, output = self._dev_mutex_result(drift=True)
        self.assertEqual(code, 1)
        self.assertIn("DEV reset workflow must use shared concurrency group", output)

    def test_dev_reset_cannot_cancel_active_reset(self):
        code, output = self._dev_mutex_result(cancel=True)
        self.assertEqual(code, 1)
        self.assertIn("must not cancel an active reset", output)

    def test_dev_reset_cannot_print_response_via_tee(self):
        code, output = self._dev_mutex_result(sink="tee")
        self.assertEqual(code, 1)
        self.assertIn("must not publish reset response bodies", output)

    def test_dev_reset_cannot_echo_response(self):
        code, output = self._dev_mutex_result(sink="echo")
        self.assertEqual(code, 1)
        self.assertIn("must not echo reset response bodies", output)

    def test_golden_path_smoke_never_publishes_ci_user_jwt(self):
        script = (ROOT / "tools/dev_scripts/golden_path.ps1").read_text(encoding="utf-8")
        self.assertNotIn("CI user ensured. Response:", script)
        self.assertNotIn("$resp | ConvertTo-Json", script)
        for secret_bearing_body in ("$r.Content", "$r2.Content", "$r3.Content"):
            self.assertNotIn(f"Write-Host {secret_bearing_body}", script)
        self.assertIn('return $resp', script)

    def test_repository_policy_invokes_complete_scan_unconditionally(self):
        import yaml
        workflow = yaml.safe_load((ROOT / ".github/workflows/repository-policy.yml").read_text())
        step = next(s for s in workflow["jobs"]["repository-policy"]["steps"]
                    if s.get("name") == "Enforce workflow policy")
        self.assertNotIn("if", step)
        self.assertIn("python tools/verify_workflow_policy.py\n", step["run"])
        self.assertNotIn("changed_workflows", step["run"])

    def test_schema_job_serialization_is_preserved(self):
        import yaml
        workflow = yaml.safe_load((ROOT / ".github/workflows/schema-migration-stage.yml").read_text())
        lock = workflow["jobs"]["production-migration"]["concurrency"]
        self.assertEqual(lock["group"], "crown-production-schema-migration")
        self.assertIs(lock["cancel-in-progress"], False)


class BranchAgeReportTests(unittest.TestCase):
    """Behavioral checks for the existing read-only branch-age report step."""

    @staticmethod
    def _report(*, state="ok", timestamp="1", protected=False):
        import json
        import os
        import subprocess
        import yaml

        doc = yaml.safe_load(
            (ROOT / ".github/workflows/repository-freshness.yml").read_text(encoding="utf-8")
        )
        steps = doc["jobs"]["report-stale-branches"]["steps"]
        script = next(
            step["run"] for step in steps
            if step.get("name") == "Report branches whose head commit is over 60 days old"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake_git = root / "git"
            fake_git.write_text(
                "#!/bin/sh\n"
                'case "$1" in\n'
                '  branch) printf "  origin/old-branch\\n";;\n'
                '  log)\n'
                '    case "$CROWN_TEST_GIT_STATUS" in\n'
                '      fail) echo "synthetic read failure" >&2; exit 128;;\n'
                '      empty) exit 0;;\n'
                '      invalid) printf "invalid-date\\n";;\n'
                '      *) printf "%s\\n" "$CROWN_TEST_GIT_TIMESTAMP";;\n'
                '    esac;;\n'
                '  *) echo "unexpected git operation" >&2; exit 2;;\n'
                'esac\n',
                encoding="utf-8",
            )
            fake_git.chmod(0o755)
            if protected:
                (root / "protected-branches.txt").write_text("old-branch\n", encoding="utf-8")
            env = {
                **os.environ,
                "PATH": str(root) + os.pathsep + os.environ["PATH"],
                "CROWN_TEST_GIT_STATUS": state,
                "CROWN_TEST_GIT_TIMESTAMP": timestamp,
            }
            result = subprocess.run(
                ["bash", "-e"], input=script, cwd=root, env=env,
                capture_output=True, text=True, check=False,
            )
            output = root / "stale-branches.json"
            records = json.loads(output.read_text(encoding="utf-8")) if output.exists() else None
            return result, records

    def test_missing_head_cannot_be_reported_as_old(self):
        run, records = self._report(state="fail")
        self.assertNotEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("Cannot read head commit", run.stdout)
        self.assertIsNone(records)

    def test_empty_or_invalid_head_timestamp_fails_closed(self):
        for state in ("empty", "invalid"):
            with self.subTest(state=state):
                run, records = self._report(state=state)
                self.assertNotEqual(run.returncode, 0, run.stdout + run.stderr)
                self.assertIn("Invalid head-commit timestamp", run.stdout)
                self.assertIsNone(records)

    def test_old_head_requires_review_and_is_not_deletion_permission(self):
        run, records = self._report(state="ok", timestamp="1")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["branch"], "old-branch")
        self.assertEqual(records[0]["head_commit_date"], "1970-01-01")
        self.assertEqual(records[0]["classification"], "age_only_not_deletion_approval")
        self.assertIn("Deletion is not authorized", run.stdout)

    def test_protected_branch_excluded(self):
        run, records = self._report(state="ok", timestamp="1", protected=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(records, [])


if __name__ == "__main__":
    unittest.main()
