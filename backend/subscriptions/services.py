"""
Entitlements service.

Precedence (lowest → highest):
  1. Plan entitlement  — defines base enabled/limit for all tenants on this plan
  2. Tenant override   — per-school customisation overrides the plan if set (non-None)
  3. Usage counter     — attaches current-period consumption (read-only here)

Public API:
  EntitlementsService.get_entitlement(school_id, feature_key) → Entitlement
  EntitlementsService.assert_enabled(school_id, feature_key)
  EntitlementsService.assert_within_limit(school_id, feature_key, increment=1)
  EntitlementsService.increment_usage(school_id, feature_key, increment=1)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone

from .models import (
    EntitlementOverride,
    Feature,
    PlanEntitlement,
    TenantSubscription,
    UsageCounter,
)


@dataclass(frozen=True)
class Entitlement:
    enabled: bool
    limit_int: int | None = None
    used_int: int | None = None


class EntitlementsService:
    """
    Resolve feature entitlements for a given school/tenant.

    All methods are @classmethod so callers never need to instantiate.
    """

    @staticmethod
    def get_active_subscription(school_id) -> TenantSubscription:
        return TenantSubscription.objects.select_related("plan").get(
            school_id=school_id, ended_at__isnull=True
        )

    @staticmethod
    def _period_yyyymm(dt: datetime | None = None) -> str:
        dt = dt or timezone.now()
        return f"{dt.year}{dt.month:02d}"

    @classmethod
    def get_entitlement(cls, school_id, feature_key: str) -> Entitlement:
        """
        Return the resolved Entitlement for (school, feature).

        Raises Feature.DoesNotExist if the feature key is unknown.
        Raises TenantSubscription.DoesNotExist if no active subscription exists.
        """
        feature = Feature.objects.get(key=feature_key)
        sub = cls.get_active_subscription(school_id)

        # Step 1: plan entitlement
        pe = PlanEntitlement.objects.filter(plan=sub.plan, feature=feature).first()
        enabled = bool(pe.enabled) if pe else False
        limit_int = pe.limit_int if pe else None

        # Step 2: per-tenant override (non-None values take precedence)
        ov = EntitlementOverride.objects.filter(
            school_id=school_id, feature=feature
        ).first()
        if ov:
            if ov.enabled is not None:
                enabled = ov.enabled
            if ov.limit_int is not None:
                limit_int = ov.limit_int

        # Step 3: attach current-period usage counter (read-only)
        used_int = None
        uc = UsageCounter.objects.filter(
            school_id=school_id,
            feature=feature,
            period_yyyymm=cls._period_yyyymm(),
        ).first()
        if uc:
            used_int = uc.used_int

        return Entitlement(enabled=enabled, limit_int=limit_int, used_int=used_int)

    @classmethod
    def assert_enabled(cls, school_id, feature_key: str) -> None:
        """Raise PermissionError if the feature is not enabled for this tenant."""
        ent = cls.get_entitlement(school_id, feature_key)
        if not ent.enabled:
            raise PermissionError(f"Feature not enabled: {feature_key}")

    @classmethod
    def assert_within_limit(
        cls, school_id, feature_key: str, increment: int = 1
    ) -> None:
        """
        Raise PermissionError if:
          - feature is not enabled, OR
          - adding `increment` would exceed limit_int (ignored when limit_int is None).
        """
        ent = cls.get_entitlement(school_id, feature_key)
        if not ent.enabled:
            raise PermissionError(f"Feature not enabled: {feature_key}")
        if ent.limit_int is None:
            return  # unlimited
        used = ent.used_int or 0
        if used + increment > ent.limit_int:
            raise PermissionError(
                f"Limit exceeded for {feature_key}: {used}/{ent.limit_int}"
            )

    @classmethod
    def increment_usage(
        cls, school_id, feature_key: str, increment: int = 1
    ) -> None:
        """
        Atomically increment the current-period usage counter for a metered feature.
        Creates the counter row if it doesn't exist yet.
        """
        feature = Feature.objects.get(key=feature_key)
        yyyymm = cls._period_yyyymm()
        uc, _ = UsageCounter.objects.get_or_create(
            school_id=school_id,
            feature=feature,
            period_yyyymm=yyyymm,
            defaults={"used_int": 0},
        )
        uc.used_int += increment
        uc.save(update_fields=["used_int"])
