"""Offline acceptance tests for DEV-only SimpleJWT migration dispatch safety."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/dev-blacklist-database-inventory.yml"
RECOVERY = "https://github.com/Arete0920/Crown-CSMS/actions/runs/40220289175"
SHA = "a" * 40


def workflow():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def guard_env(**overrides):
    result = {
        "EXPECTED_SHA": SHA,
        "SUPPORT_MODE": "false",
        "LEGACY_MODE": "false",
        "BLACKLIST_MODE": "false",
        "CONFIRM_SUPPORT": "",
        "CONFIRM_LEGACY": "",
        "CONFIRM_BLACKLIST": "",
        "RECOVERY_RECEIPT": "",
        "INSPECT_PLAN": "false",
    }
    result.update(overrides)
    return {**os.environ, **result}


class DevBlacklistWorkflowStageTests(unittest.TestCase):
    def setUp(self):
        data = workflow()
        self.inspect = data["jobs"]["inspect"]
        self.stage = data["jobs"]["stage-reviewed-dev-migrations"]
        self.steps = self.stage["steps"]
        self.guard = next(step["run"] for step in self.steps
                          if step.get("name") == "Require exact authority before any Azure login")

    def run_guard(self, **env):
        return subprocess.run(["bash", "-e", "-c", self.guard], env=guard_env(**env),
                              capture_output=True, text=True, timeout=4)

    def test_all_three_mutually_exclusive_modes_have_explicit_inputs(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        for name in ("apply_reviewed_blacklist", "confirm_dev_blacklist", "dev_recovery_receipt"):
            self.assertIn(name + ":", source)
        self.assertIn("inputs.apply_reviewed_blacklist != true", self.inspect["if"])
        self.assertIn("inputs.apply_reviewed_blacklist == true", self.stage["if"])
        self.assertIn("github.ref == 'refs/heads/main'", self.stage["if"])
        self.assertEqual(self.stage["environment"], "dev")
        self.assertEqual(self.stage["permissions"]["id-token"], "write")

    def test_readonly_census_runs_on_manual_inspection_without_schema_application(self):
        steps = {step.get("name"): step for step in self.inspect["steps"]}
        for name in (
            "Verify census evidence boundary (offline)",
            "Collect DEV school counts (read-only, protected main)",
            "Retain sanitized school count evidence",
            "Discard local school count evidence",
        ):
            self.assertIn(name, steps)
            self.assertIn("github.event_name == 'push'", steps[name]["if"])
            self.assertIn("github.event_name == 'workflow_dispatch'", steps[name]["if"])
        census = steps["Collect DEV school counts (read-only, protected main)"]
        self.assertEqual(census["env"]["SHA"], "${{ inputs.expected_sha || github.sha }}")
        self.assertIn("read_dev_school_census.py", census["run"])
        self.assertNotIn("--apply", census["run"])
        self.assertEqual(self.inspect["environment"], "dev")

    def test_only_explicit_single_mode_authorized(self):
        valid = [
            dict(BLACKLIST_MODE="true", CONFIRM_BLACKLIST="migrate-dev-blacklist",
                 RECOVERY_RECEIPT=RECOVERY),
            dict(SUPPORT_MODE="true", CONFIRM_SUPPORT="migrate-dev-support"),
            dict(LEGACY_MODE="true", CONFIRM_LEGACY="migrate-dev-legacy-refresh"),
        ]
        for case in valid:
            with self.subTest(case=case):
                self.assertEqual(self.run_guard(**case).returncode, 0)

    def test_wrong_or_missing_authority_fails_closed(self):
        cases = [
            {}, dict(BLACKLIST_MODE="true"),
            dict(BLACKLIST_MODE="true", CONFIRM_BLACKLIST="migrate-dev-blacklist"),
            dict(BLACKLIST_MODE="true", CONFIRM_BLACKLIST="migrate-dev-blacklist",
                 RECOVERY_RECEIPT="https://example.org/backup"),
            dict(BLACKLIST_MODE="true", CONFIRM_BLACKLIST="migrate-dev-blacklist",
                 RECOVERY_RECEIPT=RECOVERY + "/../../../oops"),
            dict(BLACKLIST_MODE="true", CONFIRM_BLACKLIST="wrong", RECOVERY_RECEIPT=RECOVERY),
            dict(BLACKLIST_MODE="true", CONFIRM_BLACKLIST="migrate-dev-blacklist",
                 RECOVERY_RECEIPT=RECOVERY, SUPPORT_MODE="true"),
            dict(BLACKLIST_MODE="true", CONFIRM_BLACKLIST="migrate-dev-blacklist",
                 RECOVERY_RECEIPT=RECOVERY, LEGACY_MODE="true"),
            dict(SUPPORT_MODE="true", CONFIRM_SUPPORT="migrate-dev-support",
                 CONFIRM_BLACKLIST="migrate-dev-blacklist"),
            dict(LEGACY_MODE="true", CONFIRM_LEGACY="migrate-dev-legacy-refresh",
                 RECOVERY_RECEIPT=RECOVERY),
            dict(BLACKLIST_MODE="true", CONFIRM_BLACKLIST="migrate-dev-blacklist",
                 RECOVERY_RECEIPT=RECOVERY, INSPECT_PLAN="true"),
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertNotEqual(self.run_guard(**case).returncode, 0)

    def test_guard_occurs_before_any_credentialed_operation(self):
        names = [step.get("name", "") for step in self.steps]
        self.assertLess(names.index("Require exact authority before any Azure login"),
                        names.index("Authenticate existing DEV only"))
        self.assertLess(names.index("Require current accepted protected main"),
                        names.index("Authenticate existing DEV only"))
        self.assertIn("git rev-parse origin/main", next(step["run"] for step in self.steps
                     if step.get("name") == "Require current accepted protected main"))
        self.assertNotIn("az ", self.guard)
        self.assertNotIn("python scripts/ops/run_dev_inquiry_migration.py", self.guard)

    def test_application_path_is_schema_only_without_activation(self):
        text = next(step["run"] for step in self.steps
                    if step.get("name") == "Stage only the selected reviewed DEV migrations under PostgreSQL lock")
        self.assertIn("--apply-reviewed-blacklist", text)
        self.assertIn("--confirm-dev-blacklist migrate-dev-blacklist", text)
        self.assertIn('if [[ "$BLACKLIST_MODE" == "true" ]]', text)
        self.assertIn("migrate-dev-support", text)
        self.assertIn("migrate-dev-legacy-refresh", text)
        self.assertNotIn("az webapp config", text)
        self.assertNotIn("CROWN_SIMPLEJWT_BLACKLIST_ENABLED=true", text)
        self.assertNotIn("deploy", text.lower())
        self.assertIn("test_dev_blacklist_workflow_stage.py", next(step["run"] for step in self.steps
                      if step.get("name") == "Verify both fail-closed migration-stage contracts without Azure"))



class DevReleaseForensicsSafetyTests(unittest.TestCase):
    """DEV release evidence is an isolated, manual-only Azure read."""

    def setUp(self):
        data = workflow()
        self.inputs = data["on"]["workflow_dispatch"]["inputs"] if "on" in data else data[True]["workflow_dispatch"]["inputs"]
        self.jobs = data["jobs"]
        self.job = self.jobs["dev-release-forensics"]
        self.steps = self.job["steps"]

    def test_manual_opt_in_is_off_by_default_and_excludes_other_jobs(self):
        self.assertEqual(self.inputs["dev_release_forensics"]["type"], "boolean")
        self.assertFalse(self.inputs["dev_release_forensics"]["default"])
        self.assertIn("github.event_name == 'workflow_dispatch'", self.job["if"])
        self.assertIn("github.ref == 'refs/heads/main'", self.job["if"])
        self.assertIn("inputs.dev_release_forensics == true", self.job["if"])
        self.assertEqual(self.job["environment"], "dev")
        self.assertEqual(self.job["permissions"], {"contents": "read", "id-token": "write"})
        for name in ("two-fixed-reference-gets", "inspect", "stage-reviewed-dev-migrations"):
            self.assertIn("inputs.dev_release_forensics != true", self.jobs[name]["if"])

    def test_azure_login_follows_source_and_authority_guards(self):
        names = [step.get("name", "") for step in self.steps]
        auth = names.index("Login with existing DEV federation")
        self.assertLess(names.index("Reject mixed authority or stale main before Azure login"), auth)
        self.assertLess(names.index("Verify accepted source is current main"), auth)
        guard = self.steps[0]["run"]
        self.assertIn('test "$EXPECTED" = "$GITHUB_SHA"', guard)
        for key in ("APPLY_SUPPORT", "APPLY_LEGACY", "APPLY_BLACKLIST",
                    "COMPARE", "INSPECT"):
            self.assertIn('test "    unittest.main()
 + key + '" = false', guard)
        for key in ("CONFIRM_SUPPORT", "CONFIRM_LEGACY", "CONFIRM_BLACKLIST", "RECEIPT"):
            self.assertIn('test -z "    unittest.main()
 + key + '"', guard)

    def test_mixed_authority_fails_before_login(self):
        guard = self.steps[0]["run"]
        env = {
            **os.environ, "GITHUB_REPOSITORY_ID": "1339719218",
            "GITHUB_SHA": SHA, "EXPECTED": SHA,
            "APPLY_SUPPORT": "false", "APPLY_LEGACY": "false",
            "APPLY_BLACKLIST": "false", "COMPARE": "false",
            "INSPECT": "false", "CONFIRM_SUPPORT": "",
            "CONFIRM_LEGACY": "", "CONFIRM_BLACKLIST": "",
            "RECEIPT": "",
        }
        def run(**overrides):
            return subprocess.run(["bash", "-e", "-c", guard],
                                  env={**env, **overrides}, capture_output=True,
                                  text=True, timeout=4).returncode
        self.assertEqual(run(), 0)
        for change in ({"GITHUB_REPOSITORY_ID": "123"},
                       {"EXPECTED": "b" * 40},
                       {"APPLY_SUPPORT": "true"},
                       {"APPLY_LEGACY": "true"},
                       {"APPLY_BLACKLIST": "true"},
                       {"COMPARE": "true"},
                       {"INSPECT": "true"},
                       {"CONFIRM_SUPPORT": "migrate-dev-support"},
                       {"RECEIPT": RECOVERY}):
            with self.subTest(change=change):
                self.assertNotEqual(run(**change), 0)

    def test_collector_uses_only_read_commands_and_redacted_metadata(self):
        collector = next(s["run"] for s in self.steps
                         if s.get("name") == "Collect sanitized DEV configuration-change evidence")
        self.assertIn('"activity-log", "list"', collector)
        self.assertIn('"webapp", "config", "show"', collector)
        self.assertIn('"webapp", "config", "appsettings", "list"', collector)
        self.assertIn("caller_hash", collector)
        self.assertNotIn('"caller": caller', collector)
        self.assertIn('report["activity"]["status"] != "COLLECTED"', collector)
        self.assertIn("any(value == \"UNVERIFIED\"", collector)
        self.assertNotIn("az webapp config set", collector)
        self.assertNotIn("az webapp config container set", collector)


if __name__ == "__main__":
    unittest.main()
