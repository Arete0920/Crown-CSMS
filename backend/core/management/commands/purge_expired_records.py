"""
Management command: purge_expired_records

Runs the retention purge service and reports results to stdout.

Usage
-----
    python manage.py purge_expired_records

Cron (daily at 02:00 UTC):
    0 2 * * * /app/.venv/bin/python /app/manage.py purge_expired_records
"""
from django.core.management.base import BaseCommand

from core.services.retention_service import purge_expired_records


class Command(BaseCommand):
    help = "Purge records that have exceeded their configured retention window."

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting retention purge...")
        results = purge_expired_records()

        total_deleted = 0
        for r in results:
            if r["skipped_reason"]:
                self.stdout.write(
                    self.style.WARNING(
                        f"  SKIP  {r['model']}: {r['skipped_reason']}"
                    )
                )
            else:
                total_deleted += r["deleted"]
                self.stdout.write(
                    f"  PURGE {r['model']}: {r['deleted']} records deleted"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Retention purge complete. Total deleted: {total_deleted}"
            )
        )
