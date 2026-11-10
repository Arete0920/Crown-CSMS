"""Offline tests for read-only DEV baseline diagnostic boundary."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/ops/inspect_dev_baseline_components.py"
WORKFLOW = ROOT / ".github/workflows/dev-baseline-components-readonly.yml"

class BaselineDiagnosticContracts(unittest.TestCase):
    def test_diagnostic_parses(self):
        ast.parse(SCRIPT.read_text(encoding="utf-8"))

    def test_read_only_transaction_and_tls(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for required in ("SET TRANSACTION READ ONLY", "verify-full",
                         "SHOW transaction_read_only", "protected_main_moved",
                         "live_schema_write_performed", "component_fingerprint"):
            self.assertIn(required, source)
        self.assertNotIn("executor.migrate(", source)
        self.assertNotIn("cursor.execute('INSERT", source)

    def test_workflow_manual_only_and_current_main(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        for required in ("workflow_dispatch:", "environment: dev", "origin/main",
                         "inputs.expected_sha", "inspect_dev_baseline_components.py"):
            self.assertIn(required, source)
        self.assertNotIn("push:", source)
        self.assertNotIn("pull_request:", source)

if __name__ == "__main__":
    unittest.main()
