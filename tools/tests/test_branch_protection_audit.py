"""Offline regression coverage for read-only branch protection auditing."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/admin/setup_branch_protection.sh"
SHA = "a" * 40


class BranchProtectionAuditContract(unittest.TestCase):
    def run_audit(self, *, contexts=None, check_runs=None, status=0, args=None):
        if contexts is None:
            contexts = [{"context": "test", "app_id": 15368}]
        if check_runs is None:
            check_runs = [{"name": "test", "app": {"id": 15368},
                           "status": "completed", "conclusion": "success"}]
        with tempfile.TemporaryDirectory() as tmp:
            bin_dir = Path(tmp)
            required, observed, calls = (bin_dir / n for n in ("required.json", "observed.json", "calls.log"))
            required.write_text(json.dumps({"name": "main", "protected": True,
                                            "protection": {"required_status_checks":
                                                           {"checks": contexts, "strict": True}}}))
            observed.write_text(json.dumps({"total_count": len(check_runs), "check_runs": check_runs}))
            gh = bin_dir / "gh"
            gh.write_text('''#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "$GH_CALLS"
if [[ "$*" == *"/branches/main" ]]; then
  if [[ "${GH_PROTECTION_ERROR:-0}" == "1" ]]; then exit 1; fi
  cat "$GH_REQUIRED"
elif [[ "$*" == *"/check-runs?per_page=100"* ]]; then
  cat "$GH_OBSERVED"
else
  exit 30
fi
''')
            gh.chmod(0o755)
            env = os.environ.copy()
            env.update(PATH=f"{bin_dir}:{env.get('PATH', '')}", GH_REQUIRED=str(required),
                       GH_OBSERVED=str(observed), GH_CALLS=str(calls),
                       GH_PROTECTION_ERROR=str(status))
            result = subprocess.run(["bash", str(SCRIPT), *(args if args is not None else ["--audit", SHA])],
                                    text=True, capture_output=True, env=env, check=False)
            invoked = calls.read_text() if calls.exists() else ""
            return result, invoked

    def test_good_exact_head_has_no_write_requests(self):
        result, calls = self.run_audit()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("REQUIRED_CHECKS_PRESENT", result.stdout)
        self.assertNotIn(" PUT ", calls)
        self.assertIn("--method GET", calls)

    def test_missing_context_fails_closed(self):
        result, _ = self.run_audit(check_runs=[])
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSING", result.stdout)

    def test_mismatched_check_app_is_not_accepted(self):
        result, _ = self.run_audit(check_runs=[{"name": "test", "app": {"id": 999},
                                                  "status": "completed", "conclusion": "success"}])
        self.assertEqual(result.returncode, 1)
        self.assertIn("WRONG_APP", result.stdout)

    def test_duplicate_success_and_failure_never_pass(self):
        result, _ = self.run_audit(check_runs=[
            {"name": "test", "app": {"id": 15368}, "status": "completed", "conclusion": "success"},
            {"name": "test", "app": {"id": 15368}, "status": "completed", "conclusion": "failure"},
        ])
        self.assertEqual(result.returncode, 1)
        self.assertIn("AMBIGUOUS_DUPLICATE", result.stdout)

    def test_incomplete_check_remains_blocked(self):
        result, _ = self.run_audit(check_runs=[{"name": "test", "app": {"id": 15368},
                                                  "status": "in_progress", "conclusion": None}])
        self.assertEqual(result.returncode, 1)
        self.assertIn("NOT_SUCCESS", result.stdout)

    def test_admin_read_failure_never_guesses_policy(self):
        result, calls = self.run_audit(status=1)
        self.assertEqual(result.returncode, 2)
        self.assertIn("REFUSED", result.stderr)
        self.assertEqual(len(calls.splitlines()), 1)

    def test_apply_is_disabled_without_contacting_github(self):
        result, calls = self.run_audit(args=["--apply"])
        self.assertEqual(result.returncode, 3)
        self.assertIn("REFUSED", result.stderr)
        self.assertEqual(calls, "")

    def test_invalid_sha_does_not_contact_github(self):
        result, calls = self.run_audit(args=["--audit", "main"])
        self.assertEqual(result.returncode, 2)
        self.assertEqual(calls, "")


if __name__ == "__main__":
    unittest.main()
