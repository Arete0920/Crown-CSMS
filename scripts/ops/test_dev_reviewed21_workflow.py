"""Built-in-only negative contracts for canonical guarded DEV deployment.

The bash authority gate is executed against fixed fake metadata; no Azure calls.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
from textwrap import dedent
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "deploy-dev.yml"
SHA = "a" * 40
GUARD = "Require reviewed21 owner authority before any Azure credential"
STAGE = "Apply separately owner-authorized reviewed21 DEV schema stage"


def step_body(source, name):
    anchor = "      - name: " + name + "\n"
    if source.count(anchor) != 1:
        raise AssertionError("expected one step named " + name)
    return source.split(anchor, 1)[1].split("\n      - name: ", 1)[0]


def values(**overrides):
    result = dict(os.environ, APPLY_REVIEWED21="true",
                  CONFIRM_REVIEWED21="migrate-dev-reviewed-21",
                  SYNTHETIC="true", RECOVERABLE="true", MAINTENANCE="true",
                  RESTORE_RUN="42273955790", RESTORE_ARTIFACT="13532038006",
                  GITHUB_RUN_ID="42290000000",
                  GITHUB_REPOSITORY="Arete0920/Crown-CSMS",
                  GITHUB_REPOSITORY_ID="1339719218")
    result.update(overrides)
    return result


class Reviewed21WorkflowContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        cls.guard_body = step_body(cls.source, GUARD)
        cls.guard = dedent(cls.guard_body.split("\n        run: |\n", 1)[1])
        cls.stage = step_body(cls.source, STAGE)

    def run_guard(self, **override):
        if not shutil.which("bash"):
            self.skipTest("Bash not available on runner")
        return subprocess.run(
            ["bash", "-e", "-c", self.guard],
            env=values(**override), capture_output=True, text=True,
            check=False, timeout=5,
        )

    def test_canonical_deployment_only_manual_and_serialized(self):
        src = self.source
        self.assertRegex(src, r"(?m)^  workflow_dispatch:\s*$")
        self.assertNotRegex(src, r"(?m)^  (?:push|pull_request|schedule):\s*$")
        self.assertIn("  group: crown-api-dev-deploy\n", src)
        self.assertIn("  cancel-in-progress: false\n", src)
        self.assertIn("    environment: dev\n", src)
        self.assertIn("  actions: read\n", src)
        self.assertIn("  id-token: write\n", src)
        self.assertEqual(src.count("\n  build-and-deploy:\n"), 1)

    def test_only_eight_manual_inputs_and_new_action_default_off(self):
        source = self.source.split("  workflow_dispatch:\n    inputs:\n",1)[1].split("\nconcurrency:\n",1)[0]
        names = re.findall(r"(?m)^      ([a-z][a-z0-9_]+):\s*$", source)
        self.assertEqual(set(names), {
            "ref", "apply_reviewed_heritage21", "confirm_dev_reviewed21",
            "synthetic_dev_confirmed", "backup_recovery_verified",
            "maintenance_window_confirmed", "rehearsal_run_id",
            "rehearsal_artifact_id",
        })
        for name in ("apply_reviewed_heritage21", "synthetic_dev_confirmed",
                     "backup_recovery_verified", "maintenance_window_confirmed"):
            entry = source.split("      " + name + ":\n",1)[1].split("\n      ",1)[0]
            self.assertIn("default: false", entry)

    def test_explicit_stage_authority_and_negative_cases(self):
        self.assertEqual(self.run_guard().returncode, 0)
        for invalid in (
            dict(CONFIRM_REVIEWED21=""),
            dict(CONFIRM_REVIEWED21="not-reviewed"),
            dict(SYNTHETIC="false"),
            dict(RECOVERABLE="false"),
            dict(MAINTENANCE="false"),
            dict(RESTORE_RUN=""),
            dict(RESTORE_ARTIFACT=""),
            dict(RESTORE_RUN="42290000000"),
            dict(GITHUB_REPOSITORY="other/fork"),
            dict(GITHUB_REPOSITORY_ID="2"),
        ):
            with self.subTest(invalid=invalid):
                self.assertNotEqual(self.run_guard(**invalid).returncode, 0)

    def test_default_off_path_requires_no_hidden_authorization(self):
        clean = dict(APPLY_REVIEWED21="false", CONFIRM_REVIEWED21="",
                     SYNTHETIC="false", RECOVERABLE="false",
                     MAINTENANCE="false", RESTORE_RUN="", RESTORE_ARTIFACT="")
        self.assertEqual(self.run_guard(**clean).returncode, 0)
        for invalid in (dict(CONFIRM_REVIEWED21="migrate-dev-reviewed-21"),
                        dict(SYNTHETIC="true"), dict(RECOVERABLE="true"),
                        dict(MAINTENANCE="true"),
                        dict(RESTORE_RUN="42273955790"),
                        dict(RESTORE_ARTIFACT="13532038006")):
            with self.subTest(invalid=invalid):
                self.assertNotEqual(self.run_guard(**dict(clean,**invalid)).returncode,0)

    def test_schema_lock_happens_after_login_and_before_image_mutation(self):
        src = self.source
        self.assertLess(src.index("      - name: " + GUARD),
                        src.index("      - name: Azure Login"))
        self.assertLess(src.index("      - name: Azure Login"),
                        src.index("      - name: " + STAGE))
        self.assertLess(src.index("      - name: " + STAGE),
                        src.index("      - name: Apply only reviewed DEV inquiry migration before deployment"))
        self.assertLess(src.index("      - name: " + STAGE),
                        src.index("      - name: Build and push Docker image"))
        self.assertNotIn("az ", self.guard)
        self.assertNotIn("stage_dev_heritage_graph.py", self.guard)
        self.assertIn("if: inputs.apply_reviewed_heritage21 == true", self.stage)
        self.assertIn("CROWN_STAGE_GITHUB_TOKEN: ${{ github.token }}",self.stage)
        for arg in ("--expected-sha", "--confirmation", "--synthetic-dev-confirmed",
                    "--backup-recovery-verified","--maintenance-window-confirmed",
                    "--rehearsal-run-id","--rehearsal-artifact-id"):
            self.assertIn(arg,self.stage)

    def test_evidence_and_existing_release_guards_retained(self):
        evidence = step_body(self.source,"Preserve audited reviewed21 DEV schema receipt")
        self.assertIn("if: always() && inputs.apply_reviewed_heritage21 == true",evidence)
        self.assertIn("retention-days: 7",evidence)
        self.assertIn("reviewed-dev-schema-stage.json",evidence)
        for name in (
            "Guard exact protected-main dispatch",
            "Verify accepted DEV source",
            "Reverify protected main before DEV migration",
            "Reverify protected main before DEV container deployment",
            "Verify SimpleJWT migration allowlist without database access",
            "Apply only reviewed DEV inquiry migration before deployment",
        ):
            self.assertIn("      - name: " + name, self.source)


if __name__ == "__main__":
    unittest.main()
