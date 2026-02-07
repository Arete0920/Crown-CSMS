"""
Temporary diagnostic command to check DB table vs Django migration state.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Check if financial_aid tables exist vs migration ledger"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Query 1: Does the table exist?
            cursor.execute(
                "SELECT to_regclass('public.financial_aid_financialaidapplication') AS fa_table;"
            )
            row = cursor.fetchone()
            fa_table = row[0] if row else None
            
            self.stdout.write(f"\n=== A.1: Table Existence Check ===")
            self.stdout.write(f"fa_table: {fa_table}")
            if fa_table is None:
                self.stdout.write("❌ Table does NOT exist in Postgres")
            else:
                self.stdout.write(f"✓ Table exists: {fa_table}")
            
            # Query 2: What does Django think?
            cursor.execute(
                """
                SELECT app, name, applied
                FROM django_migrations
                WHERE app = 'financial_aid'
                ORDER BY applied DESC;
                """
            )
            rows = cursor.fetchall()
            
            self.stdout.write(f"\n=== A.2: Django Migration Ledger ===")
            if not rows:
                self.stdout.write("⚠ No financial_aid migrations in django_migrations table")
            else:
                self.stdout.write(f"Found {len(rows)} migration(s) for financial_aid:")
                for app, name, applied in rows:
                    self.stdout.write(f"  - {app}/{name} (applied: {applied})")
            
            # Query 3: Confirm database connection
            cursor.execute(
                "SELECT current_database() AS db, inet_server_addr() AS server_ip, version();"
            )
            db_info = cursor.fetchone()
            self.stdout.write(f"\n=== Database Connection Info ===")
            self.stdout.write(f"Database: {db_info[0]}")
            self.stdout.write(f"Server IP: {db_info[1]}")
            self.stdout.write(f"Version: {db_info[2][:80]}...")
            
            # Summary
            self.stdout.write(f"\n=== DIAGNOSIS ===")
            if fa_table is None and len(rows) > 0:
                self.stdout.write("🔴 SCHEMA DRIFT: Migration ledger says 'applied' but table doesn't exist")
                self.stdout.write("FIX: DELETE FROM django_migrations WHERE app = 'financial_aid'; then re-migrate")
            elif fa_table is not None and len(rows) == 0:
                self.stdout.write("⚠ PARTIAL DRIFT: Table exists but no migration ledger")
                self.stdout.write("FIX: Fake applied migrations or re-sync")
            elif fa_table is None and len(rows) == 0:
                self.stdout.write("✓ CLEAN: No table, no migrations (expected for fresh DB)")
            else:
                self.stdout.write("✓ CONSISTENT: Table exists and migrations recorded")
