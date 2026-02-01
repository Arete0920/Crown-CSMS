from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from applications.models import Application, Applicant, ApplicationEvent


def seed_admissions_funnel(*, school_id, academic_year_name=None):
    """
    Deterministic admissions funnel seed with realistic distribution.
    - 100 applicants with demo-ready stage progression
    - Distribution: 40% inquiry → 30% application_started → 20% submitted → 8% accepted → 2% enrolled
    - Events emitted for inquiry/tour/decision/enrollment where relevant
    """
    from households.models import Household

    # Avoid duplicates if rerun
    if Applicant.objects.filter(school_id=school_id).exists():
        return

    sources = [
        "church_referral", "facebook", "instagram", "google",
        "direct_mail_qr", "website", "word_of_mouth", "other",
    ]

    # Realistic funnel distribution (100 total)
    # 40 inquiry → 30 started → 20 submitted → 8 accepted → 2 enrolled
    stage_plan = (
        ["inquiry"] * 40 +
        ["application_started"] * 30 +
        ["application_submitted"] * 20 +
        ["accepted"] * 8 +
        ["enrolled"] * 2
    )

    # Minimal “flags” pattern
    def flags_for(i):
        if i == 7:
            return {"duplicate_suspected": True, "bot_suspected": False}
        if i == 13:
            return {"duplicate_suspected": False, "bot_suspected": True}
        return {"duplicate_suspected": False, "bot_suspected": False}

    # Application.status mapping baseline
    def app_status_for(stage):
        if stage in ("application_started", "inquiry"):
            return "DRAFT"
        if stage == "application_submitted":
            return "SUBMITTED"
        if stage in ("accepted", "enrolled"):
            return "DECIDED"
        return "DRAFT"

    # Decision payload mapping
    def decision_payload(stage):
        if stage == "accepted":
            return {"decision": "accepted"}
        if stage == "enrolled":
            return {"decision": "accepted"}
        return None

    for i in range(100):
        stage = stage_plan[i]
        source = sources[i % len(sources)]

        app = Application.objects.create(
            school_id=school_id,
            household=Household.objects.filter(school_id=school_id).first(),
            status=app_status_for(stage),
        )

        Applicant.objects.create(
            school_id=school_id,
            application=app,
            student=None,
            first_name=f"Student{i+1}",
            last_name="Applicant",
            grade_applying_for=str((i % 12) + 1),
            dob=None,
            source=source,
            flags=flags_for(i),
        )

        # Event chain: Always start with inquiry
        ApplicationEvent.objects.create(
            school_id=school_id,
            application=app,
            event_type="inquiry_created",
            payload={"source": source},
        )

        # Progress events based on stage
        if stage in ("application_started", "application_submitted", "accepted", "enrolled"):
            ApplicationEvent.objects.create(
                school_id=school_id,
                application=app,
                event_type="application_started",
                payload={},
            )

        if stage in ("application_submitted", "accepted", "enrolled"):
            ApplicationEvent.objects.create(
                school_id=school_id,
                application=app,
                event_type="application_submitted",
                payload={},
            )

        if stage in ("accepted", "enrolled"):
            ApplicationEvent.objects.create(
                school_id=school_id,
                application=app,
                event_type="decision_made",
                payload=decision_payload(stage),
            )

        if stage == "enrolled":
            ApplicationEvent.objects.create(
                school_id=school_id,
                application=app,
                event_type="enrollment_confirmed",
                payload={},
            )


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

    def _seed_financial_aid(self, school):
        """
        Create deterministic seed data for Financial Aid MVP.
        Idempotent: uses update_or_create with deterministic UUIDs.
        """
        from financial_aid.models import FinancialAidApplication, AidAward, AidAuditEvent, AidBucket

        # Fixed base timestamps
        ts_2025 = datetime(2025, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
        ts_2024 = datetime(2024, 8, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Deterministic UUIDs for applications and awards
        app_ids_2025 = [
            uuid.UUID("11111111-1111-1111-1111-000000000001"),
            uuid.UUID("11111111-1111-1111-1111-000000000002"),
            uuid.UUID("11111111-1111-1111-1111-000000000003"),
            uuid.UUID("11111111-1111-1111-1111-000000000004"),
            uuid.UUID("11111111-1111-1111-1111-000000000005"),
        ]
        app_ids_2024 = [
            uuid.UUID("22222222-2222-2222-2222-000000000001"),
            uuid.UUID("22222222-2222-2222-2222-000000000002"),
            uuid.UUID("22222222-2222-2222-2222-000000000003"),
            uuid.UUID("22222222-2222-2222-2222-000000000004"),
            uuid.UUID("22222222-2222-2222-2222-000000000005"),
        ]

        award_ids = [
            uuid.UUID("33333333-3333-3333-3333-000000000001"),
            uuid.UUID("33333333-3333-3333-3333-000000000002"),
            uuid.UUID("33333333-3333-3333-3333-000000000003"),
            uuid.UUID("33333333-3333-3333-3333-000000000004"),
            uuid.UUID("33333333-3333-3333-3333-000000000005"),
            uuid.UUID("33333333-3333-3333-3333-000000000006"),
            uuid.UUID("33333333-3333-3333-3333-000000000007"),
            uuid.UUID("33333333-3333-3333-3333-000000000008"),
            uuid.UUID("33333333-3333-3333-3333-000000000009"),
            uuid.UUID("33333333-3333-3333-3333-000000000010"),
            uuid.UUID("33333333-3333-3333-3333-000000000011"),
            uuid.UUID("33333333-3333-3333-3333-000000000012"),
        ]

        event_ids = [
            uuid.UUID("44444444-4444-4444-4444-000000000001"),
            uuid.UUID("44444444-4444-4444-4444-000000000002"),
            uuid.UUID("44444444-4444-4444-4444-000000000003"),
            uuid.UUID("44444444-4444-4444-4444-000000000004"),
            uuid.UUID("44444444-4444-4444-4444-000000000005"),
            uuid.UUID("44444444-4444-4444-4444-000000000006"),
            uuid.UUID("44444444-4444-4444-4444-000000000007"),
            uuid.UUID("44444444-4444-4444-4444-000000000008"),
            uuid.UUID("44444444-4444-4444-4444-000000000009"),
            uuid.UUID("44444444-4444-4444-4444-000000000010"),
        ]

        # Create applications
        apps_2025 = []
        for i, app_id in enumerate(app_ids_2025):
            app, _ = FinancialAidApplication.objects.update_or_create(
                id=app_id,
                defaults={
                    "school_id": school.id,
                    "household_id": uuid.UUID(f"55555555-5555-5555-5555-{i:012d}"),
                    "academic_year": "2025-2026",
                    "submitted_at": ts_2025,
                    "household_income": Decimal("60000.00"),
                    "household_size": 4,
                    "status": "submitted",
                },
            )
            apps_2025.append(app)

        apps_2024 = []
        for i, app_id in enumerate(app_ids_2024):
            app, _ = FinancialAidApplication.objects.update_or_create(
                id=app_id,
                defaults={
                    "school_id": school.id,
                    "household_id": uuid.UUID(f"66666666-6666-6666-6666-{i:012d}"),
                    "academic_year": "2024-2025",
                    "submitted_at": ts_2024,
                    "household_income": Decimal("55000.00"),
                    "household_size": 3,
                    "status": "submitted",
                },
            )
            apps_2024.append(app)

        # Create awards (12 total, distributed across buckets per year)
        # 2025: need, mission, marketing, merit, hardship (one each)
        # 2024: need, mission, marketing, merit, hardship (one each)
        # Extras: need +2, mission +1, marketing +1
        awards_data = [
            # 2025 bucket coverage (5 awards)
            (award_ids[0], apps_2025[0], AidBucket.NEED, Decimal("5000.00"), ts_2025),
            (award_ids[1], apps_2025[1], AidBucket.MISSION, Decimal("3000.00"), ts_2025),
            (award_ids[2], apps_2025[2], AidBucket.MARKETING, Decimal("2000.00"), ts_2025),
            (award_ids[3], apps_2025[3], AidBucket.MERIT, Decimal("4000.00"), ts_2025),
            (award_ids[4], apps_2025[4], AidBucket.HARDSHIP, Decimal("1500.00"), ts_2025),
            # 2024 bucket coverage (5 awards)
            (award_ids[5], apps_2024[0], AidBucket.NEED, Decimal("4500.00"), ts_2024),
            (award_ids[6], apps_2024[1], AidBucket.MISSION, Decimal("2500.00"), ts_2024),
            (award_ids[7], apps_2024[2], AidBucket.MARKETING, Decimal("1800.00"), ts_2024),
            (award_ids[8], apps_2024[3], AidBucket.MERIT, Decimal("3500.00"), ts_2024),
            (award_ids[9], apps_2024[4], AidBucket.HARDSHIP, Decimal("1200.00"), ts_2024),
            # Extra awards for bucket variation
            (award_ids[10], apps_2025[0], AidBucket.NEED, Decimal("2500.00"), ts_2025),
            (award_ids[11], apps_2024[0], AidBucket.MISSION, Decimal("1500.00"), ts_2024),
        ]

        for award_id, app, bucket, amount, created_at in awards_data:
            AidAward.objects.update_or_create(
                id=award_id,
                defaults={
                    "school_id": school.id,
                    "application": app,
                    "bucket": bucket,
                    "amount": amount,
                    "rationale": f"Seed award for {bucket}",
                    "approved_by_user_id": None,
                    "created_at": created_at,
                },
            )

        # Create audit events
        for i, event_id in enumerate(event_ids):
            if i < 6:
                # 5 award events + 1 app event for 2025
                if i < 5:
                    entity_id = award_ids[i]
                    entity_type = "aid_award"
                else:
                    entity_id = app_ids_2025[0]
                    entity_type = "aid_application"
                created_at = ts_2025
            else:
                # 5 award events + 1 app event for 2024
                if i < 11:
                    entity_id = award_ids[i - 1]
                    entity_type = "aid_award"
                else:
                    entity_id = app_ids_2024[0]
                    entity_type = "aid_application"
                created_at = ts_2024

            AidAuditEvent.objects.update_or_create(
                id=event_id,
                defaults={
                    "school_id": school.id,
                    "event_type": "seed",
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "actor_user_id": None,
                    "message": f"Seed {entity_type} created",
                    "created_at": created_at,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"[FINANCIAL_AID_SEED] Created/Updated: "
                f"10 applications, 12 awards, 10 audit events"
            )
        )


    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("=== GOLDEN_PATH_BOOTSTRAP_BEGIN ===")

        from aid.models import AidApplication, AidAward
        from billing.models import BillingRun, Invoice
        from core.models import AcademicYear, Family, School, Student
        from finance.models import ChartAccount
        from households.models import Household
        from ledger.models import Charge, LedgerAccount
        from django.contrib.auth import get_user_model

        school = School.objects.order_by("created_at", "id").first()
        if not school:
            school = School.objects.create(
                name=str(options["school_name"])[:255],
                timezone="America/New_York",
                is_active=True,
            )

        User = get_user_model()
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@local.test", "school": school},
        )
        if not admin.school:
            admin.school = school
        admin.is_active = True
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password("Crown2026!")
        admin.save()
        self.stdout.write("BOOTSTRAP_OK admin=admin active=1 staff=1 superuser=1")

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

        seed_admissions_funnel(school_id=school.id, academic_year_name=academic_year.name if academic_year else None)

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

        # Seed Financial Aid MVP data
        self._seed_financial_aid(school)

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

        self.stdout.write("=== GOLDEN_PATH_BOOTSTRAP_END ===")
