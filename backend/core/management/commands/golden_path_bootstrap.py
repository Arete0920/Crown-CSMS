from __future__ import annotations

import json
from datetime import date
from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = (
        "Create minimal Golden Path objects and print GP_* IDs for API-only smoke runs "
        "(safe for Azure; no remote shell from client required)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--school-name",
            default="GP School",
            help="School name to create if none exists.",
        )
        parser.add_argument(
            "--year-name",
            default="2026–2027",
            help="AcademicYear name to create if missing.",
        )
        parser.add_argument(
            "--award-cents",
            type=int,
            default=25000,
            help="AidAward awarded_cents (default: 25000 = $250.00).",
        )
        parser.add_argument(
            "--invoice-amount",
            default="250.00",
            help="Invoice and Charge amount (decimal dollars, default: 250.00).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        from aid.models import AidApplication, AidAward
        from billing.models import BillingRun, Invoice
        from core.models import AcademicYear, Family, School, Student
        from finance.models import ChartAccount
        from households.models import Household
        from ledger.models import Charge, LedgerAccount

        school = School.objects.order_by("created_at", "id").first()
        if not school:
            school = School.objects.create(
                name=str(options["school_name"])[:255],
                timezone="America/New_York",
                is_active=True,
            )

        academic_year = (
            AcademicYear.objects.filter(school=school)
            .order_by("-is_current", "-start_date", "id")
            .first()
        )
        if not academic_year:
            academic_year = AcademicYear.objects.create(
                school=school,
                name=str(options["year_name"])[:100],
                start_date=date(2026, 8, 15),
                end_date=date(2027, 6, 10),
                is_current=True,
            )

        family, _ = Family.objects.get_or_create(school=school, family_name="GP Family")
        student, _ = Student.objects.get_or_create(
            school=school,
            family=family,
            student_number="GP0001",
            defaults={"first_name": "Golden", "last_name": "Path", "dob": date(2010, 1, 1)},
        )

        ChartAccount.objects.get_or_create(
            school=school,
            code="AID",
            defaults={"name": "Financial Aid", "account_type": "EXPENSE", "is_active": True},
        )

        aid_app, _ = AidApplication.objects.get_or_create(
            school=school,
            academic_year=academic_year,
            family=family,
            defaults={"status": AidApplication.STATUS_NEEDS_INFO},
        )
        if aid_app.status != AidApplication.STATUS_NEEDS_INFO:
            aid_app.status = AidApplication.STATUS_NEEDS_INFO
            aid_app.save(update_fields=["status", "updated_at"])

        # Create a fresh accepted award so POST_ACCEPTED_AWARDS can demonstrate posting.
        # (If you reuse an already-posted award, the director action will be a no-op.)
        aid_award = AidAward.objects.create(
            school=school,
            academic_year=academic_year,
            student=student,
            awarded_cents=int(options["award_cents"]),
            decision_status=AidAward.DECISION_ACCEPTED,
        )

        household, _ = Household.objects.get_or_create(school_id=school.id, name="GP Household")
        ledger_acct, _ = LedgerAccount.objects.get_or_create(
            school_id=school.id,
            household=household,
        )

        run_id = datetime.now().strftime("%Y%m%d-%H%M%S")

        try:
            invoice_amount = Decimal(str(options["invoice_amount"])).quantize(Decimal("0.01"))
        except Exception:
            raise ValueError("--invoice-amount must be a decimal like 250.00")
        if invoice_amount <= 0:
            raise ValueError("--invoice-amount must be > 0")

        charge = Charge.objects.create(
            school_id=school.id,
            account=ledger_acct,
            description=f"GP Tuition Charge {run_id}",
            amount=invoice_amount,
        )

        # Term max_len is 24; this format is 23 chars: 2026-GP-YYYYMMDD-HHMMSS
        billing_run = BillingRun.objects.create(
            school_id=school.id,
            term=f"2026-GP-{run_id}",
            run_type="TUITION",
        )

        invoice = Invoice.objects.create(
            school_id=school.id,
            billing_run=billing_run,
            household=household,
            due_on=date.today(),
            total_amount=invoice_amount,
            ledger_charge_id=charge.id,
        )

        payload = {
            "school_id": str(school.id),
            "school_name": school.name,
            "year_id": str(academic_year.id),
            "year_name": academic_year.name,
            "aid_application_id": str(aid_app.id),
            "aid_award_id": str(aid_award.id),
            "invoice_id": str(invoice.id),
            "household_id": str(household.id),
            "ledger_charge_id": str(charge.id),
        }

        self.stdout.write(json.dumps(payload))
        self.stdout.write("")
        self.stdout.write("# PowerShell (copy/paste):")
        self.stdout.write(f'$env:GP_SCHOOL_ID="{payload["school_id"]}"')
        self.stdout.write(f'$env:GP_YEAR_ID="{payload["year_id"]}"')
        self.stdout.write(f'$env:GP_AID_AWARD_ID="{payload["aid_award_id"]}"')
        self.stdout.write(f'$env:GP_INVOICE_ID="{payload["invoice_id"]}"')
        self.stdout.write(f'$env:GP_AID_APP_ID="{payload["aid_application_id"]}"')
