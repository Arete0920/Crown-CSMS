"""Offline image-probe control tests; never contact ACR, Azure or a database."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_dev_prior_image as module

SHA = "a" * 40
CONTAINER = "b" * 64
DB = "crown_restore_123_2"
ENV = {
    "GITHUB_ACTIONS": "true", "GITHUB_REF": "refs/heads/main",
    "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REPOSITORY": "Arete0920/Crown-CSMS",
    "GITHUB_REPOSITORY_ID": "1339719218", "GITHUB_SHA": SHA,
    "GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "2", "POSTGRES_CONTAINER_ID": CONTAINER,
    "PATH": "/usr/bin", "HOME": "/tmp", "DOCKER_CONFIG": "/tmp/probe-auth",
    "DATABASE_URL": "PRIVATE", "PGPASSWORD": "PRIVATE", "AZURE_CLIENT_SECRET": "PRIVATE",
    "IDENTITY_ENDPOINT": "PRIVATE", "GH_TOKEN": "PRIVATE", "DOCKER_HOST": "tcp://private:2375",
}


def runner(*, failure=None, receipt=None):
    calls = []
    labels = {}
    def run(args, **kwargs):
        calls.append((args, kwargs))
        operation = args[3]
        code, stdout = 0, ""
        if operation == "image": stdout = json.dumps([module.PRIOR_IMAGE])
        if operation == "run":
            key, value = args[args.index("--label")+1].split("=", 1)
            labels[key] = value
        if operation == "container": stdout = json.dumps(labels)
        if operation == "exec": stdout = json.dumps(receipt or {"result": "PASS"})
        if operation == failure: code, stdout = 1, "PRIVATE"
        return SimpleNamespace(returncode=code, stdout=stdout, stderr="PRIVATE")
    return calls, run


class PriorImageContracts(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("CROWN_PRIOR_IMAGE_TEST_CONTAINER"), "requires disposable PG15")
    def test_actual_pg15_role_database_and_cluster_boundary(self):
        import dev_backup_restore as recovery
        container = os.environ["CROWN_PRIOR_IMAGE_TEST_CONTAINER"]
        env = recovery.target_environment(os.environ)
        recovery.target_identity(container, env, expected_major=15)
        with recovery.disposable_database(container, env, DB, {}):
            cluster = recovery.scalar(container, env, DB, "SELECT system_identifier FROM pg_control_system()")
            module.verify_disposable_target(container, DB, cluster, os.environ)
            with self.assertRaisesRegex(module.PriorImageBlocked, "^prior_image_disposable_target_unverified$"):
                module.verify_disposable_target(container, DB, "0", os.environ)

    def test_exact_job_copy_is_required_before_any_process_or_target_access(self):
        for changes in ({"GITHUB_ACTIONS": "false"}, {"GITHUB_REF": "refs/heads/rc/test"},
                        {"GITHUB_EVENT_NAME": "push"}, {"GITHUB_REPOSITORY": "other/repo"},
                        {"GITHUB_REPOSITORY_ID": "1"}, {"GITHUB_SHA": "c" * 40},
                        {"GITHUB_RUN_ATTEMPT": "3"}, {"POSTGRES_CONTAINER_ID": "d" * 64}):
            target, process = Mock(), Mock()
            with self.subTest(changes=changes), self.assertRaises(module.PriorImageBlocked):
                module.probe_prior_image(CONTAINER, DB, "12345", SHA, {**ENV, **changes},
                                         run=process, verify_target=target)
            target.assert_not_called()
            process.assert_not_called()
        for database, cluster in (("postgres", "123"), ("production", "123"), (DB, "--evil")):
            with self.subTest(database=database, cluster=cluster), self.assertRaises(module.PriorImageBlocked):
                module.validate_scope(CONTAINER, database, cluster, SHA, ENV)

    def test_wrong_disposable_identity_blocks_before_registry_or_image_start(self):
        process = Mock()
        target = Mock(side_effect=module.PriorImageBlocked("prior_image_disposable_target_unverified"))
        with self.assertRaisesRegex(module.PriorImageBlocked, "^prior_image_disposable_target_unverified$"):
            module.probe_prior_image(CONTAINER, DB, "12345", SHA, ENV, run=process, verify_target=target)
        process.assert_not_called()

    def test_real_target_verifier_requires_pg15_database_and_cluster(self):
        import dev_backup_restore as recovery
        for values in ((DB, "12345"), ("production", "12345"), (DB, "999")):
            with patch.object(recovery, "target_identity") as identity, \
                 patch.object(recovery, "scalar", side_effect=values):
                if values == (DB, "12345"):
                    module.verify_disposable_target(CONTAINER, DB, "12345", ENV)
                    self.assertEqual(identity.call_args.kwargs, {"expected_major": 15})
                else:
                    with self.assertRaises(module.PriorImageBlocked):
                        module.verify_disposable_target(CONTAINER, DB, "12345", ENV)

    def test_fixed_digest_original_startup_and_bounded_container_have_no_live_credentials(self):
        calls, run = runner()
        target = Mock()
        receipt = module.probe_prior_image(CONTAINER, DB, "12345", SHA, ENV, run=run, verify_target=target)
        target.assert_called_once_with(CONTAINER, DB, "12345", ENV)
        self.assertEqual(receipt["result"], "PASS")
        self.assertEqual(receipt["full_application_rollback"], "NOT_VERIFIED")
        self.assertTrue(receipt["probe_container_removed"])
        self.assertEqual(calls[0][0], module.DOCKER + ["pull", module.PRIOR_IMAGE])
        args, kwargs = next(c for c in calls if c[0][3] == "run")
        self.assertEqual(args[-1], module.PRIOR_IMAGE)
        self.assertIn("container:" + CONTAINER, args)
        for flag in ("--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
                     "--pids-limit=128", "--memory=768m", "--cpus=1", "--log-driver=none"):
            self.assertIn(flag, args)
        for flag in ("--entrypoint", "--volume", "--mount", "--publish", "--privileged"):
            self.assertNotIn(flag, args)
        self.assertEqual(kwargs["env"]["DATABASE_URL"],
                         f"postgresql://crown_drill:crown-drill-password@127.0.0.1:5432/{DB}?sslmode=disable")
        self.assertNotIn("DATABASE_URL=", " ".join(args))
        self.assertNotIn(kwargs["env"]["DJANGO_SECRET_KEY"], " ".join(args))
        self.assertNotIn("PRIVATE", json.dumps(calls))
        for key in ("GH_TOKEN", "AZURE_CLIENT_SECRET", "IDENTITY_ENDPOINT", "PGPASSWORD", "DOCKER_HOST"):
            self.assertNotIn(key, kwargs["env"])
        self.assertEqual(kwargs["env"]["HTTPS_PROXY"], "")

    def test_pull_or_digest_failure_does_not_start_container_and_never_leaks_errors(self):
        for operation in ("pull", "image"):
            calls, run = runner(failure=operation)
            with self.subTest(operation=operation), self.assertRaises(module.PriorImageBlocked) as error:
                module.probe_prior_image(CONTAINER, DB, "12345", SHA, ENV, run=run, verify_target=Mock())
            self.assertNotIn("PRIVATE", str(error.exception))
            self.assertFalse(any(args[3] == "run" for args, _ in calls))

    def test_cleanup_runs_on_uncertain_start_and_failed_or_private_probe_receipt(self):
        for failure in ("run", "exec"):
            calls, run = runner(failure=failure)
            with self.subTest(failure=failure), self.assertRaises(module.PriorImageBlocked):
                module.probe_prior_image(CONTAINER, DB, "12345", SHA, ENV, run=run, verify_target=Mock())
            self.assertEqual(calls[-1][0][3:5], ["rm", "--force"])
        for receipt in ({"result": "PASS", "extra": "PRIVATE"},
                        {"result": "BLOCKED", "reason": "PRIVATE"},
                        {"result": "BLOCKED", "reason": ["PRIVATE"]}):
            calls, run = runner(receipt=receipt)
            with self.subTest(receipt=receipt), self.assertRaisesRegex(module.PriorImageBlocked,
                                                                     "^prior_image_probe_receipt_invalid$"):
                module.probe_prior_image(CONTAINER, DB, "12345", SHA, ENV, run=run, verify_target=Mock())
            self.assertEqual(calls[-1][0][3], "rm")

    def test_only_fixed_failure_codes_cross_child_boundary(self):
        for reason in module.SAFE_REASONS:
            _, run = runner(receipt={"result": "BLOCKED", "reason": reason})
            with self.subTest(reason=reason), self.assertRaisesRegex(module.PriorImageBlocked, "^"+reason+"$"):
                module.probe_prior_image(CONTAINER, DB, "12345", SHA, ENV, run=run, verify_target=Mock())

    def test_failed_cleanup_or_timeout_cannot_return_pass(self):
        _, run = runner(failure="rm")
        with self.assertRaisesRegex(module.PriorImageBlocked, "^prior_image_container_cleanup_failed$"):
            module.probe_prior_image(CONTAINER, DB, "12345", SHA, ENV, run=run, verify_target=Mock())
        with self.assertRaisesRegex(module.PriorImageBlocked, "^prior_image_process_unavailable$"):
            module.probe_prior_image(CONTAINER, DB, "12345", SHA, ENV,
                run=Mock(side_effect=subprocess.TimeoutExpired(["PRIVATE"], 1)), verify_target=Mock())

    def test_unrelated_or_unverifiable_container_is_never_deleted(self):
        for labels in ({}, {"crown.prior-probe": "someone-else"}, "PRIVATE"):
            calls, real = runner()
            def run(args, **kwargs):
                result = real(args, **kwargs)
                if args[3] == "container": result.stdout = json.dumps(labels)
                return result
            with self.subTest(labels=labels), self.assertRaisesRegex(module.PriorImageBlocked,
                                                           "^prior_image_container_cleanup_unverified$"):
                module.probe_prior_image(CONTAINER, DB, "12345", SHA, ENV, run=run, verify_target=Mock())
            self.assertFalse(any(args[3] == "rm" for args, _ in calls))

    def test_workflow_dispatch_authority_matrix_executes_without_cloud_access(self):
        import yaml
        root = Path(__file__).resolve().parents[2]
        workflow = yaml.safe_load((root / ".github/workflows/isolated-postgres-restore-drill.yml").read_text())
        dispatch = workflow.get("on", workflow.get(True))["workflow_dispatch"]["inputs"]
        self.assertIs(dispatch["verify_prior_image"]["default"], False)
        steps = workflow["jobs"]["dev-restore-contracts"]["steps"]
        guard = next(s["run"] for s in steps if s.get("name") ==
                     "Require explicit disposable prior-image probe authority")
        cases = [("false", "false", "false", "", 0),
                 ("true", "true", "true", module.CONFIRMATION, 0),
                 ("false", "true", "true", module.CONFIRMATION, 1),
                 ("true", "false", "true", module.CONFIRMATION, 1),
                 ("true", "true", "true", "wrong", 1),
                 ("true", "true", "false", module.CONFIRMATION, 1)]
        for operational, rehearse, image, confirmation, expected in cases:
            with self.subTest(operational=operational, rehearse=rehearse, image=image, confirmation=confirmation):
                result = subprocess.run(["bash", "-c", guard], env={"PATH": os.environ["PATH"],
                    "OPERATIONAL": operational, "REHEARSE": rehearse,
                    "PRIOR_IMAGE": image, "PRIOR_CONFIRMATION": confirmation},
                    capture_output=True, check=False, timeout=5)
                self.assertEqual(bool(result.returncode), bool(expected))
        operational = workflow["jobs"]["dev-operational-restore"]
        self.assertIn("github.ref == 'refs/heads/main'", operational["if"])
        login = next(s for s in operational["steps"] if s.get("name", "").startswith("Authenticate pull"))
        self.assertEqual(login["if"], "inputs.verify_prior_image == true")
        self.assertNotIn("expose-token", login["run"])

    def test_embedded_probe_parses_and_all_synthetic_writes_are_in_rollback_transaction(self):
        tree = ast.parse(module.PROBE)
        writes = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Attribute) and n.func.attr == "create"]
        atomic = [n for n in ast.walk(tree) if isinstance(n, ast.With) and any(
            isinstance(i.context_expr, ast.Call) and isinstance(i.context_expr.func, ast.Attribute)
            and i.context_expr.func.attr == "atomic" for i in n.items)]
        self.assertEqual(len(atomic), 1)
        self.assertTrue(writes)
        self.assertTrue(all(n in list(ast.walk(atomic[0])) for n in writes))
        self.assertFalse(any(isinstance(n, ast.Return) for n in ast.walk(atomic[0])))
        self.assertIn("transaction.set_rollback(True)", module.PROBE)
        self.assertIn("artifact_build_sha", module.PROBE)
        self.assertIn("class NoRedirect", module.PROBE)


if __name__ == "__main__":
    unittest.main()
