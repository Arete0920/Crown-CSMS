"""
Temporary management command to fix financial_aid schema drift.
Deletes financial_aid + dependent migration ledgers (academics, billing), then re-migrates in order.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command


def _run_sql(cursor, sql: str, params=None):
    exec_fn = getattr(cursor, "execute")
    return exec_fn(sql, [] if params is None else params)


class Command(BaseCommand):
    help = "Fix schema drift: delete ledgers (financial_aid→academics→billing), re-migrate"

    def handle(self, *args, **options):
        apps_to_fix = ["financial_aid", "academics", "billing"]

        with connection.cursor() as cursor:
            self.stdout.write("\n=== BEFORE: Migration Ledger ===")

            for app in apps_to_fix:
                _run_sql(
                    cursor,
                    "SELECT app, name FROM django_migrations WHERE app = %s ORDER BY applied;",
                    [app],
                )
                rows = cursor.fetchall()
                if rows:
                    self.stdout.write(f"{app}: {len(rows)} migration(s)")
                    for _, name in rows[:3]:  # Show first 3
                        self.stdout.write(f"  - {name}")
                    if len(rows) > 3:
                        self.stdout.write(f"  ... and {len(rows) - 3} more")
                else:
                    self.stdout.write(f"{app}: (none)")

            self.stdout.write("\n=== STEP B.1: Delete Ledger Entries (financial_aid→academics→billing) ===")

            total_deleted = 0
            for app in apps_to_fix:
                _run_sql(cursor, "DELETE FROM django_migrations WHERE app = %s;", [app])
                deleted = cursor.rowcount
                total_deleted += deleted
                self.stdout.write(f"✓ Deleted {deleted} {app} ledger entry(ies)")

            self.stdout.write(f"\nTotal deleted: {total_deleted} migration ledger entries")

        self.stdout.write("\n=== STEP B.2: Re-run Migrations (dependency order) ===")

        # Migrate in dependency order: financial_aid → academics → billing
        for app in apps_to_fix:
            self.stdout.write(f"\nMigrating {app}...")
            call_command("migrate", app, verbosity=2, interactive=False)

        with connection.cursor() as cursor:
            self.stdout.write("\n=== AFTER: Migration Ledger ===")

            _run_sql(
                cursor,
                "SELECT app, name FROM django_migrations"
                " WHERE app IN ('financial_aid', 'academics', 'billing')"
                " ORDER BY app, applied;"
            )
            after_rows = cursor.fetchall()
            if after_rows:
                current_app = None
                count = 0
                for app, name in after_rows:
                    if app != current_app:
                        if current_app:
                            self.stdout.write(f"{current_app}: {count} migration(s) applied")
                        current_app = app
                        count = 1
                    else:
                        count += 1
                if current_app:
                    self.stdout.write(f"{current_app}: {count} migration(s) applied")
            else:
                self.stdout.write("  (no migrations)")

            self.stdout.write("\n=== STEP B.3: Verify Tables Exist ===")

            tables_to_check = [
                ("financial_aid_financialaidapplication", "financial_aid"),
                ("course", "academics"),
                ("invoice", "billing"),
            ]

            for table_name, app_name in tables_to_check:
                # table_name is from hardcoded list above — safe to format here
                _run_sql(cursor, "SELECT to_regclass(%s) AS tbl;", [f"public.{table_name}"])
                row = cursor.fetchone()
                table = row[0] if row else None

                if table:
                    self.stdout.write(f"✓ {app_name} table exists: {table}")
                else:
                    self.stdout.write(f"❌ {app_name} table missing: {table_name}")

        self.stdout.write("\n=== SCHEMA DRIFT FIX COMPLETE ===")
