import copy

from finance_setup.serializers import FinanceSetupWizardPayloadSerializer


BASE_PAYLOAD = {
    "academic_year": "2026-2027",
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
        "staff_discount_percent_bp": 0,
        "ministry_discount_enabled": False,
        "ministry_discount_percent_bp": 0,
        "max_discount_percent_bp": 10000,
    },
    "aid": {
        "application_fee_cents": 5500,
        "aid_applies_to": "tuition_only",
        "distribute_aid_evenly": True,
        "max_aid_per_student_cents": 0,
        "max_aid_per_family_cents": 0,
    },
    "payment_plans": {
        "allow_pay_in_full": True,
        "allow_semi_annual": True,
        "allow_quarterly": True,
        "allow_10_month": True,
        "allow_12_month": True,
        "ach_required_for_installments": True,
        "pay_in_full_discount_percent_bp": 0,
        "late_fee_grace_days": 5,
        "late_fee_flat_cents": 0,
    },
    "extended_care": {
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
    },
}


def _payload_with(path, value):
    payload = copy.deepcopy(BASE_PAYLOAD)
    section, key = path
    payload[section][key] = value
    return payload


def test_rejects_negative_currency_values():
    payload = _payload_with(("aid", "application_fee_cents"), -1)

    serializer = FinanceSetupWizardPayloadSerializer(data=payload)

    assert serializer.is_valid() is False
    assert "aid" in serializer.errors


def test_rejects_discount_basis_points_above_100_percent():
    payload = _payload_with(("discounts", "sibling_discount_percent_bp"), 10001)

    serializer = FinanceSetupWizardPayloadSerializer(data=payload)

    assert serializer.is_valid() is False
    assert "discounts" in serializer.errors
