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


if __name__ == "__main__":
    unittest.main()
