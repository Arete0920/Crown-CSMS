"""
Management command: verify_backup_restore

Runs a restore drill against the latest database backup.
Intended for quarterly DR verification.

Usage
-----
    python manage.py verify_backup_restore

Requirements
------------
- createdb and pg_restore must be on PATH (pg_client tools installed)
- /backups/latest.dump must exist (Azure Backup mount or local copy)
- The running user must have CREATEDB privilege on the Postgres server

Exit codes: 0 = pass, non-zero = failure (raises SystemExit via check=True)
"""
import datetime
import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = "Verify the latest DB backup can be restored to a temp database (DR drill)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--backup-path",
            default="/backups/latest.dump",
            help="Path to the .dump file to restore (default: /backups/latest.dump)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print commands that would be run without executing them.",
        )

    def handle(self, *args, **options):
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M")
        temp_db = f"restore_test_{timestamp}"
        backup_path = options["backup_path"]
        dry_run = options["dry_run"]

        rto = getattr(settings, "CROWN_RTO_HOURS", 4)
        rpo = getattr(settings, "CROWN_RPO_HOURS", 1)
        self.stdout.write(f"DR Policy — RTO: {rto}h | RPO: {rpo}h")
        self.stdout.write(f"Temp DB target : {temp_db}")
        self.stdout.write(f"Backup path    : {backup_path}")

        create_cmd = ["createdb", temp_db]
        restore_cmd = [
            "pg_restore",
            "--dbname", temp_db,
            "--no-owner",
            backup_path,
        ]
        drop_cmd = ["dropdb", "--if-exists", temp_db]

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] Would execute:"))
            self.stdout.write(f"  {' '.join(create_cmd)}")
            self.stdout.write(f"  {' '.join(restore_cmd)}")
            self.stdout.write(f"  {' '.join(drop_cmd)}")
            return

        try:
            self.stdout.write("Creating temp database...")
            subprocess.run(create_cmd, check=True, capture_output=True)

            self.stdout.write("Restoring latest backup...")
            subprocess.run(restore_cmd, check=True, capture_output=True)

            self.stdout.write(self.style.SUCCESS("Backup restore verified."))

        except subprocess.CalledProcessError as exc:
            raise CommandError(
                f"Restore drill failed: {exc.stderr.decode(errors='replace')}"
            ) from exc

        finally:
            # Always attempt cleanup — ignore errors here
            self.stdout.write("Dropping temp database...")
            subprocess.run(drop_cmd, check=False, capture_output=True)
