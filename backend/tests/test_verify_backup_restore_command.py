from __future__ import annotations

import json
import os
import subprocess
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
