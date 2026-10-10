"""Tests for CROWN Azure cost collector; no live cloud calls."""
import json
from pathlib import Path
from unittest.mock import patch
import unittest
import crown_azure_cost_audit as audit

class AuditTests(unittest.TestCase):

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

    def test_empty_cost_rows_are_not_claimed_free(self):
        with patch.object(audit, "az_json", return_value={
            "properties": {"columns": [{"name": "PreTaxCost"}], "rows": []}
        }):
            report = audit.billing("/subscriptions/example", "MonthToDate", [])
        self.assertEqual(report["status"], "COLLECTED_NO_ROWS")
        self.assertIn("not proof of $0", report["note"])

if __name__ == "__main__":
    unittest.main()
