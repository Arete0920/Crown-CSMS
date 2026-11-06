"""Offline negative contracts for manual-only DEV reviewed-21 workflow (#427).

Reads the workflow and executes ONLY the pure bash authority guard. No cloud
credentials, GitHub mutations, Azure calls, database access, or schema writes.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / ".github" / "workflows" / "dev-reviewed-21-migration-stage.yml"
SHA = "a" * 40


def workflow():
    return yaml.safe_load(PATH.read_text(encoding="utf-8"))


def actions_environment(**overrides):
    env = dict(
        os.environ, EXPECTED_SHA=SHA, CONFIRM="migrate-dev-reviewed-21",
        SYNTHETIC="true", RECOVERABLE="true", WINDOW="true",
        PRIOR_RUN="42273955790", PRIOR_ARTIFACT="13532038006",
        GITHUB_ACTIONS="true", GITHUB_EVENT_NAME="workflow_dispatch",
        GITHUB_REF="refs/heads/main", GITHUB_SHA=SHA,
        GITHUB_RUN_ID="42290000000", GITHUB_REPOSITORY="Arete0920/Crown-CSMS",
        GITHUB_REPOSITORY_ID="1339719218",
    )
    env.update(overrides)
    return env


class Reviewed21WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PATH.read_text(encoding="utf-8")
        cls.wf = workflow()
        cls.events = cls.wf.get("on", cls.wf.get(True))
        cls.stage = cls.wf["jobs"]["migrate-reviewed-21"]
        cls.steps = cls.stage["steps"]
        cls.guard = next(x["run"] for x in cls.steps
                         if x.get("name") ==
                         "Require explicit owner authority before credentials or database access")

    def check_guard(self, **env):
        return subprocess.run(
            ["bash", "-e", "-c", self.guard],
            env=actions_environment(**env),
            capture_output=True, text=True, timeout=5, check=False,
        )

    def test_no_unattended_azure_schema_execution_path(self):
        self.assertEqual(set(self.events), {"pull_request", "workflow_dispatch"})
        self.assertEqual(set(self.wf["jobs"]), {"contract-tests", "migrate-reviewed-21"})
        self.assertEqual(self.wf["permissions"], {"contents": "read"})
        self.assertEqual(self.wf["concurrency"]["cancel-in-progress"], False)
        self.assertIn("github.event_name == 'pull_request'",
                      self.wf["jobs"]["contract-tests"]["if"])
        self.assertIn("github.event_name == 'workflow_dispatch'", self.stage["if"])
        self.assertIn("github.ref == 'refs/heads/main'", self.stage["if"])
        self.assertEqual(self.stage["environment"], "dev")
        self.assertEqual(self.stage["permissions"]["id-token"], "write")
        self.assertEqual(self.stage["permissions"]["actions"], "read")
        self.assertFalse(any("production" in str(x).lower()
                             for x in self.stage.get("environment", [])))

    def test_required_owner_inputs_default_to_fail_closed(self):
        inputs = self.events["workflow_dispatch"]["inputs"]
        self.assertEqual(len(inputs), 7)
        for name in ("expected_sha", "confirm_dev_reviewed21",
                     "synthetic_dev_confirmed", "backup_recovery_verified",
                     "maintenance_window_confirmed", "rehearsal_run_id",
                     "rehearsal_artifact_id"):
            self.assertTrue(inputs[name]["required"], name)
        for key in ("synthetic_dev_confirmed", "backup_recovery_verified",
                    "maintenance_window_confirmed"):
            self.assertIs(inputs[key]["default"], False, key)

    def test_valid_manual_owner_gate_and_required_negative_matrix(self):
        ok = self.check_guard()
        self.assertEqual(ok.returncode, 0, ok.stderr)
        negative = [
            dict(CONFIRM=""), dict(CONFIRM="migrate-dev-unsafe"),
            dict(SYNTHETIC="false"), dict(RECOVERABLE="false"),
            dict(WINDOW="false"), dict(EXPECTED_SHA="short"),
            dict(EXPECTED_SHA="b"*40),
            dict(GITHUB_EVENT_NAME="pull_request"),
            dict(GITHUB_REF="refs/heads/rc/main"),
            dict(GITHUB_SHA="b"*40),
            dict(GITHUB_REPOSITORY="someone/fork"),
            dict(GITHUB_REPOSITORY_ID="1"),
            dict(PRIOR_RUN="42290000000"),
            dict(PRIOR_RUN="no-id"),
            dict(PRIOR_ARTIFACT="no-id"),
            dict(GITHUB_RUN_ID="42273955790"),
        ]
        for invalid in negative:
            with self.subTest(invalid=invalid):
                result = self.check_guard(**invalid)
                self.assertNotEqual(result.returncode, 0,
                                    f"accepted invalid authority: {invalid}")

    def test_no_auth_before_guard_and_exact_main_identity(self):
        step_names = [x.get("name", "") for x in self.steps]
        self.assertEqual(step_names[0],
                         "Require explicit owner authority before credentials or database access")
        auth = step_names.index("Authenticate existing DEV identity via OIDC")
        stage = step_names.index(
            "Apply exact reviewed 21-migration plan with authenticated receipt and DB lock")
        main = step_names.index("Verify immutable source matches live protected main")
        self.assertLess(main, auth)
        self.assertLess(auth, stage)
        self.assertNotIn("az ", self.guard)
        self.assertNotIn("stage_dev_heritage_graph.py", self.guard)
        checkout = next(x for x in self.steps
                        if x.get("name") == "Checkout exact accepted main")
        self.assertEqual(checkout["with"]["ref"], "${{ inputs.expected_sha }}")
        self.assertIs(checkout["with"]["persist-credentials"], False)
        main_check = next(x for x in self.steps
                          if x.get("name") == "Verify immutable source matches live protected main")
        self.assertIn("git rev-parse refs/remotes/origin/main", main_check["run"])
        self.assertIn("git rev-parse HEAD", main_check["run"])

    def test_github_receipt_token_and_stage_flags_are_bounded(self):
        script = next(x for x in self.steps
                      if x.get("name") ==
                      "Apply exact reviewed 21-migration plan with authenticated receipt and DB lock")
        env = script["env"]
        self.assertEqual(env["CROWN_STAGE_GITHUB_TOKEN"], "${{ github.token }}")
        self.assertIn("python scripts/ops/stage_dev_heritage_graph.py", script["run"])
        for marker in ("--expected-sha", "--confirmation", "--synthetic-dev-confirmed",
                       "--backup-recovery-verified", "--maintenance-window-confirmed",
                       "--rehearsal-run-id", "--rehearsal-artifact-id",
                       '--evidence-path "$RUNNER_TEMP/reviewed-dev-schema-stage.json"'):
            self.assertIn(marker, script["run"])
        self.assertNotIn("az webapp", script["run"])
        self.assertNotIn("az postgres", script["run"])
        self.assertNotIn("python manage.py migrate", script["run"])

    def test_fixed_retention_and_no_automatic_prod_deployment(self):
        upload = next(x for x in self.steps if x.get("name")
                      == "Preserve sanitized reviewed DEV stage result")
        self.assertEqual(upload["with"]["retention-days"], 7)
        self.assertEqual(upload["if"], "always()")
        self.assertFalse(re.search(r"^(\s*)push:", self.source, re.MULTILINE))
        self.assertFalse(re.search(r"^(\s*)schedule:", self.source, re.MULTILINE))
        self.assertNotIn("az webapp config container set", self.source)


if __name__ == "__main__":
    unittest.main()
