"""
Management command: run_daily_payout_audit

Captures the daily expected-vs-actual payout snapshot for each school.

Usage:
    python manage.py run_daily_payout_audit
    python manage.py run_daily_payout_audit --school-id <uuid>

Cron (nightly at 01:00 UTC):
    0 1 * * * /app/.venv/bin/python /app/manage.py run_daily_payout_audit
"""
import uuid

from django.core.management.base import BaseCommand, CommandError

from ledger.services_reconciliation import record_daily_payout_audit
from ledger.models import LedgerAccount


class Command(BaseCommand):
    help = "Run the nightly payout verification audit for all active schools."

    def add_arguments(self, parser):
        parser.add_argument(
            "--school-id",
            type=str,
            default=None,
            help="Restrict audit to a single school UUID.",
        )

    def handle(self, *args, **options):
        school_id_arg = options.get("school_id")

        if school_id_arg:
            try:
                school_ids = [uuid.UUID(school_id_arg)]
            except ValueError as exc:
                raise CommandError(f"Invalid school-id: {school_id_arg}") from exc
        else:
            # Discover all active school IDs from LedgerAccount
            school_ids = list(
                LedgerAccount.objects.values_list("school_id", flat=True).distinct()
            )

        if not school_ids:
            self.stdout.write(self.style.WARNING("No schools found — nothing to audit."))
            return

        self.stdout.write(f"Running payout audit for {len(school_ids)} school(s)...")

        for sid in school_ids:
            audit = record_daily_payout_audit(school_id=sid)
            status = self.style.SUCCESS("✓ MATCH") if audit.verified else self.style.ERROR("✗ MISMATCH")
            self.stdout.write(
                f"  school={sid} date={audit.audit_date} "
                f"expected={audit.expected_total} actual={audit.actual_total} "
                f"variance={audit.variance} {status}"
            )

        self.stdout.write("Payout audit complete.")
