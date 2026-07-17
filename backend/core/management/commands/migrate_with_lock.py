from __future__ import annotations

import time
from contextlib import contextmanager

from django.core.management import BaseCommand, CommandError, call_command
from django.db import connection


LOCK_ID = 2026071701


class Command(BaseCommand):
    help = "Run Django migrations under a database-level advisory lock."

    def add_arguments(self, parser):
        parser.add_argument(
            "--lock-timeout-seconds",
            type=int,
            default=300,
            help="Maximum time to wait for the PostgreSQL advisory lock.",
        )
        parser.add_argument(
            "--allow-non-postgresql",
            action="store_true",
            help="Allow execution without an advisory lock for local/CI proof only.",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            help="Check for pending migrations without applying them.",
        )

    def handle(self, *args, **options):
        timeout_seconds = options["lock_timeout_seconds"]
        if timeout_seconds < 0:
            raise CommandError("--lock-timeout-seconds must be zero or greater")

        with self._migration_lock(
            timeout_seconds=timeout_seconds,
            allow_non_postgresql=options["allow_non_postgresql"],
        ):
            self.stdout.write(
                self.style.NOTICE(
                    f"schema migration authority acquired; vendor={connection.vendor}"
                )
            )
            call_command(
                "migrate",
                interactive=False,
                check=options["check"],
                verbosity=options.get("verbosity", 1),
            )
            self.stdout.write(self.style.SUCCESS("schema migration stage completed"))

    @contextmanager
    def _migration_lock(self, *, timeout_seconds: int, allow_non_postgresql: bool):
        if connection.vendor != "postgresql":
            if not allow_non_postgresql:
                raise CommandError(
                    "migrate_with_lock requires PostgreSQL advisory locking. "
                    "Use --allow-non-postgresql only for local or CI proof."
                )
            self.stdout.write(
                self.style.WARNING(
                    "non-PostgreSQL proof mode: database advisory lock is not active"
                )
            )
            yield
            return

        deadline = time.monotonic() + timeout_seconds
        acquired = False

        with connection.cursor() as cursor:
            while True:
                cursor.execute("SELECT pg_try_advisory_lock(%s)", [LOCK_ID])
                acquired = bool(cursor.fetchone()[0])
                if acquired:
                    break
                if time.monotonic() >= deadline:
                    raise CommandError(
                        "Timed out waiting for the production schema migration lock"
                    )
                time.sleep(1)

            try:
                yield
            finally:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [LOCK_ID])
                released = bool(cursor.fetchone()[0])
                if not released:
                    raise CommandError(
                        "Production schema migration lock was not released cleanly"
                    )
