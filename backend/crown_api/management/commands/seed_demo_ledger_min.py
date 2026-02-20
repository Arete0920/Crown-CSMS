"""
Phase 3 P3: Minimum ledger seed for the runtime proof ceremony.

Seeds exactly:
  - 1 Household  (name="Demo Household (proof)", school_id=<demo school>)
  - 1 LedgerAccount  (linked to that household)
  - 1 Charge  (amount=100.00, description="Demo Charge (proof)")

Uses get_or_create everywhere — safe to run multiple times.
Resolves the demo school UUID the same way proof_phase3_runtime does:
  School.objects.get(name="Crown Demo Christian Academy")
"""
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


DEMO_SCHOOL_NAME = "Crown Demo Christian Academy"
DEMO_HOUSEHOLD_NAME = "Demo Household (proof)"
DEMO_CHARGE_DESC = "Demo Charge (proof)"


class Command(BaseCommand):
    help = "Seeds minimum ledger entities for the Phase 3 runtime proof ceremony."

    def add_arguments(self, parser):
        parser.add_argument("--verbose", action="store_true", help="Print debug info")

    @transaction.atomic
    def handle(self, *args, **opts):
        verbose = bool(opts.get("verbose"))

        # Resolve demo school — must exist (seed_demo_school runs before this)
        from core.models import School
        try:
            school = School.objects.get(name=DEMO_SCHOOL_NAME)
        except School.DoesNotExist:
            raise CommandError(
                f"Demo school '{DEMO_SCHOOL_NAME}' not found. "
                "Run seed_demo_school --wipe first."
            )
        school_id = school.id
        if verbose:
            self.stdout.write(f"seed_demo_ledger_min: school_id={school_id}")

        # 1. Household
        from households.models import Household
        hh, hh_created = Household.objects.get_or_create(
            school_id=school_id,
            name=DEMO_HOUSEHOLD_NAME,
        )
        if verbose:
            flag = "created" if hh_created else "exists"
            self.stdout.write(f"seed_demo_ledger_min: household {flag} pk={hh.pk}")

        # 2. LedgerAccount
        from ledger.models import LedgerAccount
        acct, acct_created = LedgerAccount.objects.get_or_create(
            school_id=school_id,
            household=hh,
        )
        if verbose:
            flag = "created" if acct_created else "exists"
            self.stdout.write(f"seed_demo_ledger_min: ledger_account {flag} pk={acct.pk}")

        # 3. Charge — only create if none exist for this account yet
        from ledger.models import Charge
        if not Charge.objects.filter(school_id=school_id, account=acct).exists():
            Charge.objects.create(
                school_id=school_id,
                account=acct,
                description=DEMO_CHARGE_DESC,
                amount=Decimal("100.00"),
            )
            if verbose:
                self.stdout.write("seed_demo_ledger_min: charge created")
        elif verbose:
            self.stdout.write("seed_demo_ledger_min: charge exists")

        self.stdout.write(
            self.style.SUCCESS(
                f"seed_demo_ledger_min: OK  household_id={hh.pk}"
            )
        )
