from __future__ import annotations

import json
import os
import subprocess
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase


MODULE = "crown_api.management.commands.verify_backup_restore"
STARTED_AT = datetime(2026, 7, 20, 1, 0, tzinfo=timezone.utc)


class VerifyBackupRestoreCommandTests(SimpleTestCase):
    def _backup(self, directory: str, *, age_hours: float = 0.25) -> Path:
        path = Path(directory) / "latest.dump"
        path.write_bytes(b"postgres-custom-format-placeholder")
        modified = STARTED_AT.timestamp() - (age_hours * 3600)
        os.utime(path, (modified, modified))
        return path

    @patch(f"{MODULE}.shutil.which", return_value="/usr/bin/tool")
    @patch(f"{MODULE}._utc_now", return_value=STARTED_AT)
    def test_rejects_backup_older_than_configured_rpo(self, _now, _which):
        with self.settings(CROWN_RPO_HOURS=1), self.subTest("stale backup"):
            from tempfile import TemporaryDirectory

            with TemporaryDirectory() as directory:
                backup = self._backup(directory, age_hours=2)
                with self.assertRaisesMessage(CommandError, "RPO window"):
                    call_command("verify_backup_restore", backup_path=str(backup))

    @patch(f"{MODULE}.shutil.which", return_value="/usr/bin/tool")
    @patch(f"{MODULE}._utc_now", return_value=STARTED_AT)
    def test_rejects_unsafe_required_table_identifier(self, _now, _which):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            backup = self._backup(directory)
            with self.assertRaisesMessage(CommandError, "simple PostgreSQL identifiers"):
                call_command(
                    "verify_backup_restore",
                    backup_path=str(backup),
                    required_tables=["django_migrations; DROP DATABASE crown"],
                )

    @patch(f"{MODULE}.time.monotonic", side_effect=[100.0, 112.5])
    @patch(f"{MODULE}._utc_now", side_effect=[STARTED_AT, STARTED_AT])
    @patch(f"{MODULE}.shutil.which", return_value="/usr/bin/tool")
    @patch(f"{MODULE}.subprocess.run")
    def test_records_structural_restore_evidence_and_cleans_up(
        self,
        run,
        _which,
        _now,
        _monotonic,
    ):
        from tempfile import TemporaryDirectory

        def completed(stdout: bytes = b""):
            return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr=b"")

        run.side_effect = [
            completed(),
            completed(),
            completed(),
            completed(b"12\n"),
            completed(b"1\n"),
            completed(b"345\n"),
            completed(),
        ]

        with TemporaryDirectory() as directory:
            backup = self._backup(directory)
            evidence = Path(directory) / "evidence" / "restore.json"

            call_command(
                "verify_backup_restore",
                backup_path=str(backup),
                evidence_path=str(evidence),
                verbosity=0,
            )

            payload = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(payload["result"], "PASS")
            self.assertTrue(payload["archive_preflight_passed"])
            self.assertTrue(payload["temporary_database_created"])
            self.assertTrue(payload["temporary_database_dropped"])
            self.assertFalse(payload["production_database_mutated"])
            self.assertEqual(payload["public_table_count"], 12)
            self.assertEqual(payload["django_migration_count"], 345)
            self.assertEqual(payload["elapsed_seconds"], 12.5)
            self.assertEqual(run.call_args_list[-1].args[0][0], "dropdb")

    def test_process_errors_redact_postgres_passwords(self):
        from crown_api.management.commands.verify_backup_restore import _safe_process_error

        password = "super" + "-secret"
        error_url = f"postgresql://operator:{password}@db.example/crown failed"
        error = subprocess.CalledProcessError(
            1,
            ["pg_restore"],
            stderr=error_url.encode(),
        )
        result = _safe_process_error(error)
        self.assertNotIn(password, result)
        self.assertIn("operator:***@db.example", result)


