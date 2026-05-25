import pytest

from finance_setup.forms import (
    DiscountPolicyAdminForm,
    FinancialAidPolicyAdminForm,
)
from finance_setup.models import FinancePolicyVersion


pytestmark = pytest.mark.django_db


@pytest.fixture
def policy_version():
    return FinancePolicyVersion.objects.create(school_id=101, academic_year="2026-2027")


def _discount_form_data(version_id: int, max_discount_percent_bp: int):
    return {
        "version": version_id,
        "discounts_apply_to": "tuition_only",
        "stacking_enabled": True,
        "sibling_discount_enabled": True,
        "sibling_discount_percent_bp": 1000,
        "sibling_discount_applies_from_child": 2,
        "staff_discount_enabled": True,
        "staff_discount_percent_bp": 0,
        "ministry_discount_enabled": False,
        "ministry_discount_percent_bp": 0,
        "max_discount_percent_bp": max_discount_percent_bp,
    }


def test_form_rejects_negative_max_discount_percent_bp(policy_version):
    form = DiscountPolicyAdminForm(data=_discount_form_data(policy_version.id, -1))

    assert form.is_valid() is False
    assert "max_discount_percent_bp" in form.errors


def test_form_rejects_max_discount_percent_bp_above_10000(policy_version):
    form = DiscountPolicyAdminForm(data=_discount_form_data(policy_version.id, 10001))

    assert form.is_valid() is False
    assert "max_discount_percent_bp" in form.errors


def test_form_accepts_valid_max_discount_percent_bp(policy_version):
    form = DiscountPolicyAdminForm(data=_discount_form_data(policy_version.id, 10000))

    assert form.is_valid() is True


def test_form_rejects_negative_application_fee(policy_version):
    form = FinancialAidPolicyAdminForm(
        data={
            "version": policy_version.id,
            "application_fee_cents": -1,
            "aid_applies_to": "tuition_only",
            "distribute_aid_evenly": True,
            "max_aid_per_student_cents": 0,
            "max_aid_per_family_cents": 0,
        }
    )

    assert form.is_valid() is False
    assert "application_fee_cents" in form.errors
