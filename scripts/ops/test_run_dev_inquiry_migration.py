"""DEV migration boundary tests: no Azure requests, database or provider calls."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_dev_inquiry_migration as migration


URL = "postgresql://synthetic:private-password@crown-pg-dev.postgres.database.azure.com/crown?sslmode=require"
SHA = "a" * 40


class DevMigrationBoundaryTests(unittest.TestCase):
    def test_database_identity_rejects_production_lookalikes_overrides_and_default_databases(self):
        self.assertEqual(migration.validate_database_url(URL), "crown")
        rejected = [
            URL.replace("crown-pg-dev", "crown-db-prod"),
            URL.replace(".azure.com", ".azure.com.attacker.invalid"),
            URL.replace("/crown?", "/postgres?"), URL.replace("/crown?", "/template1?"),
            URL.replace("/crown?", "/?"), URL.replace("/crown?", "/crown/other?"),
            URL.replace(".com/", ".com:5433/"), URL.replace("require", "disable"),
            URL + "&hostaddr=127.0.0.1", URL + "&options=-csearch_path=other",
            URL + "#ignored", "sqlite:///crown", URL.replace("private-password", ""),
        ]
        for value in rejected:
            with self.subTest(value=value), self.assertRaises((migration.Blocked, ValueError)):
                migration.validate_database_url(value)

    def test_configuration_is_read_only_and_bound_to_existing_dev_app(self):
        calls = []

        def read(*args):
            calls.append(args)
            if args[:2] == ("webapp", "show"):
                return {"name": "crown-api-dev", "defaultHostName": "crown-api-dev.azurewebsites.net"}
            return [{"name": key, "value": value} for key, value in {
                "CROWN_ENV": "dev", "ENVIRONMENT": "dev", "DJANGO_ENV": "development",
                "DATABASE_URL": URL, "SECRET_KEY": "synthetic-secret",
            }.items()]

        self.assertEqual(migration.load_dev_settings(read=read), (URL, "synthetic-secret", "crown"))
        self.assertEqual(len(calls), 2)
        self.assertTrue(all("crown-api-dev" in call and "crown-rg" in call for call in calls))
        self.assertTrue(all(not {"create", "set", "update", "delete", "restart"}.intersection(call) for call in calls))
        with self.assertRaises(migration.Blocked):
            migration.load_dev_settings(read=lambda *args: {"name": "crown-api-prod", "defaultHostName": "crown-api-prod.azurewebsites.net"})
        with self.assertRaises(migration.Blocked):
            migration.load_dev_settings(read=Mock(side_effect=[
                {"name": "crown-api-dev", "defaultHostName": "crown-api-dev.azurewebsites.net"},
                [{"name": "CROWN_ENV", "value": "production"}],
            ]))
        rejected = Mock(side_effect=[
            {"name": "crown-api-dev", "defaultHostName": "crown-api-dev.azurewebsites.net"},
            [{"name": key, "value": value} for key, value in {
                "CROWN_ENV": "dev", "ENVIRONMENT": "dev", "DJANGO_ENV": "development",
                "DATABASE_URL": URL.replace("crown-pg-dev", "crown-db-prod"),
                "SECRET_KEY": "@Microsoft.KeyVault(VaultName=existing-vault;SecretName=key)",
            }.items()],
        ])
        with self.assertRaises(migration.Blocked):
            migration.load_dev_settings(read=rejected)
        self.assertEqual(rejected.call_count, 2)  # Reject target before resolving another secret.

    def test_verified_tls_is_configured_before_django_application_setup(self):
        def setup():
            target = migration.urlsplit(os.environ["DATABASE_URL"])
            self.assertEqual(target.hostname, migration.DEV_HOST)
            self.assertEqual(dict(migration.parse_qsl(target.query)), {
                "sslmode": "verify-full", "sslrootcert": "/etc/ssl/certs/ca-certificates.crt", "connect_timeout": "15",
            })
            raise RuntimeError("stop before database access")

        with patch.dict(os.environ, {}, clear=True), patch.dict("sys.modules", {"django": SimpleNamespace(setup=setup)}), \
                patch.object(migration.Path, "is_file", return_value=True):
            with self.assertRaisesRegex(RuntimeError, "stop before database access"):
                migration.migrate_on_dev(URL, "synthetic-secret", "crown", SHA)

    def test_blacklist_app_enabled_only_in_read_only_or_authorized_schema_stage(self):
        # Stop before opening a database and inspect exactly what Django sees.
        for kwargs, enabled in (
            ({}, "false"),
            ({"check_only": True}, "true"),
            ({"apply_blacklist": True}, "true"),
        ):
            with self.subTest(kwargs=kwargs):
                def setup():
                    self.assertEqual(
                        os.environ["CROWN_SIMPLEJWT_BLACKLIST_ENABLED"], enabled
                    )
                    raise RuntimeError("halt before touching database")
                with patch.dict(os.environ, {}, clear=True), patch.dict(
                    "sys.modules", {"django": SimpleNamespace(setup=setup)}
                ), patch.object(migration.Path, "is_file", return_value=True):
                    with self.assertRaisesRegex(RuntimeError, "halt before"):
                        migration.migrate_on_dev(URL, "synthetic-secret", "crown", SHA, **kwargs)

    def test_key_vault_reference_is_parsed_as_data_and_rejects_external_hosts(self):
        read = Mock(return_value={"value": "resolved-private-value"})
        uri = "https://existing-vault.vault.azure.net/secrets/existing-secret/version"
        self.assertEqual(migration.resolve_value("@Microsoft.KeyVault(SecretUri=" + uri + ")", read=read), "resolved-private-value")
        read.assert_called_once_with("keyvault", "secret", "show", "--id", uri)
        for reference in [
            "@Microsoft.KeyVault(SecretUri=https://attacker.invalid/secrets/key)",
            "@Microsoft.KeyVault(SecretUri=" + uri + "?override=true)",
            "@Microsoft.KeyVault(VaultName=--unsafe;SecretName=key;VaultName=second)",
        ]:
            with self.subTest(reference=reference), self.assertRaises(migration.Blocked):
                migration.resolve_value(reference, read=read)
        self.assertEqual(read.call_count, 1)

    def test_source_requires_full_accepted_sha_and_exact_reviewed_migration_bytes(self):
        reviewed_bytes = (migration.ROOT / "backend/crm_marketing/migrations/0002_inquiry_capture.py").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file = root / "backend/crm_marketing/migrations/0002_inquiry_capture.py"
            file.parent.mkdir(parents=True)
            file.write_bytes(reviewed_bytes)
            run = Mock(side_effect=[SimpleNamespace(returncode=0, stdout=SHA), SimpleNamespace(returncode=0)])
            migration.validate_source(SHA, root=root, run=run)
            self.assertEqual(hashlib.sha256(reviewed_bytes).hexdigest(), migration.MIGRATION_SHA256)
            self.assertEqual(run.call_args_list[1].args[0], ["git", "merge-base", "--is-ancestor", SHA, "origin/main"])
            for head, ancestry, expected in [("b" * 40, 0, SHA), (SHA, 1, SHA), (SHA, 0, "main")]:
                with self.subTest(head=head, ancestry=ancestry, expected=expected), self.assertRaises(migration.Blocked):
                    migration.validate_source(expected, root=root, run=Mock(side_effect=[
                        SimpleNamespace(returncode=0, stdout=head), SimpleNamespace(returncode=ancestry),
                    ]))
            file.write_bytes(reviewed_bytes + b"\n# unreviewed change\n")
            with self.assertRaisesRegex(migration.Blocked, "digest_mismatch"):
                migration.validate_source(SHA, root=root, run=Mock(side_effect=[
                    SimpleNamespace(returncode=0, stdout=SHA), SimpleNamespace(returncode=0),
                ]))

    def _execute(self, plans, *, identity_error=False, ddl_error=False, check_only=False,
                 plan_validator=migration.validate_plan, post_verify=None):
        events = []

        @contextlib.contextmanager
        def acquire():
            events.append("lock")
            try:
                yield
            finally:
                events.append("unlock")

        def verify_identity():
            events.append("identity")
            if identity_error:
                raise migration.Blocked("connected_database_identity_mismatch")

        def verify_ddl():
            events.append("ddl")
            if ddl_error:
                raise migration.Blocked("existing_database_ddl_authority_unavailable")

        def read_plan():
            events.append("plan")
            return plans.pop(0)

        def invoke(name, **kwargs):
            events.append((name, kwargs))

        self.events = events
        return migration.apply_reviewed_plan(acquire_lock=acquire, verify_identity=verify_identity,
            verify_ddl=verify_ddl, read_plan=read_plan, invoke=invoke,
            check_only=check_only, plan_validator=plan_validator, post_verify=post_verify)

    def test_reviewed_plan_is_checked_and_verified_under_same_lock(self):
        item = SimpleNamespace(app_label="crm_marketing", name="0002_inquiry_capture")
        self.assertEqual(self._execute([[(item, False)], []]), ["crm_marketing.0002_inquiry_capture"])
        self.assertEqual(self.events, ["lock", "identity", "plan", "ddl",
            ("migrate_with_lock", {"lock_timeout_seconds": 300, "check": False}),
            ("migrate", {"check": True, "interactive": False}), "plan", "unlock"])

    def test_empty_plan_only_checks_without_running_migration_mutations(self):
        self.assertEqual(self._execute([[], []]), [])
        self.assertNotIn("ddl", self.events)
        self.assertIn(("migrate_with_lock", {"lock_timeout_seconds": 300, "check": True}), self.events)

    def test_other_reverse_or_missing_dependency_plans_never_reach_apply(self):
        reviewed = SimpleNamespace(app_label="crm_marketing", name="0002_inquiry_capture")
        other = SimpleNamespace(app_label="applications", name="0011_application_checklist_access_key_and_more")
        for plan in [[(other, False)], [(reviewed, True)], [(other, False), (reviewed, False)]]:
            with self.subTest(plan=plan), self.assertRaisesRegex(migration.Blocked, "unreviewed"):
                self._execute([plan])
            self.assertFalse(any(isinstance(item, tuple) for item in self.events))
            self.assertEqual(self.events[-1], "unlock")

    def test_identity_or_ddl_failure_does_not_invoke_migration(self):
        reviewed = SimpleNamespace(app_label="crm_marketing", name="0002_inquiry_capture")
        for kwargs in ({"identity_error": True}, {"ddl_error": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(migration.Blocked):
                self._execute([[(reviewed, False)]], **kwargs)
            self.assertFalse(any(isinstance(item, tuple) for item in self.events))

    def test_verification_failure_cannot_be_reported_as_success(self):
        other = SimpleNamespace(app_label="other", name="0001_initial")
        with self.assertRaisesRegex(migration.Blocked, "after_verification"):
            self._execute([[], [(other, False)]])

    def test_failures_emit_safe_bounded_plan_context_without_raw_errors(self):
        output = io.StringIO()
        with patch.object(migration, "validate_source"), patch.object(migration, "load_dev_settings",
                side_effect=RuntimeError("private-password provider detail")), contextlib.redirect_stdout(output):
            self.assertEqual(migration.main(["--expected-sha", SHA]), 1)
        self.assertNotIn("private-password", output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["status"], "BLOCKED")

        reviewed = SimpleNamespace(app_label="crm_marketing", name="0002_inquiry_capture")
        other = SimpleNamespace(app_label="applications", name="0011_application_checklist_access_key_and_more")
        unsafe = SimpleNamespace(app_label="x" * 129, name="private-password\nSELECT * FROM sensitive")
        plan = [(other, False), (reviewed, True), (unsafe, False)] + [(other, False)] * 20
        output = io.StringIO()
        with patch.object(migration, "validate_source"), patch.object(migration, "load_dev_settings",
                return_value=(URL, "synthetic-secret", "crown")), patch.object(migration, "migrate_on_dev",
                side_effect=lambda *args: self._execute([plan])), contextlib.redirect_stdout(output):
            self.assertEqual(migration.main(["--expected-sha", SHA]), 1)
        # Masking commands are consumed by GitHub; only the final line is structured evidence.
        evidence_line = output.getvalue().splitlines()[-1]
        evidence = json.loads(evidence_line)
        self.assertEqual(evidence["reason"], "unreviewed_pending_migrations")
        self.assertEqual(evidence["source_sha"], SHA)
        self.assertEqual(evidence["target_app"], "crown-api-dev")
        self.assertEqual(evidence["pending_migrations_count"], len(plan))
        self.assertTrue(evidence["pending_migrations_truncated"])
        self.assertEqual(len(evidence["pending_migrations"]), 20)
        self.assertEqual(evidence["pending_migrations"][0], {
            "app": other.app_label, "migration": other.name, "direction": "forward",
        })
        self.assertEqual(evidence["pending_migrations"][1]["direction"], "backward")
        self.assertEqual(evidence["pending_migrations"][2], {
            "app": "[invalid]", "migration": "[invalid]", "direction": "forward",
        })
        for sensitive in ("private-password", "SELECT", URL, "synthetic-secret"):
            self.assertNotIn(sensitive, evidence_line)
        self.assertFalse(any(isinstance(item, tuple) for item in self.events))

    def test_read_only_preflight_never_invokes_migration_or_ddl(self):
        item = SimpleNamespace(app_label="crm_marketing", name="0002_inquiry_capture")
        self.assertEqual(
            self._execute([[(item, False)]], check_only=True),
            ["crm_marketing.0002_inquiry_capture"],
        )
        self.assertEqual(self.events, ["lock", "identity", "plan", "unlock"])
        other = SimpleNamespace(app_label="token_blacklist", name="0001_initial")
        with self.assertRaisesRegex(migration.Blocked, "unreviewed"):
            self._execute([[(other, False)]], check_only=True)
        self.assertEqual(self.events, ["lock", "identity", "plan", "unlock"])

    def test_read_only_cli_emits_mode_and_invokes_no_write_path(self):
        output = io.StringIO()
        with patch.object(migration, "validate_source"), patch.object(
            migration, "load_dev_settings",
            return_value=(URL, "synthetic-secret", "crown")
        ), patch.object(migration, "migrate_on_dev", return_value=[]) as called, contextlib.redirect_stdout(output):
            self.assertEqual(migration.main(["--expected-sha", SHA, "--check-only"]), 0)
        called.assert_called_once_with(URL, "synthetic-secret", "crown", SHA, check_only=True)
        evidence = json.loads(output.getvalue().splitlines()[-1])
        self.assertEqual(evidence["status"], "PASS")
        self.assertEqual(evidence["mode"], "read_only")
        self.assertEqual(evidence["reviewed_pending_migrations"], [])

    def test_explicit_blacklist_stage_accepts_only_exact_upstream_suffix(self):
        from reviewed_blacklist_migrations import APP_LABEL, MIGRATION_NAMES
        suffix = [(SimpleNamespace(app_label=APP_LABEL, name=name), False)
                  for name in MIGRATION_NAMES[9:]]
        self.assertEqual(migration.validate_blacklist_plan(suffix),
                         [(APP_LABEL, name) for name in MIGRATION_NAMES[9:]])
        self.assertEqual(migration.validate_blacklist_plan([]), [])
        foreign = (SimpleNamespace(app_label="crm_marketing", name="0002_inquiry_capture"), False)
        for bad in [
            [foreign],
            suffix + [foreign],
            [foreign] + suffix,
            list(reversed(suffix)),
            [(suffix[0][0], True)],
        ]:
            with self.subTest(plan=bad), self.assertRaises(migration.UnreviewedPlan):
                migration.validate_blacklist_plan(bad)

    def test_schema_postverification_precedes_unlock_and_is_required(self):
        from reviewed_blacklist_migrations import APP_LABEL, MIGRATION_NAMES
        initial = SimpleNamespace(app_label=APP_LABEL, name=MIGRATION_NAMES[0])
        def verified():
            self.events.append("schema_verified")
        self.assertEqual(
            self._execute(
                [[(initial, False)], []],
                plan_validator=migration.validate_blacklist_plan,
                post_verify=verified,
            ), [APP_LABEL + "." + MIGRATION_NAMES[0]]
        )
        self.assertEqual(self.events[-3:], ["plan", "schema_verified", "unlock"])
        with self.assertRaisesRegex(migration.Blocked, "schema_invalid"):
            self._execute(
                [[], []],
                plan_validator=migration.validate_blacklist_plan,
                post_verify=lambda: (_ for _ in ()).throw(migration.Blocked("schema_invalid")),
            )
        self.assertEqual(self.events[-1], "unlock")

    def test_blacklist_schema_authority_is_explicit_and_conflict_safe(self):
        output = io.StringIO()
        with patch.object(migration, "validate_source"), patch.object(
            migration, "load_dev_settings",
            return_value=(URL, "synthetic-secret", "crown")
        ), patch.object(migration, "migrate_on_dev", return_value=[]) as called, contextlib.redirect_stdout(output):
            self.assertEqual(
                migration.main(["--expected-sha", SHA, "--apply-reviewed-blacklist",
                                "--confirm-dev-blacklist", "migrate-dev-blacklist"]), 0
            )
        called.assert_called_once_with(URL, "synthetic-secret", "crown", SHA,
                                       apply_blacklist=True)
        self.assertEqual(json.loads(output.getvalue().splitlines()[-1])["mode"],
                         "reviewed_dev_blacklist")
        for args in [
            ["--apply-reviewed-blacklist"],
            ["--confirm-dev-blacklist", "migrate-dev-blacklist"],
            ["--apply-reviewed-blacklist", "--confirm-dev-blacklist", "wrong"],
            ["--apply-reviewed-blacklist", "--confirm-dev-blacklist", "migrate-dev-blacklist",
             "--check-only"],
        ]:
            with self.subTest(args=args), patch.object(migration, "validate_source") as source, patch.object(
                migration, "load_dev_settings"
            ) as read, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(migration.main(["--expected-sha", SHA, *args]), 1)
                source.assert_not_called()
                read.assert_not_called()

    def test_workflow_checks_source_then_schema_before_any_runtime_mutation(self):
        import yaml
        workflow = yaml.safe_load((migration.ROOT / ".github/workflows/deploy-dev.yml").read_text())
        triggers = workflow.get("on", workflow.get(True))
        self.assertEqual(set(triggers), {"push", "workflow_dispatch"})
        self.assertEqual(triggers["push"]["branches"], ["rc/**"])
        job = workflow["jobs"]["build-and-deploy"]
        self.assertEqual(job["environment"], "dev")
        steps = job["steps"]
        source = next(i for i, step in enumerate(steps) if step.get("name") == "Verify accepted DEV source")
        gate = next(i for i, step in enumerate(steps) if "run_dev_inquiry_migration.py --expected-sha" in step.get("run", ""))
        self.assertIn("git fetch --no-tags origin refs/heads/main:refs/remotes/origin/main", steps[source]["run"])
        self.assertIn('git merge-base --is-ancestor "$SOURCE_SHA" origin/main', steps[source]["run"])
        self.assertNotIn("if", steps[gate])
        self.assertNotIn("continue-on-error", steps[gate])
        for index, step in enumerate(steps):
            command, action = step.get("run", ""), step.get("uses", "")
            if "pip install" in command or "azure/login@" in action:
                self.assertLess(source, index)
            if ("az webapp config appsettings set" in command or "az webapp config container set" in command
                    or "docker/build-push-action@" in action or "az webapp start" in command):
                self.assertLess(gate, index)
        guard = steps[0]
        self.assertEqual(guard["env"]["INPUT_REF"], "${{ github.event.inputs.ref }}")
        self.assertNotIn("${{ github.event.inputs.ref }}", guard["run"])


if __name__ == "__main__":
    unittest.main()
