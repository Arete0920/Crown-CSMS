"""
management command: seed_finance_setup_demo
===========================================
Populates realistic-but-safe demo data for N schools × 1 academic year.

Usage:
    python manage.py seed_finance_setup_demo --schools 5 --year 2026-2027
"""

from django.core.management.base import BaseCommand

from finance_setup.services import upsert_finance_policies

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

# Cycles through SCHOOL_VARIATIONS for schools > len(SCHOOL_VARIATIONS)
def _variation_for(school_id: int) -> dict:
    return SCHOOL_VARIATIONS[(school_id - 1) % len(SCHOOL_VARIATIONS)]


class Command(BaseCommand):
    help = "Seed Finance Setup demo data for N schools"

    def add_arguments(self, parser):
        parser.add_argument(
            "--schools",
            type=int,
            default=5,
            help="Number of school IDs to seed (school_id 1..N)",
        )
        parser.add_argument(
            "--year",
            type=str,
            default="2026-2027",
            help="Academic year to seed (YYYY-YYYY format)",
        )

    def handle(self, *args, **options):
        n_schools = options["schools"]
        academic_year = options["year"]

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Seeding Finance Setup demo: {n_schools} schools × {academic_year}"
            )
        )

        for school_id in range(1, n_schools + 1):
            variation = _variation_for(school_id)
            payload = {
                "academic_year": academic_year,
                "tuition": variation["tuition"],
                "discounts": variation["discounts"],
                "aid": variation["aid"],
                "payment_plans": variation["payment_plans"],
                "extended_care": variation["extended_care"],
            }
            upsert_finance_policies(school_id=school_id, academic_year=academic_year, payload=payload)
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ school_id={school_id}  [{variation['label']}]"
                )
            )

        self.stdout.write(self.style.SUCCESS("Done."))
