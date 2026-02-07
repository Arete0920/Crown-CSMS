"""
Temporary management command to fix financial_aid schema drift.
Deletes financial_aid migration ledger entries, then re-migrates.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command


class Command(BaseCommand):
    help = "Fix financial_aid schema drift: delete ledger, re-migrate"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write("\n=== BEFORE: Migration Ledger ===")
            cursor.execute(
                "SELECT app, name FROM django_migrations WHERE app = 'financial_aid' ORDER BY applied;"
            )
            before_rows = cursor.fetchall()
            if before_rows:
                for app, name in before_rows:
                    self.stdout.write(f"  - {app}/{name}")
            else:
                self.stdout.write("  (no financial_aid migrations)")

            self.stdout.write("\n=== STEP B.1: Delete Financial Aid Ledger Entries ===")
            cursor.execute("DELETE FROM django_migrations WHERE app = 'financial_aid';")
            deleted_count = cursor.rowcount
            self.stdout.write(f"✓ Deleted {deleted_count} migration ledger entry(ies)")

        self.stdout.write("\n=== STEP B.2: Re-run Migrations ===")
        call_command("migrate", "financial_aid", verbosity=2, interactive=False)

        with connection.cursor() as cursor:
            self.stdout.write("\n=== AFTER: Migration Ledger ===")
            cursor.execute(
                "SELECT app, name FROM django_migrations WHERE app = 'financial_aid' ORDER BY applied;"
            )
            after_rows = cursor.fetchall()
            if after_rows:
                for app, name in after_rows:
                    self.stdout.write(f"  - {app}/{name}")
            else:
                self.stdout.write("  (no financial_aid migrations)")

            self.stdout.write("\n=== STEP B.3: Verify Table Exists ===")
            cursor.execute("SELECT to_regclass('public.financial_aid_financialaidapplication') AS fa_table;")
            row = cursor.fetchone()
            fa_table = row[0] if row else None
            
            if fa_table:
                self.stdout.write(f"✓ Table exists: {fa_table}")
            else:
                self.stdout.write("❌ Table STILL missing after migration")

        self.stdout.write("\n=== SCHEMA DRIFT FIX COMPLETE ===")
