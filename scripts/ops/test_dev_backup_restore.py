"""Offline negative contracts; no Azure, Docker or database connection."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dev_backup_restore as module

SHA = "a" * 40
ENV = {
    "GITHUB_ACTIONS": "true", "GITHUB_REF": "refs/heads/main",
    "GITHUB_EVENT_NAME": "workflow_dispatch", "POSTGRES_CONTAINER_ID": "b" * 64,
    "GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "2", "PATH": "/usr/bin",
}


class RecoveryBoundaryTests(unittest.TestCase):
    def test_authority_requires_each_independent_boundary(self):
        self.assertEqual(module.authority(SHA, module.CONFIRMATION, "true", ENV)[1], "crown_restore_123_2")
        for changes in ({"GITHUB_ACTIONS": "false"}, {"GITHUB_REF": "refs/heads/rc/test"},
                        {"GITHUB_EVENT_NAME": "push"}, {"POSTGRES_CONTAINER_ID": "--evil"},
                        {"GITHUB_RUN_ID": "123;bad"}):
            with self.subTest(changes=changes), self.assertRaises(module.RestoreBlocked):
                module.authority(SHA, module.CONFIRMATION, "true", {**ENV, **changes})
        for sha, confirmation, synthetic in [("short", module.CONFIRMATION, "true"),
                                             (SHA, "", "true"), (SHA, module.CONFIRMATION, "false")]:
            with self.assertRaises(module.RestoreBlocked):
                module.authority(sha, confirmation, synthetic, ENV)

    def test_target_discards_ambient_connection_and_service_secrets(self):
        env = module.target_environment({**ENV, "PGHOST": "production.invalid",
              "PGHOSTADDR": "10.0.0.1", "PGSERVICE": "production",
              "PGSERVICEFILE": "/secret", "PGPASSWORD": "PRIVATE", "DATABASE_URL": "PRIVATE"})
        self.assertEqual(env["PGHOST"], "127.0.0.1")
        self.assertEqual(env["PGDATABASE"], "postgres")
        self.assertNotIn("PGHOSTADDR", env)
        self.assertNotIn("PGSERVICE", env)
        self.assertNotIn("PGSERVICEFILE", env)
        self.assertNotIn("DATABASE_URL", env)
        self.assertNotIn("PRIVATE", json.dumps(env))

    def test_source_rejects_wrong_database_even_on_dev_host(self):
        url = "postgresql://user:PRIVATE@" + module.DEV_HOST + "/wrong"
        with self.assertRaises(module.RestoreBlocked):
            module.source_environment(url, "wrong", ENV)
        with self.assertRaises(Exception):
            module.source_environment("postgresql://user:PRIVATE@production.invalid/wrong", "wrong", ENV)

    def test_docker_arguments_never_include_credential_values(self):
        env = {**module.target_environment(ENV), "PGPASSWORD": "PRIVATE"}
        command = module.docker_command("b" * 64, env, ["psql", "--dbname", "postgres"])
        self.assertIn("PGPASSWORD", command)
        self.assertNotIn("PRIVATE", " ".join(command))
        self.assertEqual(command[1:3], ["--host", "unix:///var/run/docker.sock"])

    def test_process_failures_do_not_disclose_stderr(self):
        def fail(*args, **kwargs):
            return SimpleNamespace(returncode=1, stdout=b"PRIVATE", stderr=b"PRIVATE")
        with self.assertRaisesRegex(module.RestoreBlocked, "^postgres_process_failed$"):
            module.execute("b" * 64, module.target_environment(ENV), ["psql"], run=fail)

    def test_private_archive_removed_after_failure(self):
        evidence = {}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                with module.private_archive({"RUNNER_TEMP": directory}, evidence) as archive:
                    archive.write_bytes(b"PRIVATE")
                    raise ValueError("failure")
            self.assertFalse(archive.exists())
            self.assertTrue(evidence["ephemeral_backup_removed"])
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_target_identity_is_checked_before_database_creation(self):
        for value in ["postgres|crown_drill|10.0.0.1|160015", "production|crown_drill|127.0.0.1|160015",
                      "postgres|other|127.0.0.1|160015", "postgres|crown_drill|127.0.0.1|180000"]:
            with patch.object(module, "scalar", return_value=value), self.assertRaises(module.RestoreBlocked):
                module.target_identity("b" * 64, module.target_environment(ENV))

    def test_failed_restore_still_drops_only_created_database(self):
        calls, evidence = [], {}
        def action(container, env, command):
            calls.append(command)
            return b"0\n"
        with self.assertRaisesRegex(ValueError, "restore failed"):
            with module.disposable_database("b" * 64, {}, "crown_restore_123_2", evidence, action=action):
                raise ValueError("restore failed")
        self.assertEqual(calls[-1], ["dropdb", "--maintenance-db=postgres", "--if-exists", "--force", "crown_restore_123_2"])
        self.assertTrue(evidence["disposable_database_dropped"])
        with self.assertRaises(module.RestoreBlocked):
            with module.disposable_database("b" * 64, {}, "postgres", {}, action=action):
                pass

    def test_cleanup_failure_prevents_success(self):
        def action(container, env, command):
            if command[0] == "dropdb":
                raise RuntimeError("PRIVATE")
            return b"0\n"
        with self.assertRaisesRegex(module.RestoreBlocked, "^disposable_database_cleanup_failed$"):
            with module.disposable_database("b" * 64, {}, "crown_restore_123_2", {}, action=action):
                pass

    def test_preexisting_target_is_never_dropped(self):
        calls = []
        def action(container, env, command):
            calls.append(command)
            return b"1\n"
        with self.assertRaisesRegex(module.RestoreBlocked, "restore_database_already_exists"):
            with module.disposable_database("b" * 64, {}, "crown_restore_123_2", {}, action=action):
                pass
        self.assertEqual(len(calls), 1)

    def test_uncertain_create_failure_still_attempts_scoped_cleanup(self):
        calls = []
        def action(container, env, command):
            calls.append(command)
            if command[0] == "createdb":
                raise module.RestoreBlocked("postgres_process_failed")
            return b"0\n"
        evidence = {}
        with self.assertRaises(module.RestoreBlocked):
            with module.disposable_database("b" * 64, {}, "crown_restore_123_2", evidence, action=action):
                pass
        self.assertEqual(calls[-1][0], "dropdb")
        self.assertTrue(evidence["disposable_database_dropped"])

    def test_integrity_mismatch_fails_and_runs_cleanup(self):
        @contextmanager
        def scope(*args):
            yield
            raise AssertionError("should propagate mismatch")
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "backup.dump"
            archive.write_bytes(b"fake")
            with patch.object(module, "disposable_database", scope), patch.object(module, "execute"), \
                 patch.object(module, "target_facts", return_value=({"x": 2}, [], [], 1)):
                with self.assertRaisesRegex(module.RestoreBlocked, "restored_snapshot_integrity_mismatch"):
                    module.restore_archive("b" * 64, {}, "crown_restore_123_2", archive,
                                           ("snapshot", {"x": 1}, [], [], 160015), {})

    def test_main_failure_evidence_never_contains_exception_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.json"
            with patch.dict(module.os.environ, ENV, clear=True), \
                 patch.object(module, "verify_accepted_source"), \
                 patch.object(module, "perform", side_effect=RuntimeError("PRIVATE")):
                result = module.main(["--expected-sha", SHA, "--confirmation", module.CONFIRMATION,
                                      "--synthetic-dev-confirmed", "true", "--evidence-path", str(path)])
            self.assertEqual(result, 1)
            text = path.read_text()
            self.assertNotIn("PRIVATE", text)
            self.assertEqual(json.loads(text)["result"], "BLOCKED")

    def test_workflow_never_uploads_archive_or_creates_azure_resources(self):
        path = Path(__file__).resolve().parents[2] / ".github/workflows/isolated-postgres-restore-drill.yml"
        workflow = path.read_text().split("  dev-operational-restore:", 1)[1].split("  restore-drill:", 1)[0]
        self.assertIn("path: ${{ runner.temp }}/dev-restore-evidence.json", workflow)
        self.assertNotIn("latest.dump", workflow)
        self.assertNotIn("az postgres", workflow)
        self.assertIn("synthetic-dev-confirmed", workflow)
        self.assertIn("before Azure login", workflow)

    @unittest.skipUnless(os.environ.get("CROWN_RESTORE_TEST_CONTAINER"), "requires disposable CI PostgreSQL")
    def test_real_disposable_postgres_dump_restore_and_corruption_cleanup(self):
        container = os.environ["CROWN_RESTORE_TEST_CONTAINER"]
        env = module.target_environment(os.environ)
        module.target_identity(container, env)
        source_db, restore_db = "crown_restore_1_1", "crown_restore_1_2"
        with module.disposable_database(container, env, source_db, {}):
            module.scalar(container, env, source_db,
                "CREATE TABLE core_school(id integer PRIMARY KEY); "
                "CREATE TABLE core_useraccount(id integer PRIMARY KEY, school_id integer REFERENCES core_school); "
                "CREATE TABLE django_migrations(app text, name text); "
                "INSERT INTO core_school VALUES (1),(2); "
                "INSERT INTO core_useraccount VALUES (1,1); "
                "INSERT INTO django_migrations VALUES ('fixture','0001_initial');")
            counts = {"core_school": 2, "core_useraccount": 1, "django_migrations": 1}
            actual_counts, columns, migrations, _ = module.target_facts(container, env, source_db, counts)
            facts = ("fixture", actual_counts, columns, migrations, 160000)
            with tempfile.TemporaryDirectory() as directory:
                archive = Path(directory) / "fixture.dump"
                with archive.open("wb") as output:
                    module.execute(container, env, ["pg_dump", "--dbname", source_db,
                                   "--format=custom", "--no-owner", "--no-acl"], stdout=output)
                evidence = {}
                module.restore_archive(container, env, restore_db, archive, facts, evidence)
                self.assertTrue(evidence["row_counts_match"])
                self.assertTrue(evidence["column_definitions_match"])
                self.assertTrue(evidence["migration_history_match"])
                self.assertTrue(evidence["disposable_database_dropped"])
                archive.write_bytes(b"corrupt archive")
                failed = {}
                with self.assertRaises(module.RestoreBlocked):
                    module.restore_archive(container, env, restore_db, archive, facts, failed)
                self.assertTrue(failed["disposable_database_dropped"])


if __name__ == "__main__":
    unittest.main()
