"""
management command: seed_finance_setup_demo
===========================================
Seeds a policy for one already-existing, explicitly selected fictional demo school.

Usage:
    python manage.py seed_finance_setup_demo --school-id <uuid> --dry-run
    python manage.py seed_finance_setup_demo --school-id <uuid> --confirm-demo-write
"""

from uuid import UUID

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import AcademicYear, School
from finance_setup.services import PolicyLockedError, get_policy_snapshot, upsert_finance_policies

# Variation table so the N schools look meaningfully different in the UI
SCHOOL_VARIATIONS = [
    {
        "label": "Traditional tuition, ACH-required installments",
        "tuition": {
            "tuition_mode": "grade_based",
            "currency": "USD",
            "flat_annual_tuition_cents": 0,
            "fees_apply_to_aid": False,
            "fees_apply_to_discounts": False,
        },
        "discounts": {
            "discounts_apply_to": "tuition_only",
            "stacking_enabled": True,
            "sibling_discount_enabled": True,
            "sibling_discount_percent_bp": 1000,
            "sibling_discount_applies_from_child": 2,
            "staff_discount_enabled": True,
            "staff_discount_percent_bp": 2000,
            "ministry_discount_enabled": False,
            "ministry_discount_percent_bp": 0,
            "max_discount_percent_bp": 5000,
        },
        "aid": {
            "application_fee_cents": 5500,
            "aid_applies_to": "tuition_only",
            "distribute_aid_evenly": True,
            "max_aid_per_student_cents": 300000,
            "max_aid_per_family_cents": 500000,
        },
        "payment_plans": {
            "allow_pay_in_full": True,
            "allow_semi_annual": True,
            "allow_quarterly": True,
            "allow_10_month": True,
            "allow_12_month": False,
            "ach_required_for_installments": True,
            "pay_in_full_discount_percent_bp": 200,
            "late_fee_grace_days": 5,
            "late_fee_flat_cents": 2500,
        },
        "extended_care": {
            "supports_annual": False,
            "supports_monthly": True,
            "supports_weekly": True,
            "supports_drop_in_daily": True,
            "supports_hybrid": True,
            "late_pickup_grace_minutes": 10,
            "late_pickup_fee_cents": 2500,
            "late_pickup_per_minute_cents": 100,
            "post_to_ledger": True,
            "include_in_tuition_plan": False,
        },
    },
    {
        "label": "Flat annual tuition, generous aid, no late fees",
        "tuition": {
            "tuition_mode": "flat",
            "currency": "USD",
            "flat_annual_tuition_cents": 1200000,  # $12,000
            "fees_apply_to_aid": True,
            "fees_apply_to_discounts": False,
        },
        "discounts": {
            "discounts_apply_to": "tuition_and_fees",
            "stacking_enabled": False,
            "sibling_discount_enabled": True,
            "sibling_discount_percent_bp": 1500,
            "sibling_discount_applies_from_child": 2,
            "staff_discount_enabled": True,
            "staff_discount_percent_bp": 5000,
            "ministry_discount_enabled": True,
            "ministry_discount_percent_bp": 2500,
            "max_discount_percent_bp": 7500,
        },
        "aid": {
            "application_fee_cents": 0,
            "aid_applies_to": "tuition_and_fees",
            "distribute_aid_evenly": True,
            "max_aid_per_student_cents": 600000,
            "max_aid_per_family_cents": 1000000,
        },
        "payment_plans": {
            "allow_pay_in_full": True,
            "allow_semi_annual": False,
            "allow_quarterly": False,
            "allow_10_month": True,
            "allow_12_month": True,
            "ach_required_for_installments": False,
            "pay_in_full_discount_percent_bp": 500,
            "late_fee_grace_days": 10,
            "late_fee_flat_cents": 0,
        },
        "extended_care": {
            "supports_annual": True,
            "supports_monthly": True,
            "supports_weekly": False,
            "supports_drop_in_daily": False,
            "supports_hybrid": False,
            "late_pickup_grace_minutes": 0,
            "late_pickup_fee_cents": 0,
            "late_pickup_per_minute_cents": 0,
            "post_to_ledger": False,
            "include_in_tuition_plan": True,
        },
    },
    {
        "label": "Minimal: pay-in-full or 10-month, drop-in only",
        "tuition": {
            "tuition_mode": "grade_based",
            "currency": "USD",
            "flat_annual_tuition_cents": 0,
            "fees_apply_to_aid": False,
            "fees_apply_to_discounts": False,
        },
        "discounts": {
            "discounts_apply_to": "tuition_only",
            "stacking_enabled": False,
            "sibling_discount_enabled": False,
            "sibling_discount_percent_bp": 0,
            "sibling_discount_applies_from_child": 2,
            "staff_discount_enabled": False,
            "staff_discount_percent_bp": 0,
            "ministry_discount_enabled": False,
            "ministry_discount_percent_bp": 0,
            "max_discount_percent_bp": 10000,
        },
        "aid": {
            "application_fee_cents": 10000,
            "aid_applies_to": "tuition_only",
            "distribute_aid_evenly": False,
            "max_aid_per_student_cents": 0,
            "max_aid_per_family_cents": 0,
        },
        "payment_plans": {
            "allow_pay_in_full": True,
            "allow_semi_annual": False,
            "allow_quarterly": False,
            "allow_10_month": True,
            "allow_12_month": False,
            "ach_required_for_installments": True,
            "pay_in_full_discount_percent_bp": 0,
            "late_fee_grace_days": 3,
            "late_fee_flat_cents": 5000,
        },
        "extended_care": {
            "supports_annual": False,
            "supports_monthly": False,
            "supports_weekly": False,
            "supports_drop_in_daily": True,
            "supports_hybrid": False,
            "late_pickup_grace_minutes": 5,
            "late_pickup_fee_cents": 1500,
            "late_pickup_per_minute_cents": 50,
            "post_to_ledger": True,
            "include_in_tuition_plan": False,
        },
    },
]

