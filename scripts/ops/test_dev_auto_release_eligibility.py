"""Offline negative proofs for future DEV auto-promotion eligibility. No network."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).with_name("dev_auto_release_eligibility.py")
spec = importlib.util.spec_from_file_location("dev_auto_release_eligibility", MODULE)
eligibility = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eligibility)
SHA = "a" * 40


def trusted_evidence():
    names = sorted(eligibility.BASELINE)
    branch = {
        "protected": True,
        "commit": {"sha": SHA},
        "protection": {
            "required_status_checks": {
                "enforcement_level": "everyone",
                "contexts": names,
                "checks": [{"context": name, "app_id": eligibility.GITHUB_ACTIONS_APP_ID}
                           for name in names],
            },
        },
    }
    checks = {
        "total_count": len(names),
        "check_runs": [
            {"name": name, "id": 1000 + i, "head_sha": SHA,
             "status": "completed", "conclusion": "success",
             "app": {"id": eligibility.GITHUB_ACTIONS_APP_ID}}
            for i, name in enumerate(names)
        ],
    }
    policy = {
        "schema_version": 1, "enabled": True, "target": "dev",
        "automatic_schema_changes": False,
    }
    return dict(
        expected_sha=SHA, event_name="push", ref="refs/heads/main",
        repository=eligibility.REPO, source_policy=policy,
        repository_opt_in=True, branch_data=branch, check_data=checks,
    )


class DevAutoReleaseEligibilityTests(unittest.TestCase):
    def test_repository_checkout_policy_is_disabled_by_default(self):
        policy = json.loads(eligibility.POLICY.read_text(encoding="utf-8"))
        self.assertIs(policy["enabled"], False)
        self.assertEqual(policy["target"], "dev")
        self.assertIs(policy["automatic_schema_changes"], False)

    def test_positive_hypothetical_eligibility_requires_all_trusted_checks(self):
        result = eligibility.assess(**trusted_evidence())
        self.assertEqual(result["status"], "ELIGIBLE", result)
        self.assertEqual(result["required_checks"], 17)

    def test_fail_closed_cases(self):
        cases = {
            "source-disabled": lambda a: a["source_policy"].update(enabled=False),
            "repository-disabled": lambda a: a.update(repository_opt_in=False),
            "foreign-repository": lambda a: a.update(repository="other/repo"),
            "pull-request": lambda a: a.update(event_name="pull_request"),
            "manual-dispatch": lambda a: a.update(event_name="workflow_dispatch"),
            "foreign-ref": lambda a: a.update(ref="refs/heads/feature"),
            "short-sha": lambda a: a.update(expected_sha="abc"),
            "main-moved": lambda a: a["branch_data"]["commit"].update(sha="b" * 40),
            "unprotected-main": lambda a: a["branch_data"].update(protected=False),
            "no-protection": lambda a: a["branch_data"].pop("protection"),
            "weak-enforcement": lambda a: a["branch_data"]["protection"]["required_status_checks"].update(enforcement_level="non_admins"),
            "removed-baseline": lambda a: a["branch_data"]["protection"]["required_status_checks"]["contexts"].pop(),
            "missing-check": lambda a: (a["check_data"]["check_runs"].pop(), a["check_data"].update(total_count=16)),
            "queued-required": lambda a: a["check_data"]["check_runs"][0].update(status="queued", conclusion=None),
            "failed-required": lambda a: a["check_data"]["check_runs"][0].update(conclusion="failure"),
            "skipped-required": lambda a: a["check_data"]["check_runs"][0].update(conclusion="skipped"),
            "foreign-check-source": lambda a: a["check_data"]["check_runs"][0].update(head_sha="b" * 40),
            "untrusted-check-app": lambda a: a["check_data"]["check_runs"][0]["app"].update(id=123),
            "wrong-protection-app": lambda a: a["branch_data"]["protection"]["required_status_checks"]["checks"][0].update(app_id=123),
            "incomplete-pagination": lambda a: a["check_data"].update(total_count=101),
            "truncated-response": lambda a: a["check_data"].update(total_count=20),
            "unexpected-policy-key": lambda a: a["source_policy"].update(skip_checks=True),
            "auto-schema-enabled": lambda a: a["source_policy"].update(automatic_schema_changes=True),
            "wrong-target": lambda a: a["source_policy"].update(target="production"),
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                argument = trusted_evidence()
                change(argument)
                result = eligibility.assess(**argument)
                self.assertEqual(result["status"], "BLOCKED", result)

    def test_latest_check_run_wins_even_if_old_run_succeeded(self):
        arguments = trusted_evidence()
        previous = copy.deepcopy(arguments["check_data"]["check_runs"][0])
        latest = copy.deepcopy(previous)
        latest["id"] = previous["id"] + 10000
        latest["status"] = "in_progress"
        latest["conclusion"] = None
        arguments["check_data"]["check_runs"].append(latest)
        arguments["check_data"]["total_count"] += 1
        self.assertEqual(eligibility.assess(**arguments)["status"], "BLOCKED")

    def test_existing_freshness_workflow_is_read_only_and_opted_out(self):
        workflow = (MODULE.parents[2] / ".github" / "workflows" /
                    "repository-freshness.yml").read_text(encoding="utf-8")
        self.assertEqual(workflow.count("  dev-auto-delivery-eligibility:"), 1)
        candidate = workflow.split("  dev-auto-delivery-eligibility:", 1)[1].split(
            "  report-stale-branches:", 1,
        )[0]
        self.assertIn("vars.CROWN_AUTO_DEV_CD_ENABLED == 'true'", candidate)
        self.assertIn("github.event_name == 'push'", candidate)
        self.assertIn("github.event.schedule == '17 6 * * *'", candidate)
        self.assertIn("      checks: read", candidate)
        self.assertIn("      contents: read", candidate)
        self.assertIn("persist-credentials: false", candidate)
        self.assertIn("dev_auto_release_eligibility.py --expected-sha", candidate)
        for forbidden in ("id-token: write", "azure/login@", "az webapp",
                          "az acr", "workflow_dispatch:", "curl -X POST",
                          "secrets.", "create-deployment", "git push"):
            self.assertNotIn(forbidden, candidate, forbidden)
        self.assertIs(json.loads(eligibility.POLICY.read_text())["enabled"], False)

    def test_main_does_not_contact_github_when_source_policy_is_off(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.json"
            path.write_text(json.dumps({
                "schema_version": 1, "enabled": False, "target": "dev",
                "automatic_schema_changes": False,
            }), encoding="utf-8")
            with patch.object(eligibility, "POLICY", path), \
                 patch.object(eligibility, "github_json", side_effect=AssertionError("network used")):
                from contextlib import redirect_stdout
                from io import StringIO
                buffer = StringIO()
                with patch.dict("os.environ", {
                    "GITHUB_TOKEN": "synthetic", "GITHUB_REPOSITORY": eligibility.REPO,
                    "CROWN_AUTO_DEV_CD_ENABLED": "true",
                }), redirect_stdout(buffer):
                    code = eligibility.main(["--expected-sha", SHA])
                self.assertEqual(code, 2)
                self.assertEqual(json.loads(buffer.getvalue())["reason"],
                                 "auto_delivery_not_authorized")


if __name__ == "__main__":
    unittest.main()
