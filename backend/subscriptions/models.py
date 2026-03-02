"""
Subscriptions & Entitlements models.

Tier definitions (canonical):
  smart_start  — core SIS + Admissions + Billing + Payments + Financial Aid + Comms + Dashboards
  next_level   — Smart Start + Attendance + Gradebook + Scheduling + Discipline + Activities
  all_access   — full platform, highest limits, board dashboards, priority support

Add-on features (optional, per-tenant overrides):
  SMS/Text bundle, Payments processing bundle, Solomon KB, Advanced analytics pack.
"""
from django.db import models
from django.utils import timezone


class Plan(models.Model):
    code = models.SlugField(unique=True)  # smart_start | next_level | all_access
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    # Pricing metadata — informational only; enforcement is via entitlements
    pricing_currency = models.CharField(max_length=3, default="USD")
    base_monthly = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    per_student_monthly = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["sort_order"]
        verbose_name = "Plan"

    def __str__(self) -> str:
        return self.name


class Feature(models.Model):
    # Dot-namespaced keys, e.g. "admissions.pipeline", "comms.sms"
    key = models.CharField(max_length=120, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["key"]
        verbose_name = "Feature"

    def __str__(self) -> str:
        return self.key


class PlanEntitlement(models.Model):
    """
    Defines which features/limits a plan includes.
    enabled=True means the plan unlocks the feature.
    limit_int — None means unlimited; integer = cap (e.g. 100 SMS/month).
    """
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="entitlements")
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name="plan_entitlements")
    enabled = models.BooleanField(default=True)
    limit_int = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("plan", "feature")
        verbose_name = "Plan Entitlement"

    def __str__(self) -> str:
        return f"{self.plan.code} / {self.feature.key} = {self.enabled}"


class TenantSubscription(models.Model):
    """
    Subscription history per tenant/school.
    school_id aligns with the X-School-ID tenant header UUID.
    ended_at=null means currently active; each plan change ends the previous
    row and creates a new one, so a school may have multiple historical rows.
    """
    school_id = models.UUIDField(db_index=True)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)  # null = active
    is_trial = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Tenant Subscription"

    def __str__(self) -> str:
        return f"{self.school_id} → {self.plan.code}"


class EntitlementOverride(models.Model):
    """
    Per-tenant overrides applied on top of plan entitlements.
    enabled=None means no override on the boolean.
    limit_int=None means no override on the limit.
    """
    school_id = models.UUIDField(db_index=True)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name="overrides")
    enabled = models.BooleanField(null=True, blank=True)   # None = no override
    limit_int = models.IntegerField(null=True, blank=True)  # None = no override

    class Meta:
        unique_together = ("school_id", "feature")
        verbose_name = "Entitlement Override"

    def __str__(self) -> str:
        return f"Override({self.school_id}, {self.feature.key})"


class UsageCounter(models.Model):
    """
    Monthly usage counters for metered features (e.g., SMS sends).
    period_yyyymm — e.g. "202602"
    """
    school_id = models.UUIDField(db_index=True)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name="usage_counters")
    period_yyyymm = models.CharField(max_length=6, db_index=True)
    used_int = models.IntegerField(default=0)

    class Meta:
        unique_together = ("school_id", "feature", "period_yyyymm")
        verbose_name = "Usage Counter"

    def __str__(self) -> str:
        return f"UsageCounter({self.school_id}, {self.feature.key}, {self.period_yyyymm})"