# Stable fictional sample policy, not the approved Jireh pricing/fee schedule.
DEMO_VARIATION = SCHOOL_VARIATIONS[0]


class Command(BaseCommand):
    help = "Seed one existing configured UUID demo-school finance policy"

    def add_arguments(self, parser):
        parser.add_argument("--school-id", type=str, help="Existing UUID matching CROWN_DEMO_SCHOOL_ID")
        parser.add_argument("--schools", type=int, default=None, help="Retired unsafe numeric ID option")
        parser.add_argument("--year", type=str, default="2026-2027")
        parser.add_argument("--dry-run", action="store_true", help="Read-only scope and policy validation")
        parser.add_argument("--confirm-demo-write", action="store_true", help="Local fictional demo only")

    def handle(self, *args, **options):
        if options["schools"] is not None:
            raise CommandError("Legacy --schools fabricated integer school IDs. Use --school-id.")
        raw = options["school_id"]
        if not raw:
            raise CommandError("--school-id is required; default numeric schools are forbidden.")
        try:
            school_id = UUID(raw)
            configured_id = UUID(str(settings.CROWN_DEMO_SCHOOL_ID))
        except (TypeError, ValueError, AttributeError) as exc:
            raise CommandError("Valid canonical UUID and CROWN_DEMO_SCHOOL_ID required.") from exc
        if str(school_id) != raw.lower() or school_id != configured_id:
            raise CommandError("Only the explicitly configured CROWN_DEMO_SCHOOL_ID may be seeded.")

        year = options["year"]
        if not isinstance(year, str) or len(year) != 9 or year[4] != "-" or (
            not year[:4].isdigit() or not year[5:].isdigit()
        ) or int(year[5:]) != int(year[:4]) + 1:
            raise CommandError("--year must be sequential YYYY-YYYY.")

        school = School.objects.filter(pk=school_id).first()
        if school is None:
            raise CommandError("Existing fictional demo School required; none was provisioned.")
        if not AcademicYear.objects.filter(school=school, name=year).exists():
            raise CommandError("Existing AcademicYear for demo school required; none was provisioned.")
        version = get_policy_snapshot(school_id=school_id, academic_year=year)
        if version is not None and version.is_locked:
            raise CommandError("Policy is locked; fixture writes prohibited.")

        if options["dry_run"]:
            self.stdout.write(f"DRY RUN: school_id={school_id} year={year}; no writes.")
            return
        if not settings.DEBUG or not options["confirm_demo_write"]:
            raise CommandError("Local DEBUG=True and --confirm-demo-write required.")

        payload = {
            "academic_year": year,
            "tuition": DEMO_VARIATION["tuition"],
            "discounts": DEMO_VARIATION["discounts"],
            "aid": DEMO_VARIATION["aid"],
            "payment_plans": DEMO_VARIATION["payment_plans"],
            "extended_care": DEMO_VARIATION["extended_care"],
        }
        try:
            upsert_finance_policies(school_id=school_id, academic_year=year, payload=payload)
        except PolicyLockedError as exc:
            raise CommandError("Finance policy locked before write.") from exc
        self.stdout.write(self.style.SUCCESS(f"Seeded fictional demo: {school_id} / {year}."))
