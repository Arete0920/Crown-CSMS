"""Offline proof of fail-closed DEV code-only automation. No cloud calls."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import dev_auto_release_controller as controller

SHA = "a" * 40
B = controller.BACKEND
F = controller.FRONTEND


def observed(backend="MISMATCH", frontend="MISMATCH", safe=True):
    checks = {
        "backend_build_sha": backend, "backend_artifact_sha": backend,
        "dev_preview_build_sha": frontend,
        "backend_environment": "DEV" if safe else "NOT_VERIFIED",
        "backend_database": "READY", "anonymous_overview": "DENIED",
        "anonymous_school_directory": "DENIED", "dev_preview_cors": "READY",
    }
    return {"expected_main_sha": SHA, "api_health_http_status": 200,
            "checks": checks,
            "precheck": "PASS" if backend == frontend == "MATCH" and safe else "BLOCKED"}


class FakeGithub:
    def __init__(self, prior=None, active=False, fail=None):
        self.prior, self.active, self.fail = prior or {}, active, fail
        self.calls, self.dispatched, self.run_by_id = [], [], {}

    def api(self, method, path, data=None):
        self.calls.append((method, path, copy.deepcopy(data)))
        if method == "GET" and "/runs?" in path:
            wf = B if B in path else F
            if "&head_sha=" in path:
                items = self.prior.get(wf, [])
                return {"total_count": len(items), "workflow_runs": items}
            if "status=in_progress" in path and self.active:
                return {"total_count": 1, "workflow_runs": [{}]}
            return {"total_count": 0, "workflow_runs": []}
        if method == "POST":
            wf = B if B in path else F
            if self.fail == "dispatch":
                return {"workflow_run_id": 0}
            ident = len(self.dispatched) + 10
            self.dispatched.append((wf, data))
            self.run_by_id[ident] = {
                "id": ident, "path": ".github/workflows/" + wf,
                "head_sha": SHA, "head_branch": "main",
                "event": "workflow_dispatch", "run_attempt": 1,
                "repository": {"full_name": controller.REPO},
                "status": "completed", "conclusion": "success",
            }
            return {"workflow_run_id": ident,
                    "run_url": controller.ROOT + "/actions/runs/" + str(ident),
                    "html_url": "https://github.com/" + controller.REPO
                    + "/actions/runs/" + str(ident)}
        if method == "GET" and path.startswith("/actions/runs/"):
            return self.run_by_id[int(path.rsplit("/", 1)[1])]
        raise AssertionError((method, path, data))


def eligible(_):
    return True


class ReleaseControllerContracts(unittest.TestCase):
    def test_policy_disabled_unconditionally(self):
        assert json.loads(controller.eligibility.POLICY.read_text())["enabled"] is False
        env = {"GITHUB_REPOSITORY": controller.REPO, "GITHUB_REF": "refs/heads/main",
               "GITHUB_SHA": SHA, "GITHUB_EVENT_NAME": "push", "GITHUB_RUN_ATTEMPT": "1",
               "CROWN_AUTO_DEV_CD_ENABLED": "true"}
        with self.assertRaisesRegex(controller.Blocked, "source_activation_disabled"):
            controller.assert_event(SHA, env)

    def test_exact_backend_then_frontend_code_only_inputs(self):
        client = FakeGithub()
        snapshots = iter([observed(), observed("MATCH"), observed("MATCH", "MATCH")])
        result = controller.run_controller(
            SHA, client=client, eligibility_check=eligible,
            probe=lambda _: next(snapshots), sleep=lambda _: None)
        self.assertEqual(result, "RELEASED_AND_VERIFIED")
        self.assertEqual([wf for wf, _ in client.dispatched], [B, F])
        backend = client.dispatched[0][1]
        frontend = client.dispatched[1][1]
        self.assertEqual(backend["ref"], "main")
        self.assertIs(backend["return_run_details"], True)
        self.assertEqual(backend["inputs"]["ref"], SHA)
        for key in ("apply_reviewed_heritage24", "apply_finance_setup_0003",
                    "synthetic_dev_confirmed", "backup_recovery_verified",
                    "maintenance_window_confirmed"):
            self.assertEqual(backend["inputs"][key], "false")
        self.assertEqual(frontend["inputs"]["dev_certification_preview"], "true")
        self.assertEqual(frontend["inputs"]["dev_deploy_only"], "true")
        self.assertEqual(frontend["inputs"]["dev_hosted_jireh_preview"], "false")
        self.assertEqual(frontend["inputs"]["dev_source_sha"], SHA)

    def test_already_current_never_dispatches(self):
        client = FakeGithub()
        result = controller.run_controller(
            SHA, client=client, eligibility_check=eligible,
            probe=lambda _: observed("MATCH", "MATCH"))
        self.assertEqual(result, "ALREADY_CURRENT")
        self.assertEqual(client.calls, [])

    def test_backend_current_skips_duplicate_backend(self):
        client = FakeGithub()
        evidence = iter([observed("MATCH"), observed("MATCH", "MATCH")])
        controller.run_controller(SHA, client=client, eligibility_check=eligible,
                                  probe=lambda _: next(evidence), sleep=lambda _: None)
        self.assertEqual([wf for wf, _ in client.dispatched], [F])

    def test_missing_dispatch_id_never_retry(self):
        client = FakeGithub(fail="dispatch")
        with self.assertRaisesRegex(controller.Blocked, "dispatch_run_id_not_returned_no_retry"):
            controller.run_controller(SHA, client=client, eligibility_check=eligible,
                                      probe=lambda _: observed())
        self.assertEqual(len([call for call in client.calls if call[0] == "POST"]), 1)

    def test_other_active_release_blocks(self):
        client = FakeGithub(active=True)
        with self.assertRaisesRegex(controller.Blocked, "another_dev_workflow_is_active"):
            controller.run_controller(SHA, client=client, eligibility_check=eligible,
                                      probe=lambda _: observed())
        self.assertFalse(client.dispatched)

    def test_unhealthy_dev_blocks_before_writes(self):
        client = FakeGithub()
        with self.assertRaisesRegex(controller.Blocked, "existing_dev_runtime_safety_unverified"):
            controller.run_controller(SHA, client=client, eligibility_check=eligible,
                                      probe=lambda _: observed(safe=False))
        self.assertFalse(client.calls)

    def test_main_moved_mid_release_denies_frontend(self):
        client = FakeGithub()
        reports = iter([observed(), observed("MATCH")])
        attempts = [0]
        def gate(_):
            attempts[0] += 1
            if attempts[0] > 2:
                raise controller.Blocked("source_or_checks_no_longer_eligible")
        with self.assertRaisesRegex(controller.Blocked, "source_or_checks_no_longer_eligible"):
            controller.run_controller(SHA, client=client, eligibility_check=gate,
                                      probe=lambda _: next(reports), sleep=lambda _: None)
        self.assertEqual([wf for wf, _ in client.dispatched], [B])

    def test_prior_failed_workflow_does_not_retry(self):
        client = FakeGithub(prior={B: [dict(
            event="workflow_dispatch", head_sha=SHA, head_branch="main",
            path=".github/workflows/" + B, repository={"full_name": controller.REPO},
            run_attempt=1, status="completed", conclusion="failure")]})
        with self.assertRaisesRegex(controller.Blocked, "prior_workflow_incomplete_or_failed"):
            controller.run_controller(SHA, client=client, eligibility_check=eligible,
                                      probe=lambda _: observed())
        self.assertFalse(client.dispatched)

    def test_broken_or_untrusted_run_cannot_advance(self):
        for case in ("failure", "sha", "repository"):
            with self.subTest(case=case):
                client = FakeGithub()
                original_api = client.api
                def api(method, path, data=None):
                    result = original_api(method, path, data)
                    if method == "GET" and path.startswith("/actions/runs/"):
                        if case == "failure": result["conclusion"] = "failure"
                        if case == "sha": result["head_sha"] = "c" * 40
                        if case == "repository": result["repository"]["full_name"] = "another/repo"
                    return result
                client.api = api
                with self.assertRaises(controller.Blocked):
                    controller.run_controller(SHA, client=client, eligibility_check=eligible,
                                              probe=lambda _: observed(), sleep=lambda _: None)
                self.assertEqual([wf for wf, _ in client.dispatched], [B])


    def test_automatic_orchestration_isolated_and_both_keys_disabled(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / ".github/workflows/repository-freshness.yml").read_text()
        self.assertEqual(workflow.count("  dev-automatic-code-only-release:"), 1)
        job = workflow.split("  dev-automatic-code-only-release:", 1)[1].split(
            "  report-stale-branches:", 1)[0]
        self.assertIn("vars.CROWN_AUTO_DEV_CD_ENABLED == 'true'", job)
        self.assertIn("      group: crown-dev-auto-release", job)
        self.assertIn("      cancel-in-progress: false", job)
        self.assertIn("    environment: dev", job)
        self.assertIn("      actions: write", job)
        self.assertIn("      contents: read", job)
        self.assertIn("      checks: read", job)
        self.assertIn("persist-credentials: false", job)
        self.assertIn("dev_auto_release_controller.py --expected-sha", job)
        self.assertNotIn("azure/login@", job)
        self.assertNotIn("id-token: write", job)
        self.assertNotIn("secrets.", job)
        policy = json.loads((root / "scripts/ops/dev_auto_release_policy.json").read_text())
        self.assertIs(policy["enabled"], False)
        self.assertIs(policy["automatic_schema_changes"], False)

    def test_backend_mutation_requires_prior_capture_and_failed_auto_rolls_back(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / ".github/workflows/deploy-dev.yml").read_text()
        def order(name):
            return workflow.index("      - name: " + name)
        self.assertLess(
            order("Capture current healthy immutable DEV release before automatic mutation"),
            order("Mark automatic release mutation boundary"))
        self.assertLess(
            order("Mark automatic release mutation boundary"),
            order("Apply appsettings (allowlisted only)"))
        self.assertLess(
            order("Apply appsettings (allowlisted only)"),
            order("Restore prior immutable DEV image after failed automatic mutation"))
        self.assertIn("if: failure() && inputs.auto_code_only == true", workflow)
        self.assertIn("test \"$AUTO_ENABLED\" = true", workflow)
        self.assertIn("test \"$APPLY_REVIEWED24\" = false", workflow)
        self.assertIn("test \"$APPLY_FINANCE\" = false", workflow)
        self.assertIn("python scripts/ops/dev_release_rollback.py capture", workflow)
        self.assertIn("python scripts/ops/dev_release_rollback.py restore", workflow)
        self.assertIn("  workflow_dispatch:", workflow)
        self.assertNotIn("  schedule:", workflow)


if __name__ == "__main__":
    unittest.main()
