"""Hermetic contracts for opt-in reviewed-21 stage in canonical DEV Deploy.

No live Azure login, workflow dispatch, data write, or production operation.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "deploy-dev.yml"
SHA = "a" * 40


def env(**overrides):
    result = dict(
        os.environ,
        APPLY_REVIEWED21="true",
        CONFIRM_REVIEWED21="migrate-dev-reviewed-21",
        SYNTHETIC="true",
        RECOVERABLE="true",
        MAINTENANCE="true",
        RESTORE_RUN="42273955790",
        RESTORE_ARTIFACT="13532038006",
        GITHUB_RUN_ID="42290000000",
        GITHUB_REPOSITORY="Arete0920/Crown-CSMS",
        GITHUB_REPOSITORY_ID="1339719218",
    )
    result.update(overrides)
    return result


class Reviewed21WorkflowContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        cls.wf = yaml.safe_load(cls.source)
        cls.events = cls.wf.get("on", cls.wf.get(True))
        cls.job = cls.wf["jobs"]["build-and-deploy"]
        cls.steps = cls.job["steps"]
        cls.guard = next(x["run"] for x in cls.steps if x.get("name") ==
                         "Require reviewed21 owner authority before any Azure credential")

    def run_guard(self, **overrides):
        return subprocess.run(
            ["bash", "-e", "-c", self.guard],
            env=env(**overrides), capture_output=True, text=True,
            check=False, timeout=5,
        )

    def test_keeps_canonical_single_manual_workflow_and_dev_serialization(self):
        self.assertEqual(set(self.events), {"workflow_dispatch"})
        self.assertEqual(self.wf["concurrency"]["group"], "crown-api-dev-deploy")
        self.assertIs(self.wf["concurrency"]["cancel-in-progress"], False)
        self.assertEqual(self.job["environment"], "dev")
        self.assertEqual(self.wf["permissions"]["id-token"], "write")
        self.assertEqual(self.wf["permissions"]["actions"], "read")
        self.assertNotIn("pull_request:", self.source)
        self.assertNotIn("push", self.events)

    def test_new_stage_is_optional_default_off_and_source_is_exact_main(self):
        inputs = self.events["workflow_dispatch"]["inputs"]
        self.assertEqual(len(inputs), 8)
        self.assertIs(inputs["apply_reviewed_heritage21"]["default"], False)
        self.assertEqual(inputs["ref"]["type"], "string")
        self.assertTrue(inputs["ref"]["required"])
        for key in ("synthetic_dev_confirmed", "backup_recovery_verified",
                    "maintenance_window_confirmed"):
            self.assertIs(inputs[key]["default"], False)
        names = [x.get("name", "") for x in self.steps]
        self.assertIn("Guard exact protected-main dispatch", names)
        self.assertIn("Verify accepted DEV source", names)
        self.assertIn("Reverify protected main before DEV migration", names)
        self.assertIn("Reverify protected main before DEV container deployment", names)

    def test_owner_confirmation_and_recovery_guards_reject_bad_inputs(self):
        result = self.run_guard()
        self.assertEqual(result.returncode, 0, result.stderr)
        for invalid in (
            dict(CONFIRM_REVIEWED21=""),
            dict(CONFIRM_REVIEWED21="migrate-dev-unreviewed"),
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
                blocked = self.run_guard(**invalid)
                self.assertNotEqual(blocked.returncode, 0,
                                    "accepted invalid release authority: " + repr(invalid))

    def test_default_off_path_is_unchanged_and_unexpected_extra_authority_rejected(self):
        self.assertEqual(self.run_guard(
            APPLY_REVIEWED21="false", CONFIRM_REVIEWED21="",
            SYNTHETIC="false", RECOVERABLE="false", MAINTENANCE="false",
            RESTORE_RUN="", RESTORE_ARTIFACT=""
        ).returncode, 0)
        for bad in (
            dict(CONFIRM_REVIEWED21="migrate-dev-reviewed-21"),
            dict(SYNTHETIC="true"), dict(RECOVERABLE="true"),
            dict(MAINTENANCE="true"), dict(RESTORE_RUN="42273955790"),
            dict(RESTORE_ARTIFACT="13532038006"),
        ):
            args = dict(APPLY_REVIEWED21="false", CONFIRM_REVIEWED21="",
                        SYNTHETIC="false", RECOVERABLE="false",
                        MAINTENANCE="false", RESTORE_RUN="", RESTORE_ARTIFACT="")
            args.update(bad)
            with self.subTest(bad=bad):
                self.assertNotEqual(self.run_guard(**args).returncode, 0)

    def test_before_azure_login_and_deploy_only_after_schema_success(self):
        names = [x.get("name", "") for x in self.steps]
        preflight = names.index("Require reviewed21 owner authority before any Azure credential")
        azure = names.index("Azure Login")
        migrate = names.index("Apply separately owner-authorized reviewed21 DEV schema stage")
        unchanged = names.index("Apply only reviewed DEV inquiry migration before deployment")
        deploy = names.index("Build and push Docker image")
        self.assertLess(preflight, azure)
        self.assertLess(azure, migrate)
        self.assertLess(migrate, unchanged)
        self.assertLess(unchanged, deploy)
        self.assertNotIn("az ", self.guard)
        self.assertNotIn("stage_dev_heritage_graph.py", self.guard)
        stage = self.steps[migrate]
        self.assertEqual(stage["if"], "inputs.apply_reviewed_heritage21 == true")
        self.assertEqual(stage["env"]["CROWN_STAGE_GITHUB_TOKEN"], "${{ github.token }}")
        for flag in ("--confirmation", "--synthetic-dev-confirmed",
                     "--backup-recovery-verified", "--maintenance-window-confirmed",
                     "--rehearsal-run-id", "--rehearsal-artifact-id"):
            self.assertIn(flag, stage["run"])

    def test_evidence_retained_but_no_prod_crossing_or_gate_weakening(self):
        artifact = next(s for s in self.steps if s.get("name") ==
                        "Preserve audited reviewed21 DEV schema receipt")
        self.assertEqual(artifact["if"],
                         "always() && inputs.apply_reviewed_heritage21 == true")
        self.assertEqual(artifact["with"]["retention-days"], 7)
        self.assertIn("reviewed-dev-schema-stage.json", artifact["with"]["path"])
        self.assertIn("python scripts/ops/run_dev_inquiry_migration.py",
                      next(s["run"] for s in self.steps
                           if s.get("name") ==
                           "Apply only reviewed DEV inquiry migration before deployment"))
        self.assertIn("Verify SimpleJWT migration allowlist",
                      " ".join(str(x.get("name", "")) for x in self.steps))
        self.assertEqual(len(self.wf["jobs"]), 1)


if __name__ == "__main__":
    unittest.main()
