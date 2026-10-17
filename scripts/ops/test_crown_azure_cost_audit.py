"""Tests for CROWN Azure cost collector; no live cloud calls."""
import json
from pathlib import Path
from unittest.mock import patch
import unittest
import crown_azure_cost_audit as audit

class AuditTests(unittest.TestCase):

    def test_rest_json_and_http_reason_errors_have_safe_labels(self):
        samples = (
            ('ERROR: Forbidden({"error":{"code":"AuthorizationFailed","message":"PRIVATE"}})', "ACCESS_DENIED"),
            ('ERROR: Bad Request({"error":{"code":"InvalidApiVersionParameter","message":"PRIVATE"}})', "INVALID_REQUEST"),
            ('ERROR: Too Many Requests({"error":{"code":"UnknownCode"}})', "RATE_LIMIT"),
            ('ERROR: Unknown({"error":{"code":"PrivateCode","message":"PRIVATE"}})', "UNKNOWN"),
        )
        for sample, expected in samples:
            with self.subTest(sample=sample):
                self.assertEqual(audit.error_category(sample), expected)

    def test_arbitrary_message_mentions_are_not_http_failures(self):
        self.assertEqual(audit.error_category('PRIVATE user said Forbidden yesterday'), "UNKNOWN")

    def test_group_probe_does_not_replace_unknown_subscription_total(self):
        calls = []
        def fake(*cmd, timeout=60):
            calls.append(cmd)
            if cmd[:2] == ("account", "show"):
                return {"id": "sub-test", "state": "Enabled"}
            if cmd[0] != "rest":
                return []
            url = cmd[cmd.index("--url") + 1]
            if "/resourceGroups/" not in url:
                raise audit.ReadUnavailable("withheld", "ACCESS_DENIED")
            if "budgets?" in url:
                return {"value": []}
            return {"properties": {"columns": [{"name": "PreTaxCost"}], "rows": [[12]]}}
        with patch.object(audit, "az_json", side_effect=fake):
            result = audit.make_report("group with space")
        self.assertEqual(result["actual_cost"]["month_to_date"]["status"], "UNAVAILABLE")
        self.assertEqual(result["resource_group_cost"]["month_to_date"]["status"], "COLLECTED")
        self.assertIsNone(result["existing_budgets"])
        self.assertEqual(result["resource_group_budgets"], [])
        self.assertTrue(any("group%20with%20space" in part for cmd in calls for part in cmd))
        diagnostics = audit.redacted_diagnostics(result)
        self.assertEqual(diagnostics["resource_group_probe"]["month_to_date"], "COLLECTED")
        self.assertNotIn("amount", json.dumps(diagnostics))
        self.assertNotIn("sub-test", json.dumps(diagnostics))

    def test_group_diagnostics_reject_private_statuses_and_messages(self):
        result = audit.redacted_diagnostics({
            "resource_group_cost": {"month_to_date": {"status": "PRIVATE"}},
            "resource_group_budgets": [{"name": "PRIVATE", "amount": 50}],
            "failures": [{"section": "group_budgets", "category": "ACCESS_DENIED", "reason": "PRIVATE"}],
        })
        self.assertEqual(result["resource_group_probe"]["month_to_date"], "UNAVAILABLE")
        self.assertEqual(result["resource_group_budget_status"], "COLLECTED")
        self.assertNotIn("PRIVATE", json.dumps(result))

    def test_provider_errors_are_classified_without_retaining_stderr(self):
        for code, expected in (("AuthorizationFailed", "ACCESS_DENIED"),
                               ("TooManyRequests", "RATE_LIMIT"),
                               ("InvalidApiVersionParameter", "INVALID_REQUEST"),
                               ("SomePrivateProviderCode", "UNKNOWN")):
            with self.subTest(code=code), patch.object(audit.subprocess, "run") as run:
                run.return_value.returncode = 1
                run.return_value.stderr = f"ERROR: ({code}) PRIVATE account secret"
                failures = []
                self.assertIsNone(audit.safe_read("cost_MonthToDate", "rest", failures=failures))
                self.assertEqual(failures[0]["category"], expected)
                self.assertNotIn("PRIVATE", json.dumps(failures))

    def test_redacted_diagnostics_cannot_copy_arbitrary_fields(self):
        report = {"subscription": "PRIVATE", "actual_cost": {"amount": 12},
                  "failures": [{"section": "cost_MonthToDate", "category": "ACCESS_DENIED",
                                "reason": "PRIVATE", "amount": 123},
                               {"section": "budgets", "category": "PRIVATE"},
                               {"section": "PRIVATE", "category": "UNKNOWN"}]}
        output = audit.redacted_diagnostics(report)
        self.assertEqual(output["failures"][0]["category"], "ACCESS_DENIED")
        self.assertEqual(output["failures"][1]["category"], "UNKNOWN")
        self.assertNotIn("PRIVATE", json.dumps(output))
        self.assertNotIn("amount", json.dumps(output))

    def test_timeout_and_invalid_json_have_distinct_categories(self):
        with patch.object(audit.subprocess, "run", side_effect=audit.subprocess.TimeoutExpired("az PRIVATE", 60)):
            with self.assertRaises(audit.ReadUnavailable) as caught:
                audit.az_json("account", "show")
            self.assertEqual(caught.exception.category, "TIMEOUT")
            self.assertNotIn("PRIVATE", str(caught.exception))
        with patch.object(audit.subprocess, "run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "PRIVATE invalid JSON"
            with self.assertRaises(audit.ReadUnavailable) as caught:
                audit.az_json("account", "show")
            self.assertEqual(caught.exception.category, "INVALID_RESPONSE")

    def test_authenticated_azure_inventory_is_manual_only(self):
        workflow = (
            Path(__file__).resolve().parents[2]
            / ".github" / "workflows" / "azure-classroom-preflight.yml"
        ).read_text(encoding="utf-8")
        inventory = workflow.split("\n  azure-inventory:\n", 1)[1]
        guard = "if: github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'"
        self.assertIn(guard, inventory)
        self.assertNotIn("github.event_name == 'push'", inventory.split("\n    steps:", 1)[0])
        self.assertIn("if: always()\n        shell: bash\n        run: rm -f azure-classroom-preflight.json private-azure-cost.json", inventory)
        self.assertIn("  collector-tests:\n", workflow)
        self.assertIn("  push:\n", workflow)
        self.assertIn("  pull_request:\n", workflow)

    def test_no_subscription_is_blocked(self):
        with patch.object(audit, "az_json", side_effect=audit.ReadUnavailable("no access")):
            report = audit.make_report("crown-rg")
        self.assertEqual(report["status"], "BLOCKED")
        self.assertNotIn("actual_cost", report)

    def test_no_azure_mutation_in_account_probe(self):
        with patch.object(audit.subprocess, "run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "{}"
            audit.az_json("account", "show")
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[:3], ["az", "account", "show"])
        self.assertIn("--only-show-errors", cmd)
        self.assertEqual(run.call_args.kwargs["env"]["AZURE_EXTENSION_USE_DYNAMIC_INSTALL"], "no")

    def test_missing_billing_is_unknown_not_zero(self):
        with patch.object(audit, "az_json", return_value={"properties": {}}):
            failures = []
            result = audit.billing("/subscriptions/example", "MonthToDate", failures)
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertTrue(failures)

    def test_whitelist_excludes_unrelated_billing_data(self):
        result = {"properties": {
            "columns": [{"name": n} for n in ["PreTaxCost", "ResourceGroup", "Currency", "Secret"]],
            "rows": [[2.4, "crown-rg", "USD", "PRIVATE"]]
        }}
        with patch.object(audit, "az_json", return_value=result):
            output = audit.billing("/subscriptions/example", "MonthToDate", [])
        self.assertEqual(output["rows"][0]["amount"], 2.4)
        self.assertNotIn("PRIVATE", json.dumps(output))

    def test_unavailable_cost_and_budget_preserved(self):
        def fake(*cmd, timeout=60):
            if cmd[:2] == ("account", "show"):
                return {"id": "sub-test", "name": "PAYG", "state": "Enabled"}
            if cmd[0] == "rest":
                raise audit.ReadUnavailable("unavailable")
            return []
        with patch.object(audit, "az_json", side_effect=fake):
            report = audit.make_report("crown-rg")
        self.assertEqual(report["status"], "COLLECTED_WITH_GAPS")
        self.assertEqual(report["actual_cost"]["month_to_date"]["status"], "UNAVAILABLE")
        self.assertIsNone(report["existing_budgets"])

    def test_paginated_cost_is_not_misreported_as_complete(self):
        payload = {"properties": {
            "columns": [{"name": "PreTaxCost"}, {"name": "ResourceGroup"}],
            "rows": [[12.5, "crown-rg"]],
            "nextLink": "https://management.azure.com/PRIVATE-next-page",
        }}
        failures = []
        with patch.object(audit, "az_json", return_value=payload):
            result = audit.billing("/subscriptions/example", "MonthToDate", failures)
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertTrue(result["has_more_pages"])
        self.assertEqual(result["rows"][0]["amount"], 12.5)
        self.assertEqual(failures[0]["category"], "INVALID_RESPONSE")
        self.assertNotIn("PRIVATE-next-page", json.dumps(result) + json.dumps(failures))

    def test_unpaginated_cost_remains_collected(self):
        payload = {"properties": {
            "columns": [{"name": "PreTaxCost"}],
            "rows": [[12.5]],
        }}
        failures = []
        with patch.object(audit, "az_json", return_value=payload):
            result = audit.billing("/subscriptions/example", "MonthToDate", failures)
        self.assertEqual(result["status"], "COLLECTED")
        self.assertFalse(result["has_more_pages"])
        self.assertEqual(failures, [])

    def test_empty_cost_rows_are_not_claimed_free(self):
        with patch.object(audit, "az_json", return_value={
            "properties": {"columns": [{"name": "PreTaxCost"}], "rows": []}
        }):
            report = audit.billing("/subscriptions/example", "MonthToDate", [])
        self.assertEqual(report["status"], "COLLECTED_NO_ROWS")
        self.assertIn("not proof of $0", report["note"])

if __name__ == "__main__":
    unittest.main()

