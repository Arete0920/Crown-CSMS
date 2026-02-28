"""
Unit tests for EntitlementsService.

Coverage:
  - Plan entitlement enabled + limit resolution
  - Tenant override disables a feature that the plan enabled
  - Tenant override enables a feature the plan disabled
  - Override adjusts limit_int
  - assert_enabled raises PermissionError for disabled feature
  - assert_within_limit raises when limit exceeded
  - increment_usage creates and increments counter
"""
import uuid

import pytest

from subscriptions.models import (
    EntitlementOverride,
    Feature,
    Plan,
    PlanEntitlement,
    TenantSubscription,
    UsageCounter,
)
from subscriptions.services import EntitlementsService

pytestmark = pytest.mark.django_db


def _make_plan_feature(
    plan_code="smart_start",
    feature_key="comms.sms",
    enabled=True,
    limit_int=100,
):
    """Helper: create plan + feature + entitlement + subscription; return (school_id, feature_key)."""
    plan, _ = Plan.objects.get_or_create(
        code=plan_code, defaults={"name": plan_code.replace("_", " ").title()}
    )
    feat, _ = Feature.objects.get_or_create(key=feature_key, defaults={"name": feature_key})
    PlanEntitlement.objects.get_or_create(
        plan=plan,
        feature=feat,
        defaults={"enabled": enabled, "limit_int": limit_int},
    )
    school_id = uuid.uuid4()
    TenantSubscription.objects.create(school_id=school_id, plan=plan)
    return school_id, feature_key


# ─────────────────────────────────────────────────────────────────────────────
# get_entitlement: plan layer
# ─────────────────────────────────────────────────────────────────────────────

def test_entitlement_enabled_and_limit():
    school_id, key = _make_plan_feature(enabled=True, limit_int=100)
    ent = EntitlementsService.get_entitlement(school_id, key)
    assert ent.enabled is True
    assert ent.limit_int == 100


def test_entitlement_disabled_by_plan():
    school_id, key = _make_plan_feature(enabled=False, limit_int=None)
    ent = EntitlementsService.get_entitlement(school_id, key)
    assert ent.enabled is False


def test_entitlement_unlimited_when_limit_int_none():
    school_id, key = _make_plan_feature(enabled=True, limit_int=None)
    ent = EntitlementsService.get_entitlement(school_id, key)
    assert ent.enabled is True
    assert ent.limit_int is None


# ─────────────────────────────────────────────────────────────────────────────
# get_entitlement: override layer
# ─────────────────────────────────────────────────────────────────────────────

def test_override_disables_feature():
    school_id, key = _make_plan_feature(enabled=True, limit_int=100)
    feat = Feature.objects.get(key=key)
    EntitlementOverride.objects.create(school_id=school_id, feature=feat, enabled=False)
    ent = EntitlementsService.get_entitlement(school_id, key)
    assert ent.enabled is False


def test_override_enables_disabled_feature():
    school_id, key = _make_plan_feature(enabled=False, limit_int=None)
    feat = Feature.objects.get(key=key)
    EntitlementOverride.objects.create(school_id=school_id, feature=feat, enabled=True, limit_int=50)
    ent = EntitlementsService.get_entitlement(school_id, key)
    assert ent.enabled is True
    assert ent.limit_int == 50


def test_override_adjusts_limit_only():
    school_id, key = _make_plan_feature(enabled=True, limit_int=100)
    feat = Feature.objects.get(key=key)
    EntitlementOverride.objects.create(school_id=school_id, feature=feat, limit_int=500)
    ent = EntitlementsService.get_entitlement(school_id, key)
    assert ent.enabled is True
    assert ent.limit_int == 500


# ─────────────────────────────────────────────────────────────────────────────
# assert_enabled / assert_within_limit
# ─────────────────────────────────────────────────────────────────────────────

def test_assert_enabled_passes():
    school_id, key = _make_plan_feature(enabled=True, limit_int=None)
    EntitlementsService.assert_enabled(school_id, key)  # should not raise


def test_assert_enabled_raises():
    school_id, key = _make_plan_feature(enabled=False, limit_int=None)
    with pytest.raises(PermissionError, match="Feature not enabled"):
        EntitlementsService.assert_enabled(school_id, key)


def test_assert_within_limit_passes():
    school_id, key = _make_plan_feature(enabled=True, limit_int=100)
    EntitlementsService.assert_within_limit(school_id, key, increment=1)  # used_int=0 < 100


def test_assert_within_limit_exceeded():
    school_id, key = _make_plan_feature(enabled=True, limit_int=5)
    feat = Feature.objects.get(key=key)
    from subscriptions.services import EntitlementsService as Svc  # noqa: PLC0415
    yyyymm = Svc._period_yyyymm()
    UsageCounter.objects.create(school_id=school_id, feature=feat, period_yyyymm=yyyymm, used_int=5)
    with pytest.raises(PermissionError, match="Limit exceeded"):
        EntitlementsService.assert_within_limit(school_id, key, increment=1)


def test_assert_unlimited_never_exceeds():
    school_id, key = _make_plan_feature(enabled=True, limit_int=None)
    feat = Feature.objects.get(key=key)
    from subscriptions.services import EntitlementsService as Svc  # noqa: PLC0415
    yyyymm = Svc._period_yyyymm()
    UsageCounter.objects.create(school_id=school_id, feature=feat, period_yyyymm=yyyymm, used_int=9999)
    EntitlementsService.assert_within_limit(school_id, key, increment=9999)  # unlimited → no raise


# ─────────────────────────────────────────────────────────────────────────────
# increment_usage
# ─────────────────────────────────────────────────────────────────────────────

def test_increment_usage_creates_counter():
    school_id, key = _make_plan_feature(enabled=True, limit_int=100)
    EntitlementsService.increment_usage(school_id, key, increment=3)
    feat = Feature.objects.get(key=key)
    from subscriptions.services import EntitlementsService as Svc  # noqa: PLC0415
    uc = UsageCounter.objects.get(
        school_id=school_id, feature=feat, period_yyyymm=Svc._period_yyyymm()
    )
    assert uc.used_int == 3


def test_increment_usage_accumulates():
    school_id, key = _make_plan_feature(enabled=True, limit_int=100)
    EntitlementsService.increment_usage(school_id, key, increment=10)
    EntitlementsService.increment_usage(school_id, key, increment=5)
    feat = Feature.objects.get(key=key)
    from subscriptions.services import EntitlementsService as Svc  # noqa: PLC0415
    uc = UsageCounter.objects.get(
        school_id=school_id, feature=feat, period_yyyymm=Svc._period_yyyymm()
    )
    assert uc.used_int == 15
