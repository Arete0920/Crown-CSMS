"""Offline regression tests for the read-only, exact-PR-head GitHub check audit."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/admin/setup_branch_protection.sh"
SHA = "a" * 40
MAIN = "b" * 40
PR = 334


class BranchProtectionAuditContract(unittest.TestCase):
    def run_audit(self, *, contexts=None, check_runs=None, protection_failure=False,
                  moving_head=False, moving_main=False, behind_main=False,
                  total_count=None, args=None):
        contexts = ([{"context": "test", "app_id": 15368}] if contexts is None else contexts)
        check_runs = ([{"name": "test", "app": {"id": 15368},
                       "status": "completed", "conclusion": "success"}]
                      if check_runs is None else check_runs)
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            before_branch, after_branch, before_pr, after_pr, observed, calls = (
                directory / name for name in ("before-branch.json", "after-branch.json", "before-pr.json",
                                              "after-pr.json", "observed.json", "calls.log")
            )
            def branch(sha):
                return {"name": "main", "protected": True, "commit": {"sha": sha},
                        "protection": {"required_status_checks": {"checks": contexts, "strict": True}}}
            def pull(head, base):
                return {"number": PR, "state": "open", "head": {"sha": head},
                        "base": {"ref": "main", "sha": base}}
            before_branch.write_text(json.dumps(branch(MAIN)))
            after_branch.write_text(json.dumps(branch("c" * 40 if moving_main else MAIN)))
            before_pr.write_text(json.dumps(pull(SHA, "d" * 40 if behind_main else MAIN)))
            after_pr.write_text(json.dumps(pull("e" * 40 if moving_head else SHA,
                                                "d" * 40 if behind_main else MAIN)))
            observed.write_text(json.dumps({"total_count": len(check_runs) if total_count is None else total_count,
                                            "check_runs": check_runs}))
            gh = directory / "gh"
            gh.write_text('''#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "$GH_CALLS"
if [[ "$*" == *"/branches/main" ]]; then
  if [[ "${GH_PROTECTION_ERROR:-0}" == "1" ]]; then exit 1; fi
  count="$(grep -c /branches/main "$GH_CALLS" || true)"
  if [[ "$count" == "1" ]]; then cat "$GH_BEFORE_BRANCH"; else cat "$GH_AFTER_BRANCH"; fi
elif [[ "$*" == *"/pulls/334" ]]; then
  count="$(grep -c /pulls/334 "$GH_CALLS" || true)"
  if [[ "$count" == "1" ]]; then cat "$GH_BEFORE_PR"; else cat "$GH_AFTER_PR"; fi
elif [[ "$*" == *"/check-runs?per_page=100"* ]]; then
  cat "$GH_OBSERVED"
else
  exit 30
fi
''')
            gh.chmod(0o755)
            env = os.environ.copy()
            env.update(PATH=f"{directory}:{env.get('PATH', '')}", GH_BEFORE_BRANCH=str(before_branch),
                       GH_AFTER_BRANCH=str(after_branch), GH_BEFORE_PR=str(before_pr), GH_AFTER_PR=str(after_pr),
                       GH_OBSERVED=str(observed), GH_CALLS=str(calls),
                       GH_PROTECTION_ERROR="1" if protection_failure else "0")
            result = subprocess.run(["bash", str(SCRIPT), *(args if args is not None else ["--audit-pr", str(PR)])],
                                    text=True, capture_output=True, env=env, check=False)
            return result, calls.read_text() if calls.exists() else ""

    def test_exact_pr_head_success_never_writes(self):
        result, calls = self.run_audit()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("REQUIRED_CHECKS_PRESENT", result.stdout)
        self.assertEqual(len(calls.splitlines()), 5)
        self.assertTrue(all("--method GET" in line for line in calls.splitlines()))

    def test_missing_context_fails(self):
        result, _ = self.run_audit(check_runs=[])
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSING", result.stdout)

    def test_wrong_check_app_fails(self):
        result, _ = self.run_audit(check_runs=[{"name": "test", "app": {"id": 999},
                                                "status": "completed", "conclusion": "success"}])
        self.assertEqual(result.returncode, 1)
        self.assertIn("WRONG_APP", result.stdout)

    def test_duplicate_check_fails(self):
        result, _ = self.run_audit(check_runs=[
            {"name": "test", "app": {"id": 15368}, "status": "completed", "conclusion": "success"},
            {"name": "test", "app": {"id": 15368}, "status": "completed", "conclusion": "failure"},
        ])
        self.assertEqual(result.returncode, 1)
        self.assertIn("AMBIGUOUS_DUPLICATE", result.stdout)

    def test_running_check_fails(self):
        result, _ = self.run_audit(check_runs=[{"name": "test", "app": {"id": 15368},
                                                "status": "in_progress", "conclusion": None}])
        self.assertEqual(result.returncode, 1)
        self.assertIn("NOT_SUCCESS", result.stdout)

    def test_unsupported_apply_without_call(self):
        result, calls = self.run_audit(args=["--apply"])
        self.assertEqual(result.returncode, 3)
        self.assertEqual(calls, "")

    def test_unbound_sha_argument_denied(self):
        result, calls = self.run_audit(args=["--audit", SHA])
        self.assertEqual(result.returncode, 2)
        self.assertEqual(calls, "")

    def test_missing_protection_access_denied(self):
        result, calls = self.run_audit(protection_failure=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(len(calls.splitlines()), 1)

    def test_head_moves_during_audit_fails_closed(self):
        result, _ = self.run_audit(moving_head=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("PR head/base changed", result.stderr)

    def test_main_moves_during_audit_fails_closed(self):
        result, _ = self.run_audit(moving_main=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("main moved", result.stderr)

    def test_behind_main_fails_closed(self):
        result, _ = self.run_audit(behind_main=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("PR head/base changed", result.stderr)

    def test_incomplete_check_page_fails_closed(self):
        result, _ = self.run_audit(total_count=110)
        self.assertEqual(result.returncode, 2)
        self.assertIn("incomplete", result.stderr)


if __name__ == "__main__":
    unittest.main()
