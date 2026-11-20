"""Synthetic-only boundary tests for CROWN #269 Azure reference evidence."""
import importlib.util
import json
import os
import tempfile
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import patch

MODULE = Path(__file__).with_name("crown269_reference_metadata_readonly.py")
modspec = importlib.util.spec_from_file_location("crown269_reference_metadata_readonly", MODULE)
mod = importlib.util.module_from_spec(modspec)
modspec.loader.exec_module(mod)
WF = Path(__file__).resolve().parents[2] / ".github/workflows/dev-blacklist-database-inventory.yml"
ACCOUNT = {"id": mod.SUBSCRIPTION_ID, "tenant": "00000000-0000-0000-0000-000000000001"}
ENV = {
    "CROWN269_EXPECTED_TENANT": ACCOUNT["tenant"],
    "CROWN269_EXPECTED_SUBSCRIPTION": mod.SUBSCRIPTION_ID,
    "GITHUB_RUN_ID": "43806004243",
    "GITHUB_SHA": "a"*40,
}


def good_reader(args):
    if args[:2] == ["account", "show"]:
        return dict(ACCOUNT)
    return {"status": "Resolved", "source_ok": True, "target_ok": True,
            "active_version_present": True}


class MetadataReadOnlyTests(unittest.TestCase):
    def test_exact_allowlist_and_documented_api(self):
        self.assertEqual(set(mod.TARGETS), {"CROWN_OPS_SECRET", "DEV_OPS_SECRET"})
        for key in mod.TARGETS:
            self.assertTrue(mod.api_url(key).startswith("https://management.azure.com/subscriptions/"))
            self.assertIn("/config/configreferences/appsettings/", mod.api_url(key))
            self.assertIn("api-version=2025-05-01", mod.api_url(key))
        with self.assertRaises(ValueError):
            mod.api_url("OPS_SECRET")
        with self.assertRaises(ValueError):
            mod.metadata_projection("OPS_SECRET")

    def test_good_metadata_produces_bounded_pass(self):
        result = mod.inspect(ENV, reader=good_reader)
        self.assertEqual(result["overall"], "PASS_TWO_REFERENCE_METADATA_ONLY_OTHER_269_ITEMS_OPEN")
        self.assertEqual(len(result["checks"]), 2)
        self.assertEqual(result["github_run_id"], ENV["GITHUB_RUN_ID"])
        self.assertEqual(result["github_source_sha"], ENV["GITHUB_SHA"])
        self.assertEqual(result["legacy_ops_secret_presence"], "NOT_VERIFIED_AVOIDS_APPSETTING_VALUE_READ")

    def test_command_boundary_three_reads_only(self):
        calls = []
        def spy(args):
            calls.append(args)
            return good_reader(args)
        mod.inspect(ENV, reader=spy)
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0][:2], ["account", "show"])
        for x in calls[1:]:
            self.assertEqual(x[:3], ["rest", "--method", "GET"])
            self.assertEqual(x[3], "--url")
            self.assertEqual(x[5], "--query")
            self.assertNotIn("/refresh", x[4])
            self.assertNotIn("/config/appsettings", x[4])
            self.assertEqual(x.count("--url"), 1)
        self.assertEqual({x[4].split("/")[-1].split("?")[0] for x in calls[1:]}, set(mod.TARGETS))

    def test_bad_expected_identity_never_calls_azure(self):
        for variant in [
            {},
            dict(ENV, CROWN269_EXPECTED_SUBSCRIPTION="wrong"),
            dict(ENV, CROWN269_EXPECTED_TENANT="not-a-uuid"),
        ]:
            def blocked(_):
                raise AssertionError("Azure called before identity validated")
            result = mod.inspect(variant, reader=blocked)
            self.assertEqual(result["overall"], "BLOCKED_EXPECTED_OIDC_IDENTITY_NOT_CONFIGURED")

    def test_wrong_account_stops_before_arm_reads(self):
        seen = []
        def reader(args):
            seen.append(args)
            return {"id": "ffffffff-ffff-ffff-ffff-ffffffffffff", "tenant": ACCOUNT["tenant"]}
        result = mod.inspect(ENV, reader=reader)
        self.assertEqual(result["overall"], "BLOCKED_WRONG_AZURE_ACCOUNT_OR_TENANT")
        self.assertEqual(len(seen), 1)

    def test_denied_or_unavailable_is_not_verified(self):
        def blocked(args):
            return dict(ACCOUNT) if args[0] == "account" else None
        result = mod.inspect(ENV, reader=blocked)
        self.assertEqual(result["overall"], "REVIEW_REQUIRED_KEYVAULT_REFERENCE_METADATA")
        self.assertTrue(all(item["outcome"] == "NOT_VERIFIED_ARM_READ_UNAVAILABLE" for item in result["checks"]))

    def test_missing_version_and_unresolved_and_bad_target_fail_closed(self):
        for bad in [
            {"status": "Resolved", "source_ok": True, "target_ok": True, "active_version_present": False},
            {"status": "SecretNotFound", "source_ok": True, "target_ok": True, "active_version_present": True},
            {"status": "Resolved", "source_ok": True, "target_ok": False, "active_version_present": True},
            {"status": "Resolved", "source_ok": "true", "target_ok": True, "active_version_present": True},
        ]:
            def reader(args):
                return dict(ACCOUNT) if args[0] == "account" else dict(bad)
            result = mod.inspect(ENV, reader=reader)
            self.assertEqual(result["overall"], "REVIEW_REQUIRED_KEYVAULT_REFERENCE_METADATA")

    def test_untrusted_result_fields_not_emitted(self):
        def reader(args):
            if args[0] == "account":
                return dict(ACCOUNT)
            return {"status": "UNTRUSTED_CANARY_VALUE", "source_ok": True,
                    "target_ok": True, "active_version_present": True,
                    "reference": "UNTRUSTED_CANARY_VALUE", "activeVersion": "UNTRUSTED_CANARY_VALUE",
                    "details": "UNTRUSTED_CANARY_VALUE"}
        result = mod.inspect(ENV, reader=reader)
        self.assertNotIn("UNTRUSTED_CANARY_VALUE", json.dumps(result))
        self.assertTrue(all(item["status"] == "UNRECOGNIZED" for item in result["checks"]))

    def test_malformed_status_list_is_sanitized_and_fail_closed(self):
        def reader(args):
            if args[0] == "account":
                return dict(ACCOUNT)
            return {"status": ["RAW_CANARY_DO_NOT_COPY"], "source_ok": True,
                    "target_ok": True, "active_version_present": True}
        result = mod.inspect(ENV, reader=reader)
        self.assertEqual(result["overall"], "REVIEW_REQUIRED_KEYVAULT_REFERENCE_METADATA")
        self.assertNotIn("RAW_CANARY", json.dumps(result))

    def test_projection_does_not_return_sensitive_metadata(self):
        for key in mod.TARGETS:
            projection = mod.metadata_projection(key)
            self.assertNotIn("reference:", projection)
            self.assertNotIn("activeVersion:", projection)
            self.assertNotIn("details:", projection)
            self.assertNotIn("secretVersion:", projection)
            self.assertIn("source_ok:", projection)
            self.assertIn("target_ok:", projection)
            self.assertIn("active_version_present:", projection)

    def test_workflow_is_opt_in_inside_existing_canonical_inventory(self):
        data = WF.read_text(encoding="utf-8")
        self.assertIn("crown269-reference-metadata-only", data)
        self.assertIn("for #269 READ-ONLY", data)
        self.assertIn('default: ""', data)
        self.assertIn("two-fixed-reference-gets:", data)
        self.assertIn("environment: dev", data)
        self.assertIn("id-token: write", data)
        self.assertIn("github.ref == 'refs/heads/main'", data)
        self.assertIn("github.repository == 'Arete0920/Crown-CSMS'", data)
        self.assertIn("GITHUB_REPOSITORY_ID\" = 1339719218", data)
        self.assertIn("secrets.AZURE_CLIENT_ID", data)
        self.assertIn("secrets.AZURE_TENANT_ID", data)
        self.assertIn("secrets.AZURE_SUBSCRIPTION_ID", data)
        self.assertIn("uses: azure/login@a457da9ea143d694b1b9c7c869ebb04ebe844ef5", data)
        self.assertIn("retention-days: 30", data)
        self.assertIn("--receipt", data)
        # Existing workflow's push/PR triggers MUST be retained, not removed.
        self.assertIn("  pull_request:", data)
        self.assertIn("  push:", data)
        self.assertEqual(data.count("  workflow_dispatch:"), 1)
        self.assertEqual(data.count("  two-fixed-reference-gets:"), 1)

    def test_new_job_isolated_from_existing_inspect_and_migrations(self):
        import yaml
        data = yaml.load(WF.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        jobs = data["jobs"]
        self.assertEqual(set(jobs), {
            "support-contract-tests", "inspect", "stage-reviewed-dev-migrations",
            "two-fixed-reference-gets",
        })
        check = jobs["two-fixed-reference-gets"]
        clause = check["if"]
        self.assertIn("github.event_name == 'workflow_dispatch'", clause)
        self.assertIn("github.ref == 'refs/heads/main'", clause)
        self.assertIn("inputs.confirm_dev_support == 'crown269-reference-metadata-only'", clause)
        self.assertIn("inputs.confirm_dev_support != 'crown269-reference-metadata-only'", jobs["inspect"]["if"])
        self.assertIn("inputs.confirm_dev_support != 'crown269-reference-metadata-only'", jobs["stage-reviewed-dev-migrations"]["if"])
        self.assertEqual(check["environment"], "dev")
        self.assertEqual(check["permissions"]["id-token"], "write")
        script = "\n".join(step.get("run", "") for step in check["steps"])
        for token in (
            'test "$GITHUB_REPOSITORY_ID" = 1339719218',
            'test "$REQUESTED_SHA" = "$GITHUB_SHA"',
            'test "$APPLY_SUPPORT" = false',
            'test "$APPLY_LEGACY_REFRESH" = false',
            'test "$APPLY_BLACKLIST" = false',
            'test "$COMPARE_BASELINE" = false',
            'test "$INSPECT_MIGRATIONS" = false',
            'test "$CONFIRM_SUPPORT" = crown269-reference-metadata-only',
            'test -z "$CONFIRM_LEGACY"',
            'test -z "$CONFIRM_BLACKLIST"',
            'test -z "$DEV_RECOVERY_RECEIPT"',
            'test "$(git rev-parse origin/main)" = "$REQUESTED_SHA"',
        ):
            self.assertIn(token, script)
        for forbidden in ("az webapp", "az keyvault", "curl -X POST",
                          "appsettings set", "migrate ", "--apply", "git push"):
            self.assertNotIn(forbidden, script)

    def test_workflow_yaml_parses_and_flag_is_default_off(self):
        import yaml
        data = yaml.load(WF.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        inputs = data["on"]["workflow_dispatch"]["inputs"]
        self.assertEqual(len(inputs), 10)
        self.assertEqual(inputs["confirm_dev_support"]["type"], "string")
        self.assertEqual(inputs["confirm_dev_support"]["default"], "")
        self.assertIn("crown269-reference-metadata-only", inputs["confirm_dev_support"]["description"])
        self.assertEqual(data["jobs"]["two-fixed-reference-gets"]["permissions"]["id-token"], "write")

    def test_cli_failure_does_not_echo_output(self):
        with patch.object(mod.subprocess, "run") as runner:
            runner.return_value.returncode = 1
            runner.return_value.stdout = "RAW_UNSAFE_CANARY"
            runner.return_value.stderr = "RAW_UNSAFE_CANARY"
            self.assertIsNone(mod.read_az(["account", "show"]))
        self.assertNotIn("RAW_UNSAFE_CANARY", json.dumps(mod.inspect({},reader=lambda args: None)))


    def test_cli_accepts_exact_private_runner_receipt_once(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {"RUNNER_TEMP": directory}), \
             patch.object(mod, "inspect", return_value={
                 "overall": "PASS_TWO_REFERENCE_METADATA_ONLY_OTHER_269_ITEMS_OPEN",
                 "checks": [],
             }) as inspect:
            path = Path(directory) / "crown269-dev-reference-metadata.json"
            self.assertEqual(mod.main(["--receipt", str(path)]), 0)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["checks"], [])
            if os.name == "posix":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            # Existing evidence is never overwritten or inspected again.
            self.assertEqual(mod.main(["--receipt", str(path)]), 3)
            self.assertEqual(inspect.call_count, 1)

    def test_cli_rejects_escaped_and_noncanonical_receipts_before_azure(self):
        with tempfile.TemporaryDirectory() as directory, \
             tempfile.TemporaryDirectory() as outside, \
             patch.dict(os.environ, {"RUNNER_TEMP": directory}), \
             patch.object(mod, "inspect", side_effect=AssertionError("AZURE_CALLED")):
            candidates = (
                "relative.json",
                str(Path(directory) / "wrong.json"),
                str(Path(directory) / "nested" / "crown269-dev-reference-metadata.json"),
                str(Path(outside) / "crown269-dev-reference-metadata.json"),
            )
            for candidate in candidates:
                with self.subTest(candidate=candidate):
                    self.assertEqual(mod.main(["--receipt", candidate]), 3)
            with patch.dict(os.environ, {"RUNNER_TEMP": ""}):
                target = Path(directory) / "crown269-dev-reference-metadata.json"
                self.assertEqual(mod.main(["--receipt", str(target)]), 3)

    def test_cli_rejects_symlinks_and_unsafe_existing_targets(self):
        with tempfile.TemporaryDirectory() as directory, \
             tempfile.TemporaryDirectory() as outside, \
             patch.dict(os.environ, {"RUNNER_TEMP": directory}), \
             patch.object(mod, "inspect", side_effect=AssertionError("AZURE_CALLED")):
            target = Path(directory) / "crown269-dev-reference-metadata.json"
            other = Path(outside) / "canary.json"
            other.write_text("KEEP", encoding="utf-8")
            try:
                target.symlink_to(other)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            self.assertEqual(mod.main(["--receipt", str(target)]), 3)
            self.assertEqual(other.read_text(encoding="utf-8"), "KEEP")
            target.unlink()
            target.mkdir()
            self.assertEqual(mod.main(["--receipt", str(target)]), 3)


if __name__ == "__main__":
    unittest.main()
