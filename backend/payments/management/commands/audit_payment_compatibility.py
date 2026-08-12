from django.core.management.base import BaseCommand, CommandError

from payments.compatibility_audit import audit_payment_compatibility


class Command(BaseCommand):
    help = "Audit canonical Payments facts against Finance compatibility rows."

    def add_arguments(self, parser):
        parser.add_argument(
            "--school-id",
            dest="school_id",
            help="Optional school UUID to audit instead of all schools.",
        )
        parser.add_argument(
            "--allow-orphans",
            action="store_true",
            help="Report legacy-only FinancePayment rows without failing the command.",
        )

    def handle(self, *args, **options):
        result = audit_payment_compatibility(school_id=options.get("school_id"))

        self.stdout.write(
            f"checked_payments={result.checked_payments} "
            f"checked_refunds={result.checked_refunds} "
            f"mismatches={len(result.mismatches)} "
            f"orphan_legacy_payments={len(result.orphan_legacy_payments)}"
        )
        for mismatch in result.mismatches:
            self.stdout.write(f"MISMATCH {mismatch}")
        for legacy_id in result.orphan_legacy_payments:
            self.stdout.write(f"ORPHAN FinancePayment:{legacy_id}")

        has_blocking_orphans = (
            bool(result.orphan_legacy_payments) and not options["allow_orphans"]
        )
        if result.mismatches or has_blocking_orphans:
            raise CommandError(
                "Payment compatibility audit failed; legacy authority retirement is not safe."
            )

        self.stdout.write(self.style.SUCCESS("Payment compatibility audit PASS"))
