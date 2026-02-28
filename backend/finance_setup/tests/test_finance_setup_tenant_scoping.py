"""
Tests: Finance Setup tenant scoping
====================================
Verifies that policies saved for school_id=1 are invisible to school_id=2.
Uses direct ORM — no HTTP client needed.
"""

import pytest

from finance_setup.models import FinancePolicyVersion, TuitionPolicy
from finance_setup.services import get_policy_snapshot, upsert_finance_policies

pytestmark = pytest.mark.django_db

YEAR = "2026-2027"

TUITION_PAYLOAD = {
    "tuition_mode": "grade_based",
    "currency": "USD",
    "flat_annual_tuition_cents": 0,
    "fees_apply_to_aid": False,
    "fees_apply_to_discounts": False,
}
DISCOUNTS_PAYLOAD = {
    "discounts_apply_to": "tuition_only",
    "stacking_enabled": True,
    "sibling_discount_enabled": True,
    "sibling_discount_percent_bp": 1000,
    "sibling_discount_applies_from_child": 2,
    "staff_discount_enabled": True,
    "staff_discount_percent_bp": 0,
    "ministry_discount_enabled": False,
    "ministry_discount_percent_bp": 0,
    "max_discount_percent_bp": 10000,
}
AID_PAYLOAD = {
    "application_fee_cents": 5500,
    "aid_applies_to": "tuition_only",
    "distribute_aid_evenly": True,
    "max_aid_per_student_cents": 0,
    "max_aid_per_family_cents": 0,
}
PAYMENT_PLANS_PAYLOAD = {
    "allow_pay_in_full": True,
    "allow_semi_annual": True,
    "allow_quarterly": True,
    "allow_10_month": True,
    "allow_12_month": True,
    "ach_required_for_installments": True,
    "pay_in_full_discount_percent_bp": 0,
    "late_fee_grace_days": 5,
    "late_fee_flat_cents": 0,
}
EXTENDED_CARE_PAYLOAD = {
    "supports_annual": False,
    "supports_monthly": True,
    "supports_weekly": False,
    "supports_drop_in_daily": True,
    "supports_hybrid": True,
    "late_pickup_grace_minutes": 5,
    "late_pickup_fee_cents": 0,
    "late_pickup_per_minute_cents": 0,
    "post_to_ledger": True,
    "include_in_tuition_plan": False,
}

FULL_PAYLOAD = {
    "academic_year": YEAR,
    "tuition": TUITION_PAYLOAD,
    "discounts": DISCOUNTS_PAYLOAD,
    "aid": AID_PAYLOAD,
    "payment_plans": PAYMENT_PLANS_PAYLOAD,
    "extended_care": EXTENDED_CARE_PAYLOAD,
}


def test_policy_only_visible_to_owning_school():
    """Policies saved for school 1 must not appear for school 2."""
    upsert_finance_policies(school_id=1, academic_year=YEAR, payload=FULL_PAYLOAD)

    v1 = get_policy_snapshot(school_id=1, academic_year=YEAR)
    v2 = get_policy_snapshot(school_id=2, academic_year=YEAR)

    assert v1 is not None, "Policy for school 1 should exist"
    assert v2 is None, "Policy for school 2 should NOT exist when only school 1 saved one"


def test_separate_schools_store_independently():
    """Two schools can have separate policies for the same year."""
    payload_1 = dict(FULL_PAYLOAD)
    payload_1["tuition"] = dict(TUITION_PAYLOAD, flat_annual_tuition_cents=120000)

    payload_2 = dict(FULL_PAYLOAD)
    payload_2["tuition"] = dict(TUITION_PAYLOAD, flat_annual_tuition_cents=200000)

    upsert_finance_policies(school_id=10, academic_year=YEAR, payload=payload_1)
    upsert_finance_policies(school_id=20, academic_year=YEAR, payload=payload_2)

    v10 = get_policy_snapshot(school_id=10, academic_year=YEAR)
    v20 = get_policy_snapshot(school_id=20, academic_year=YEAR)

    assert v10.tuition.flat_annual_tuition_cents == 120000
    assert v20.tuition.flat_annual_tuition_cents == 200000


def test_school_multi_year_scoping():
    """School 1 2026-2027 policy must not bleed into 2027-2028."""
    upsert_finance_policies(school_id=1, academic_year="2026-2027", payload=FULL_PAYLOAD)

    v_2628 = get_policy_snapshot(school_id=1, academic_year="2027-2028")
    assert v_2628 is None, "2027-2028 policy should not exist when only 2026-2027 was saved"


def test_finance_policy_version_unique_constraint():
    """(school_id, academic_year) must be unique — second create must upsert, not duplicate."""
    upsert_finance_policies(school_id=5, academic_year=YEAR, payload=FULL_PAYLOAD)
    upsert_finance_policies(school_id=5, academic_year=YEAR, payload=FULL_PAYLOAD)

    count = FinancePolicyVersion.objects.filter(school_id=5, academic_year=YEAR).count()
    assert count == 1, f"Expected 1 FinancePolicyVersion, got {count}"
