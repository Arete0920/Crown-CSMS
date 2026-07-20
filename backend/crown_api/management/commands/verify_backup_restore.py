from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


DEFAULT_REQUIRED_TABLES = ("django_migrations",)
TABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
POSTGRES_URL_SECRET = re.compile(r"(postgres(?:ql)?://[^:\s]+:)([^@\s]+)(@)", re.IGNORECASE)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_process_error(exc: subprocess.CalledProcessError) -> str:
    raw = (exc.stderr or exc.stdout or b"").decode(errors="replace").strip()
    redacted = POSTGRES_URL_SECRET.sub(r"\1***\3", raw)
    return redacted[-2000:] or f"command exited with status {exc.returncode}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(command, check=True, capture_output=True)


def _query_scalar(database: str, sql: str) -> int:
    result = _run(
        [
            "psql",
            "--dbname",
            database,
            "--no-psqlrc",
            "--set=ON_ERROR_STOP=1",
            "--tuples-only",
            "--no-align",
            "--command",
            sql,
        ]
    )
    value = result.stdout.decode(errors="replace").strip()
    try:
        return int(value)
    except ValueError as exc:
        raise CommandError(f"Restore validation returned a non-integer result: {value!r}") from exc


class Command(BaseCommand):
    help = "Restore the latest PostgreSQL backup to an isolated database and validate it."

    def add_arguments(self, parser):
        parser.add_argument(
            "--backup-path",
            default="/backups/latest.dump",
            help="Path to the PostgreSQL custom-format dump.",
        )
        parser.add_argument(
            "--max-backup-age-hours",
            type=float,
            default=None,
            help="Maximum accepted backup age; defaults to CROWN_RPO_HOURS.",
        )
        parser.add_argument(
            "--required-table",
            action="append",
            dest="required_tables",
            default=[],
            help="Public table that must exist after restore. May be repeated.",
        )
        parser.add_argument(
            "--minimum-public-table-count",
            type=int,
            default=1,
            help="Minimum number of restored public base tables.",
        )
        parser.add_argument(
            "--evidence-path",
            help="Optional JSON evidence output path.",
        )
        parser.add_argument(
            "--keep-temp-db-on-failure",
            action="store_true",
            help="Preserve the isolated database after a failed validation for investigation.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate inputs and print the planned commands without executing them.",
        )

    def handle(self, *args, **options):
        started_at = _utc_now()
        started_monotonic = time.monotonic()
        backup_path = Path(options["backup_path"]).expanduser().resolve()
        max_age_hours = options["max_backup_age_hours"]
        if max_age_hours is None:
            max_age_hours = float(getattr(settings, "CROWN_RPO_HOURS", 1))
        minimum_table_count = options["minimum_public_table_count"]
        required_tables = sorted(set(DEFAULT_REQUIRED_TABLES + tuple(options["required_tables"])))
        invalid_tables = [name for name in required_tables if not TABLE_NAME.fullmatch(name)]
        if invalid_tables:
            raise CommandError(
                "--required-table values must be simple PostgreSQL identifiers: "
                + ", ".join(invalid_tables)
            )
        keep_on_failure = options["keep_temp_db_on_failure"]
        dry_run = options["dry_run"]

        missing_tools = [
            tool
            for tool in ("createdb", "pg_restore", "psql", "dropdb")
            if shutil.which(tool) is None
        ]
        if missing_tools:
            raise CommandError("Missing required PostgreSQL client tools: " + ", ".join(missing_tools))

        if max_age_hours <= 0:
            raise CommandError("--max-backup-age-hours must be greater than zero.")
        if minimum_table_count < 1:
            raise CommandError("--minimum-public-table-count must be at least one.")
        if not backup_path.exists() or not backup_path.is_file():
            raise CommandError(f"Backup file does not exist: {backup_path}")

        stat = backup_path.stat()
        backup_modified_at = datetime.fromtimestamp(stat.st_mtime, timezone.utc)
        backup_age_hours = max(0.0, (started_at - backup_modified_at).total_seconds() / 3600)
        if backup_age_hours > max_age_hours:
            raise CommandError(
                f"Backup age {backup_age_hours:.2f}h exceeds the allowed {max_age_hours:.2f}h RPO window."
            )

        temp_db = f"crown_restore_{started_at.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        list_cmd = ["pg_restore", "--list", str(backup_path)]
        create_cmd = ["createdb", temp_db]
        restore_cmd = [
            "pg_restore",
            "--dbname",
            temp_db,
            "--exit-on-error",
            "--no-owner",
            str(backup_path),
        ]
        drop_cmd = ["dropdb", "--if-exists", temp_db]

        self.stdout.write(
            f"DR policy targets: RTO={getattr(settings, 'CROWN_RTO_HOURS', 4)}h "
            f"RPO={getattr(settings, 'CROWN_RPO_HOURS', 1)}h"
        )
        self.stdout.write(f"Backup: {backup_path} ({backup_age_hours:.2f}h old, {stat.st_size} bytes)")
        self.stdout.write(f"Isolated restore target: {temp_db}")

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] No database changes will be made."))
            for command in (list_cmd, create_cmd, restore_cmd, drop_cmd):
                self.stdout.write("  " + " ".join(command))
            return

        evidence = {
            "schema_version": 1,
            "result": "FAIL",
            "started_at_utc": started_at.isoformat(),
            "completed_at_utc": None,
            "elapsed_seconds": None,
            "backup_path": str(backup_path),
            "backup_size_bytes": stat.st_size,
            "backup_modified_at_utc": backup_modified_at.isoformat(),
            "backup_age_hours": round(backup_age_hours, 4),
            "max_backup_age_hours": max_age_hours,
            "backup_sha256": _sha256(backup_path),
            "temporary_database": temp_db,
            "archive_preflight_passed": False,
            "temporary_database_created": False,
            "required_tables": required_tables,
            "minimum_public_table_count": minimum_table_count,
            "public_table_count": None,
            "django_migration_count": None,
            "failure": None,
            "temporary_database_dropped": False,
            "production_database_mutated": False,
        }
        failure: Exception | None = None

        try:
            self.stdout.write("Validating PostgreSQL backup archive before database creation...")
            _run(list_cmd)
            evidence["archive_preflight_passed"] = True

            self.stdout.write("Creating isolated database...")
            _run(create_cmd)
            evidence["temporary_database_created"] = True

            self.stdout.write("Restoring backup with fail-fast PostgreSQL validation...")
            _run(restore_cmd)

            public_table_count = _query_scalar(
                temp_db,
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema='public' AND table_type='BASE TABLE';",
            )
            if public_table_count < minimum_table_count:
                raise CommandError(
                    f"Restore contains {public_table_count} public tables; expected at least {minimum_table_count}."
                )

            for table_name in required_tables:
                exists = _query_scalar(
                    temp_db,
                    "SELECT COUNT(*) FROM information_schema.tables "
                    f"WHERE table_schema='public' AND table_name='{table_name}' AND table_type='BASE TABLE';",
                )
                if exists != 1:
                    raise CommandError(f"Required restored table is missing: {table_name}")

            migration_count = _query_scalar(temp_db, "SELECT COUNT(*) FROM django_migrations;")
            if migration_count < 1:
                raise CommandError("Restored django_migrations table contains no applied migrations.")

            evidence["public_table_count"] = public_table_count
            evidence["django_migration_count"] = migration_count
            evidence["result"] = "PASS"
            self.stdout.write(self.style.SUCCESS("Isolated backup restore and structural validation passed."))

        except subprocess.CalledProcessError as exc:
            failure = CommandError(f"Restore drill command failed: {_safe_process_error(exc)}")
            evidence["failure"] = str(failure)
        except CommandError as exc:
            failure = exc
            evidence["failure"] = str(exc)
        finally:
            if evidence["temporary_database_created"]:
                if not (failure and keep_on_failure):
                    drop_result = subprocess.run(drop_cmd, check=False, capture_output=True)
                    evidence["temporary_database_dropped"] = drop_result.returncode == 0
                    if drop_result.returncode != 0:
                        cleanup_failure = CommandError("Cleanup of the isolated restore database failed.")
                        evidence["failure"] = "; ".join(
                            part for part in (evidence.get("failure"), str(cleanup_failure)) if part
                        )
                        evidence["result"] = "FAIL"
                        failure = CommandError(evidence["failure"])
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Preserving failed restore target for investigation: {temp_db}")
                    )

            completed_at = _utc_now()
            evidence["completed_at_utc"] = completed_at.isoformat()
            evidence["elapsed_seconds"] = round(time.monotonic() - started_monotonic, 3)

            evidence_path_value = options.get("evidence_path")
            if evidence_path_value:
                evidence_path = Path(evidence_path_value).expanduser()
                try:
                    evidence_path.parent.mkdir(parents=True, exist_ok=True)
                    evidence_path.write_text(
                        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    self.stdout.write(f"Evidence written to: {evidence_path}")
                except OSError as exc:
                    write_failure = CommandError(f"Unable to write restore evidence: {exc}")
                    evidence["failure"] = "; ".join(
                        part for part in (evidence.get("failure"), str(write_failure)) if part
                    )
                    evidence["result"] = "FAIL"
                    failure = CommandError(evidence["failure"])

            self.stdout.write(json.dumps(evidence, indent=2, sort_keys=True))

        if failure:
            raise failure
