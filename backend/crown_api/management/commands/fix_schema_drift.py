"""
Temporary management command to fix financial_aid schema drift.
Deletes financial_aid + dependent academics migration ledger entries, then re-migrates.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command


class Command(BaseCommand):
    help = "Fix financial_aid schema drift: delete ledgers (financial_aid + academics), re-migrate"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write("\n=== BEFORE: Migration Ledger ===")
            
            # Check financial_aid
            cursor.execute(
                "SELECT app, name FROM django_migrations WHERE app = 'financial_aid' ORDER BY applied;"
            )
            fa_rows = cursor.fetchall()
            if fa_rows:
                self.stdout.write("financial_aid:")
                for app, name in fa_rows:
                    self.stdout.write(f"  - {name}")
            else:
                self.stdout.write("financial_aid: (none)")

            # Check academics
            cursor.execute(
                "SELECT app, name FROM django_migrations WHERE app = 'academics' ORDER BY applied;"
            )
            acad_rows = cursor.fetchall()
            if acad_rows:
                self.stdout.write("academics:")
                for app, name in acad_rows:
                    self.stdout.write(f"  - {name}")
            else:
                self.stdout.write("academics: (none)")

            self.stdout.write("\n=== STEP B.1: Delete Ledger Entries (financial_aid + academics) ===")
            
            # Delete financial_aid first
            cursor.execute("DELETE FROM django_migrations WHERE app = 'financial_aid';")
            fa_deleted = cursor.rowcount
            self.stdout.write(f"✓ Deleted {fa_deleted} financial_aid ledger entry(ies)")

            # Delete academics (to resolve dependency deadlock)
            cursor.execute("DELETE FROM django_migrations WHERE app = 'academics';")
            acad_deleted = cursor.rowcount
            self.stdout.write(f"✓ Deleted {acad_deleted} academics ledger entry(ies)")

        self.stdout.write("\n=== STEP B.2: Re-run Migrations (financial_aid → academics) ===")
        
        # Migrate financial_aid first (creates tables)
        self.stdout.write("Migrating financial_aid...")
        call_command("migrate", "financial_aid", verbosity=2, interactive=False)
        
        # Then migrate academics (resolves dependency)
        self.stdout.write("\nMigrating academics...")
        call_command("migrate", "academics", verbosity=2, interactive=False)

        with connection.cursor() as cursor:
            self.stdout.write("\n=== AFTER: Migration Ledger ===")
            
            cursor.execute(
                "SELECT app, name FROM django_migrations WHERE app IN ('financial_aid', 'academics') ORDER BY app, applied;"
            )
            after_rows = cursor.fetchall()
            if after_rows:
                for app, name in after_rows:
                    self.stdout.write(f"  - {app}/{name}")
            else:
                self.stdout.write("  (no migrations for financial_aid or academics)")

            self.stdout.write("\n=== STEP B.3: Verify Table Exists ===")
            cursor.execute("SELECT to_regclass('public.financial_aid_financialaidapplication') AS fa_table;")
            row = cursor.fetchone()
            fa_table = row[0] if row else None
            
            if fa_table:
                self.stdout.write(f"✓ financial_aid table exists: {fa_table}")
            else:
                self.stdout.write("❌ financial_aid table STILL missing after migration")

            cursor.execute("SELECT to_regclass('public.course') AS course_table;")
            row = cursor.fetchone()
            course_table = row[0] if row else None
            
            if course_table:
                self.stdout.write(f"✓ academics table exists: {course_table}")
            else:
                self.stdout.write("❌ academics table STILL missing after migration")

        self.stdout.write("\n=== SCHEMA DRIFT FIX COMPLETE ===")
