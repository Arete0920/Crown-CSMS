"""
Tests: Finance Setup policy locking
=====================================
Verifies that once a policy is locked:
  - configure/ returns HTTP 409
  - lock/ is idempotent (200)
  - snapshot/ still returns data
Uses RequestFactory + patches school_id_from_request to bypass UUID validation.
"""

import json
from unittest.mock import patch

import pytest
from django.test import RequestFactory

from finance_setup.models import FinancePolicyVersion
from finance_setup.services import PolicyLockedError, lock_finance_policies, upsert_finance_policies
from finance_setup.wizard_api import wizard_configure, wizard_lock, wizard_snapshot, wizard_status

pytestmark = pytest.mark.django_db

YEAR = "2026-2027"
SCHOOL_ID = 1

FULL_PAYLOAD = {
    "academic_year": YEAR,
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

_factory = RequestFactory()
_patch_tenant = patch("finance_setup.wizard_api.school_id_from_request", return_value=SCHOOL_ID)


def _post(body: dict):
    return _factory.post(
        "/api/v1/finance-setup/wizard/configure/",
        data=json.dumps(body),
        content_type="application/json",
    )


def _get(path: str, params: dict = None):
    return _factory.get(path, data=params or {})


def _lock_post(body: dict):
    return _factory.post(
        "/api/v1/finance-setup/wizard/lock/",
        data=json.dumps(body),
        content_type="application/json",
    )


@_patch_tenant
def test_configure_succeeds_before_lock(mock_sid):
    req = _post(FULL_PAYLOAD)
    resp = wizard_configure(req)
    body = json.loads(resp.content)
    assert resp.status_code == 200, body
    assert body["status"] == "saved"


@_patch_tenant
def test_lock_returns_200(mock_sid):
    upsert_finance_policies(school_id=SCHOOL_ID, academic_year=YEAR, payload=FULL_PAYLOAD)
    req = _lock_post({"academic_year": YEAR, "locked_by": "test_suite"})
    resp = wizard_lock(req)
    body = json.loads(resp.content)
    assert resp.status_code == 200, body
    assert body["status"] == "locked"
    assert body["locked_by"] == "test_suite"


@_patch_tenant
def test_configure_after_lock_returns_409(mock_sid):
    upsert_finance_policies(school_id=SCHOOL_ID, academic_year=YEAR, payload=FULL_PAYLOAD)
    lock_finance_policies(school_id=SCHOOL_ID, academic_year=YEAR, locked_by="test_suite")

    req = _post(FULL_PAYLOAD)
    resp = wizard_configure(req)
    assert resp.status_code == 409, json.loads(resp.content)


@_patch_tenant
def test_lock_is_idempotent(mock_sid):
    upsert_finance_policies(school_id=SCHOOL_ID, academic_year=YEAR, payload=FULL_PAYLOAD)
    lock_finance_policies(school_id=SCHOOL_ID, academic_year=YEAR)

    req = _lock_post({"academic_year": YEAR})
    resp = wizard_lock(req)
    assert resp.status_code == 200, json.loads(resp.content)


@_patch_tenant
def test_snapshot_visible_after_lock(mock_sid):
    upsert_finance_policies(school_id=SCHOOL_ID, academic_year=YEAR, payload=FULL_PAYLOAD)
    lock_finance_policies(school_id=SCHOOL_ID, academic_year=YEAR)

    req = _get("/api/v1/finance-setup/wizard/snapshot/", {"year": YEAR})
    resp = wizard_snapshot(req)
    body = json.loads(resp.content)
    assert resp.status_code == 200, body
    assert body["data"]["version"]["is_locked"] is True


@_patch_tenant
def test_lock_on_missing_policy_returns_404(mock_sid):
    req = _lock_post({"academic_year": "2099-2100"})
    resp = wizard_lock(req)
    assert resp.status_code == 404, json.loads(resp.content)


def test_service_raises_policy_locked_error():
    upsert_finance_policies(school_id=2, academic_year=YEAR, payload=FULL_PAYLOAD)
    lock_finance_policies(school_id=2, academic_year=YEAR)

    with pytest.raises(PolicyLockedError):
        upsert_finance_policies(school_id=2, academic_year=YEAR, payload=FULL_PAYLOAD)
