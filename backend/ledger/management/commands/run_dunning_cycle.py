"""
Management command: run_dunning_cycle

Processes all DunningRecords that are due for retry.

Usage:
    python manage.py run_dunning_cycle

Cron (every 30 minutes):
    */30 * * * * /app/.venv/bin/python /app/manage.py run_dunning_cycle
"""
from django.core.management.base import BaseCommand

from ledger.services_dunning import process_failed_payments


class Command(BaseCommand):
    help = "Process all overdue failed payment retry records (dunning cycle)."

    def handle(self, *args, **options):
        self.stdout.write("Starting dunning cycle...")
        result = process_failed_payments()
        self.stdout.write(
            self.style.SUCCESS(
                f"Dunning cycle complete — "
                f"retried: {result['retried']}, "
                f"delinquent: {result['delinquent']}, "
                f"skipped: {result['skipped']}"
            )
        )
        if result["delinquent"] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"  ⚠  {result['delinquent']} payment(s) escalated to DELINQUENT"
                )
            )