class IsolatedRestoreEvidencePacketTests(SimpleTestCase):
    RESTORE = {
        "result": "PASS", "archive_preflight_passed": True,
        "temporary_database_created": True, "temporary_database_dropped": True,
        "production_database_mutated": False,
    }
    EXECUTION = {
        "result": "PASS", "database_engine": "postgresql", "postgresql_version_num": 160004,
        "source_database": "crown_source", "test_database": "test_crown_source",
        "normal_migrations": True, "pytest_exit_code": 0,
        "test_database_dropped": True, "source_database_still_present": True,
    }
    JUNIT = (
        '<testsuites><testsuite tests="1" errors="0" failures="0" skipped="0">'
        '<testcase classname="backend.crm_marketing.tests.test_inquiry_capture" '
        'name="test_pre_inquiry_model_can_insert_after_inquiry_migration" />'
        '</testsuite></testsuites>'
    )

    def _assemble(self, *, restore=RESTORE, execution=EXECUTION, junit=JUNIT, outcome="success"):
        from tempfile import TemporaryDirectory

        workflow = (Path(__file__).resolve().parents[2] / ".github/workflows/isolated-postgres-restore-drill.yml").read_text()
        step = workflow.split("      - name: Assemble evidence packet\n", 1)[1]
        source = step.split("          python - <<'PY'\n", 1)[1].split("\n          PY\n", 1)[0]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            if restore is not None:
                (root / "restore-evidence.json").write_text(json.dumps(restore))
            if execution is not None:
                (root / "inquiry-legacy-insert-execution.json").write_text(json.dumps(execution))
            if junit is not None:
                (root / "inquiry-legacy-insert.xml").write_text(junit)
            with patch.dict(os.environ, {
                "EVIDENCE_DIR": directory, "INQUIRY_COMPATIBILITY_OUTCOME": outcome,
                "GITHUB_SHA": "a" * 40,
            }, clear=True):
                exec(compile(textwrap.dedent(source), str(root / "assemble.py"), "exec"), {"__name__": "__main__"})
            return json.loads((root / "retained-recovery-evidence.json").read_text())

    def test_requires_restore_and_exact_unskipped_postgres_legacy_insert_proof(self):
        packet = self._assemble()
        self.assertEqual(packet["result"], "PASS")
        self.assertEqual(packet["schema_version"], 2)
        self.assertEqual(packet["restore"], self.RESTORE)
        self.assertEqual(packet["inquiry_legacy_insert"]["execution"], self.EXECUTION)
        self.assertEqual(packet["inquiry_legacy_insert"]["junit"]["case_count"], 1)
        self.assertFalse(packet["production_mutation_performed"])

        for change in [None, {"result": "FAIL"}, {"archive_preflight_passed": False},
                       {"temporary_database_created": False}, {"temporary_database_dropped": False},
                       {"production_database_mutated": True}]:
            restore = None if change is None else {**self.RESTORE, **change}
            with self.subTest(restore=restore):
                self.assertEqual(self._assemble(restore=restore)["result"], "FAIL")

    def test_missing_failed_skipped_or_different_junit_cannot_pass_with_restore_alone(self):
        cases = [
            None, "<broken", "<testsuites />",
            self.JUNIT.replace(" />", "><failure /></testcase>"),
            self.JUNIT.replace(" />", "><error /></testcase>"),
            self.JUNIT.replace(" />", "><skipped /></testcase>"),
            self.JUNIT.replace('failures="0"', 'failures="1"'),
            self.JUNIT.replace('errors="0"', 'errors="1"'),
            self.JUNIT.replace('skipped="0"', 'skipped="1"'),
            self.JUNIT.replace('tests="1"', 'tests="0"'),
            self.JUNIT.replace("test_pre_inquiry_model_can_insert_after_inquiry_migration", "unrelated_test"),
            self.JUNIT.replace("backend.crm_marketing.tests.test_inquiry_capture", "unrelated_module"),
            self.JUNIT.replace("</testsuite>", '<testcase name="extra" /></testsuite>'),
        ]
        for junit in cases:
            with self.subTest(junit=junit):
                packet = self._assemble(junit=junit)
                self.assertEqual(packet["result"], "FAIL")
                self.assertEqual(packet["inquiry_legacy_insert"]["result"], "FAIL")

    def test_runner_database_or_cleanup_failure_cannot_pass_with_passing_junit(self):
        for change in [None, {"result": "FAIL"}, {"database_engine": "sqlite"},
                       {"postgresql_version_num": 150000}, {"source_database": "other"},
                       {"test_database": "crown_source"}, {"normal_migrations": False},
                       {"pytest_exit_code": 1}, {"test_database_dropped": False},
                       {"source_database_still_present": False}]:
            execution = None if change is None else {**self.EXECUTION, **change}
            with self.subTest(execution=execution):
                self.assertEqual(self._assemble(execution=execution)["result"], "FAIL")
        for outcome in ("failure", "skipped", "cancelled", ""):
            with self.subTest(outcome=outcome):
                self.assertEqual(self._assemble(outcome=outcome)["result"], "FAIL")
