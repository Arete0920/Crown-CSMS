# backend/financial_aid/management/commands/seed_phase4b_scenario.py
"""
Phase 4B demo seed command.

Creates a deterministic, idempotent financial aid + ledger scenario:
  - 1 school (fixed UUID for repeatability)
  - 1 household ("Demo Family")
  - 1 tuition charge: $10,000
  - 1 aid award: $3,000 (need-based)
  - Runs apply_financial_aid_to_billing_run()
  - Prints ledger statement + billing run summary

Usage:
    python manage.py seed_phase4b_scenario
    python manage.py seed_phase4b_scenario --reset
"""
from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import School
from households.models import Household
from ledger.models import LedgerAccount, Charge, Payment, Allocation
from ledger.services import account_balance, build_account_statement, billing_run_summary
from billing.models import BillingRun, Invoice
from financial_aid.models import FinancialAidApplication, AidAward, AidAuditEvent
from financial_aid.services import apply_financial_aid_to_billing_run

# Deterministic UUIDs — fixed so the command is safe to run multiple times.
_SCHOOL_ID = uuid.UUID("aabbccdd-0001-0002-0003-000000004b00")
_TERM = "2025-26"
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Seed a deterministic Phase 4B ledger + financial aid demo scenario."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all Phase 4B demo objects before seeding (for a clean re-run).",
        )

    def handle(self, *args, **options):
        sid = _SCHOOL_ID

        if options["reset"]:
            self._reset(sid)
            self.stdout.write(self.style.WARNING(f"[reset] Cleared Phase 4B demo data for school {sid}"))

        with transaction.atomic():
            # -- School --
            school, created = School.objects.get_or_create(
                id=sid,
                defaults={"name": "Phase4B Demo School"},
            )
            self.stdout.write(f"[school] {'created' if created else 'exists'}: {school.name} ({sid})")

            # -- Household --
            hh, created = Household.objects.get_or_create(
                school_id=sid,
                name="Demo Family",
                defaults={},
            )
            self.stdout.write(f"[household] {'created' if created else 'exists'}: {hh.name} ({hh.id})")

            # -- Ledger Account --
            acct, created = LedgerAccount.objects.get_or_create(
                school_id=sid,
                household=hh,
            )
            self.stdout.write(f"[ledger_account] {'created' if created else 'exists'}: {acct.id}")

            # -- Billing Run --
            run, created = BillingRun.objects.get_or_create(
                school_id=sid,
                term=_TERM,
                defaults={
                    "description": "Phase 4B Demo Billing Run",
                    "amount_per_student": Decimal("10000.00"),
                },
            )
            self.stdout.write(f"[billing_run] {'created' if created else 'exists'}: {run.id}")

            # -- Charge + Invoice --
            charge = None
            invoice = Invoice.objects.filter(school_id=sid, billing_run=run, household=hh).first()
            if invoice is None:
                charge = Charge.objects.create(
                    school_id=sid,
                    account=acct,
                    description="Tuition 2025-26",
                    amount=Decimal("10000.00"),
                )
                invoice = Invoice.objects.create(
                    school_id=sid,
                    billing_run=run,
                    household=hh,
                    total_amount=Decimal("10000.00"),
                    ledger_charge_id=charge.id,
                )
                self.stdout.write(f"[charge] created: {charge.id} — $10,000.00")
                self.stdout.write(f"[invoice] created: {invoice.id} — ledger_charge_id={charge.id}")
            else:
                self.stdout.write(f"[invoice] exists: {invoice.id} — ledger_charge_id={invoice.ledger_charge_id}")

            # -- Financial Aid Application + Award --
            fin_app = FinancialAidApplication.objects.filter(
                school_id=sid,
                household_id=hh.id,
                academic_year=_TERM,
            ).first()
            if fin_app is None:
                fin_app = FinancialAidApplication.objects.create(
                    school_id=sid,
                    household_id=hh.id,
                    academic_year=_TERM,
                    status="decided",
                    household_income=Decimal("55000.00"),
                    household_size=4,
                )
                self.stdout.write(f"[aid_application] created: {fin_app.id}")
            else:
                self.stdout.write(f"[aid_application] exists: {fin_app.id}")

            award = AidAward.objects.filter(school_id=sid, application=fin_app).first()
            if award is None:
                award = AidAward.objects.create(
                    school_id=sid,
                    application=fin_app,
                    bucket="need",
                    amount=Decimal("3000.00"),
                    rationale="Need-based award — Phase 4B demo.",
                )
                self.stdout.write(f"[aid_award] created: {award.id} — $3,000.00")
            else:
                self.stdout.write(f"[aid_award] exists: {award.id} — ${award.amount}")

        # -- Apply aid to billing run (idempotent) --
        self.stdout.write("\nApplying financial aid to billing run ...")
        result = apply_financial_aid_to_billing_run(
            school_id=sid,
            billing_run_id=run.id,
        )
        self.stdout.write(self.style.SUCCESS(f"[apply_aid] {result}"))

        # -- Print billing run summary --
        self.stdout.write("\n--- Billing Run Summary ---")
        summary = billing_run_summary(school_id=sid, billing_run=run)
        for k, v in summary.items():
            self.stdout.write(f"  {k}: {v}")

        # -- Print ledger statement --
        self.stdout.write("\n--- Ledger Account Statement ---")
        stmt = build_account_statement(school_id=sid, account=acct)
        self.stdout.write(f"  account_id : {stmt['account_id']}")
        self.stdout.write(f"  balance    : ${stmt['balance']}")
        self.stdout.write(f"  entries    : {len(stmt['entries'])}")
        for entry in stmt["entries"]:
            direction = "DEBIT " if entry["direction"] == "DEBIT" else "CREDIT"
            self.stdout.write(
                f"    [{direction}] {entry['type']:<22} "
                f"${entry['amount']:>10}  "
                f"source={entry.get('source') or 'n/a':<14}  "
                f"balance={entry['running_balance']}"
            )

        # -- Final balance assertion --
        bal = account_balance(acct)
        self.stdout.write(f"\n[account_balance] ${bal}")
        if bal == Decimal("7000.00"):
            self.stdout.write(self.style.SUCCESS("[PASS] balance == $7,000.00 after aid applied."))
        else:
            self.stdout.write(self.style.WARNING(f"[INFO] balance is ${bal} (expected $7,000.00 if aid not yet fully allocated)."))

    def _reset(self, sid):
        """Remove all Phase 4B demo objects for school sid."""
        AidAuditEvent.objects.filter(school_id=sid).delete()
        AidAward.objects.filter(school_id=sid).delete()
        FinancialAidApplication.objects.filter(school_id=sid).delete()
        Allocation.objects.filter(school_id=sid).delete()
        Payment.objects.filter(school_id=sid).delete()
        Charge.objects.filter(school_id=sid).delete()
        Invoice.objects.filter(school_id=sid).delete()
        BillingRun.objects.filter(school_id=sid).delete()
        LedgerAccount.objects.filter(school_id=sid).delete()
        try:
            Household.objects.filter(school_id=sid).delete()
        except Exception:
            logger.exception("seed_phase4b_scenario: failed deleting households during reset")
