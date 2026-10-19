from __future__ import annotations

import json
import os
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from applications.models import Application, Applicant, ApplicationEvent
from core.models_seed import SeedRun
from core.golden_path_fixture_profiles import (
    GOLDEN_PATH_FUNNEL_SIZE,
    applicant_identity,
    fixture_uuid,
)
from crown_api.ops_route_guard import demo_ops_runtime_allowed


def seed_admissions_funnel(*, school_id, academic_year_name=None, force=False):
    """Create a fictional 94-applicant DEV funnel without deleting user records."""
    from households.models import Household

    # A forced proof rerun may refresh financial fixture records, but may not
    # erase canonical applications. Existing admissions remain authoritative.
    if Applicant.objects.filter(school_id=school_id).exists():
        return {"skipped": True, "reason": "existing_applicants_preserved"}

    sources = [
        "church_referral", "facebook", "instagram", "google",
        "direct_mail_qr", "website", "word_of_mouth", "other",
    ]

    # Fixed stage counts make dashboard contract tests reproducible.
    stage_plan = (
        ["inquiry"] * 18 +
        ["tour_scheduled"] * 12 +
        ["tour_completed"] * 10 +
        ["application_started"] * 20 +
        ["application_submitted"] * 14 +
        ["in_review"] * 10 +
        ["accepted"] * 6 +
        ["waitlisted"] * 2 +
        ["declined"] * 1 +
        ["enrolled"] * 1
    )
    assert len(stage_plan) == GOLDEN_PATH_FUNNEL_SIZE

    # Deliberate duplicate/bot scenarios; every record remains fictional.
    def flags_for(i):
        if i == 7:
            return {"fixture_origin": "golden_path", "duplicate_suspected": True, "bot_suspected": False}
        if i == 13:
            return {"fixture_origin": "golden_path", "duplicate_suspected": False, "bot_suspected": True}
        return {"fixture_origin": "golden_path", "duplicate_suspected": False, "bot_suspected": False}

    # Application.status mapping baseline
    def app_status_for(stage):
        if stage in ("application_submitted",):
            return "SUBMITTED"
        if stage in ("in_review",):
            return "IN_REVIEW"
        if stage in ("accepted", "waitlisted", "declined", "enrolled"):
            return "DECIDED"
        return "DRAFT"

    # Decision payload mapping
    def decision_payload(stage):
        if stage == "accepted":
            return {"decision": "accepted"}
        if stage == "waitlisted":
            return {"decision": "waitlisted"}
        if stage == "declined":
            return {"decision": "declined"}
        if stage == "enrolled":
            return {"decision": "accepted"}
        return None

    for i, stage in enumerate(stage_plan):
        source = sources[(i * 5 + i // len(sources)) % len(sources)]
        first_name, last_name = applicant_identity(i)
        household_id = fixture_uuid(school_id, "admissions-household", i)
        household, _ = Household.objects.get_or_create(
            id=household_id,
            defaults={"school_id": school_id, "name": f"{last_name} Family"},
        )
        if str(household.school_id) != str(school_id):
            raise CommandError("Golden Path fixture household belongs to another tenant.")

        app = Application.objects.create(
            school_id=school_id,
            household=household,
            status=app_status_for(stage),
        )

        Applicant.objects.create(
            school_id=school_id,
            application=app,
            student=None,
            first_name=first_name,
            last_name=last_name,
            grade_applying_for=str((i % 12) + 1),
            dob=None,
            source=source,
            flags=flags_for(i),
        )

        # Event chain (deterministic per stage)
        if stage in (
            "inquiry",
            "tour_scheduled",
            "tour_completed",
            "application_submitted",
            "in_review",
            "accepted",
            "waitlisted",
            "declined",
            "enrolled",
        ):
            ApplicationEvent.objects.create(
                school_id=school_id,
                application=app,
                event_type="inquiry_created",
                payload={"source": source},
            )

        if stage in ("tour_scheduled", "tour_completed"):
            ApplicationEvent.objects.create(
                school_id=school_id,
                application=app,
                event_type="tour_scheduled",
                payload={},
            )

        if stage in ("tour_completed",):
            ApplicationEvent.objects.create(
                school_id=school_id,
                application=app,
                event_type="tour_completed",
                payload={},
            )

        if stage in ("application_submitted", "in_review", "accepted", "waitlisted", "declined", "enrolled"):
            ApplicationEvent.objects.create(
                school_id=school_id,
                application=app,
                event_type="application_submitted",
                payload={},
            )

        if stage in ("accepted", "waitlisted", "declined", "enrolled"):
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

    return {"skipped": False, "pipeline_total": len(stage_plan)}


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
            "--force",
            action="store_true",
            help="Force reseed even if already seeded.",
        )
        parser.add_argument(
            "--school-id",
            type=str,
            default=None,
            help="Optional school UUID scope for telemetry.",
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

        # Tenant-scoped, stable UUIDs; no shared sequential IDs across schools.
        app_ids_2025 = [
            fixture_uuid(school.id, "aid-application-2025", i) for i in range(1, 6)
        ]
        app_ids_2024 = [
            fixture_uuid(school.id, "aid-application-2024", i) for i in range(1, 6)
        ]
        award_ids = [
            fixture_uuid(school.id, "aid-award", i) for i in range(1, 13)
        ]
        event_ids = [
            fixture_uuid(school.id, "aid-event", i) for i in range(1, 11)
        ]

        # Never reassign an existing deterministic fixture record from another
        # tenant. This guard is retained even though v2 IDs are school-scoped.
        for model, ids in (
            (FinancialAidApplication, app_ids_2025 + app_ids_2024),
            (AidAward, award_ids),
            (AidAuditEvent, event_ids),
        ):
            if model.objects.filter(id__in=ids).exclude(school_id=school.id).exists():
                raise CommandError("Golden Path financial fixture ID is already assigned to another tenant.")

        # Create applications
        apps_2025 = []
        for i, app_id in enumerate(app_ids_2025):
            app, _ = FinancialAidApplication.objects.update_or_create(
                id=app_id,
                defaults={
                    "school_id": school.id,
                    "household_id": fixture_uuid(school.id, "aid-household-2025", i),
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
                    "household_id": fixture_uuid(school.id, "aid-household-2024", i),
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
                    "rationale": f"Fictional Golden Path financial-aid scenario: {bucket}",
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
                    "message": f"Fictional Golden Path {entity_type} proof event",
                    "created_at": created_at,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"[FINANCIAL_AID_SEED] Created/Updated: "
                f"10 applications, 12 awards, 10 audit events"
            )
        )

    def _admissions_stage_counts(self, school_id):
        stages = [
            "inquiry",
            "tour_scheduled",
            "tour_completed",
            "application_started",
            "application_submitted",
            "in_review",
            "accepted",
            "waitlisted",
            "declined",
            "enrolled",
        ]

        def _decision_from_payload(payload: dict) -> str | None:
            d = (payload or {}).get("decision")
            if d in ("accepted", "waitlisted", "declined"):
                return d
            return None

        def _compute_stage(
            app,
            has_inquiry: bool,
            has_tour_scheduled: bool,
            has_tour_completed: bool,
            decision: str | None,
            enrolled: bool,
        ) -> str:
            if enrolled:
                return "enrolled"
            if decision == "accepted":
                return "accepted"
            if decision == "waitlisted":
                return "waitlisted"
            if decision == "declined":
                return "declined"
            if app.status == "IN_REVIEW":
                return "in_review"
            if app.status == "SUBMITTED":
                return "application_submitted"
            if app.status == "DRAFT":
                if has_tour_completed:
                    return "tour_completed"
                if has_tour_scheduled:
                    return "tour_scheduled"
                if has_inquiry:
                    return "inquiry"
                return "application_started"
            if app.status == "DECIDED":
                return "declined"
            return "application_started"

        apps = Application.objects.filter(school_id=school_id)
        app_ids = list(apps.values_list("id", flat=True))
        if not app_ids:
            return {k: 0 for k in stages}, 0

        events = ApplicationEvent.objects.filter(school_id=school_id, application_id__in=app_ids)
        inquiry_app_ids = set(
            events.filter(event_type="inquiry_created").values_list("application_id", flat=True)
        )
        tour_scheduled_app_ids = set(
            events.filter(event_type="tour_scheduled").values_list("application_id", flat=True)
        )
        tour_completed_app_ids = set(
            events.filter(event_type="tour_completed").values_list("application_id", flat=True)
        )
        enrolled_app_ids = set(
            events.filter(event_type="enrollment_confirmed").values_list("application_id", flat=True)
        )

        decision_by_app = {}
        for r in events.filter(event_type="decision_made").values("application_id", "payload"):
            decision = _decision_from_payload(r.get("payload") or {})
            if decision:
                decision_by_app[r["application_id"]] = decision

        stage_counts = {k: 0 for k in stages}
        apps_by_id = {a.id: a for a in apps}
        for app_id, app in apps_by_id.items():
            st = _compute_stage(
                app=app,
                has_inquiry=(app_id in inquiry_app_ids),
                has_tour_scheduled=(app_id in tour_scheduled_app_ids),
                has_tour_completed=(app_id in tour_completed_app_ids),
                decision=decision_by_app.get(app_id),
                enrolled=(app_id in enrolled_app_ids),
            )
            stage_counts[st] += 1

        return stage_counts, len(app_ids)

    def handle(self, *args, **options):
        # The management command is not a production administrator bootstrap.
        # DEV Azure remains supported only under its explicit DEV guard.
        labels = [
            str(value or "").strip().lower()
            for value in (
                os.getenv("CROWN_ENV"), os.getenv("DJANGO_ENV"),
                os.getenv("ENVIRONMENT"), os.getenv("APP_ENV"),
                os.getenv("AZURE_ENVIRONMENT"),
                getattr(settings, "CROWN_ENV", ""),
                getattr(settings, "ENVIRONMENT", ""),
            )
            if str(value or "").strip()
        ]
        if any(label in {"production", "prod", "live"} for label in labels):
            raise CommandError("Golden Path is prohibited in production.")
        sqlite_local = (
            settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
            and not (os.getenv("WEBSITE_HOSTNAME") or os.getenv("WEBSITE_INSTANCE_ID"))
        )
        if not (demo_ops_runtime_allowed() or sqlite_local):
            raise CommandError("Golden Path requires a verified DEV or isolated local runtime.")

        force = bool(options.get("force", False))
        school_id_str = options.get("school_id") or os.getenv("CROWN_GOLDEN_PATH_SCHOOL_ID")
        school_id = None
        if school_id_str:
            try:
                school_id = uuid.UUID(str(school_id_str))
            except (TypeError, ValueError) as exc:
                raise CommandError("Golden Path requires a valid school UUID.") from exc
        elif not sqlite_local:
            raise CommandError("Golden Path DEV bootstraps require --school-id.")

        self.stdout.write("=== GOLDEN_PATH_BOOTSTRAP_BEGIN ===")

        env_name = (
            os.getenv("CROWN_ENV")
            or os.getenv("DJANGO_ENV")
            or os.getenv("ENVIRONMENT")
            or os.getenv("APP_ENV")
            or "unknown"
        ).strip().lower() or "unknown"

        try:
            from crown_api.build_info import BUILD_SHA
            build_sha = BUILD_SHA
        except Exception:
            build_sha = "unknown"

        seedrun = SeedRun.objects.create(
            env_name=env_name,
            build_sha=build_sha,
            school_id=school_id,
            force=force,
            status="started",
            command="golden_path_bootstrap",
        )

        from aid.models import AidApplication, AidAward
        from billing.models import BillingRun, Invoice
        from core.models import AcademicYear, Family, School, Student
        from core.seed_helpers import ensure_deterministic_school
        from finance.models import ChartAccount
        from households.models import Household
        from ledger.models import Charge, LedgerAccount
        from django.contrib.auth import get_user_model

        try:
            with transaction.atomic():
                if school_id:
                    # Do not seed an existing customer school under an arbitrary
                    # supplied ID; the canonical DEV school is named distinctly.
                    existing_school = School.objects.filter(pk=school_id).first()
                    if existing_school and existing_school.name != "Crown Demo School":
                        raise CommandError("Golden Path refuses non-demo school identities.")
                    school, created = ensure_deterministic_school(school_id)
                    if created:
                        self.stdout.write(f"BOOTSTRAP_OK school_created=1 id={school_id}")
                else:
                    # Local SQLite can create/reuse only this named fixture school;
                    # never silently select the database's first tenant.
                    school, created = School.objects.get_or_create(
                        name="GP School",
                        defaults={"timezone": "America/New_York", "is_active": True},
                    )
                if school.name not in {"Crown Demo School", "GP School"}:
                    raise CommandError("Golden Path may seed only a dedicated demo school.")

                User = get_user_model()
                admin, created_admin = User.objects.get_or_create(
                    username="admin",
                    defaults={"email": "admin@local.test", "school": school},
                )
                if not created_admin:
                    if admin.school_id != school.id or admin.email != "admin@local.test":
                        raise CommandError("Golden Path refuses an unrelated administrator account.")
                    if not (admin.is_active and admin.is_staff and admin.is_superuser):
                        raise CommandError("Golden Path may not elevate an existing non-administrator.")
                else:
                    admin.is_active = True
                    admin.is_staff = True
                    admin.is_superuser = True

                demo_password = os.environ.get("CROWN_DEMO_PASSWORD")
                if not demo_password:
                    raise CommandError("CROWN_DEMO_PASSWORD must be set for DEV Golden Path proof.")
                try:
                    validate_password(demo_password, user=admin)
                except ValidationError as exc:
                    raise CommandError("Golden Path proof password does not satisfy security policy.") from exc
                admin.set_password(demo_password)
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

                seed_result = seed_admissions_funnel(
                    school_id=school.id,
                    academic_year_name=academic_year.name if academic_year else None,
                    force=force,
                )

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

            admissions_by_stage, pipeline_total = self._admissions_stage_counts(school.id)
            seedrun.school_id = school.id
            seedrun.status = "ok"
            seedrun.summary_json = {
                "skipped": bool(seed_result and seed_result.get("skipped")),
                "reason": (seed_result or {}).get("reason"),
                "pipeline_total": pipeline_total,
                "admissions_by_stage": admissions_by_stage,
            }
            seedrun.save(update_fields=["school_id", "status", "summary_json"])

        except Exception as e:
            seedrun.status = "error"
            seedrun.error_text = repr(e)
            seedrun.save(update_fields=["status", "error_text"])
            raise

        self.stdout.write("=== GOLDEN_PATH_BOOTSTRAP_END ===")
