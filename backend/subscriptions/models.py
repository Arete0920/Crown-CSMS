"""
Subscriptions & Entitlements models.

Tier definitions (canonical):
  smart_start  — core SIS + Admissions + Billing + Payments + Financial Aid + Comms + Dashboards
  next_level   — Smart Start + Attendance + Gradebook + Scheduling + Discipline + Activities
  all_access   — full platform, highest limits, board dashboards, priority support

Add-on features (optional, per-tenant overrides):
  SMS/Text bundle, Payments processing bundle, Solomon KB, Advanced analytics pack.
"""
import uuid

from django.conf import settings
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


class SchoolModule(models.Model):
    """Tracks add-on module entitlements per school (tenant)."""

    MODULE_CHOICES = [
        ("financial_aid", "Financial Aid Processing"),
        ("chapel_tracking", "Chapel & Devotional Tracking"),
        ("gradebook_pro", "Advanced Gradebook"),
        ("curriculum_mgmt", "Curriculum Management"),
        ("parent_portal_plus", "Enhanced Parent Portal"),
        ("home_academy", "Home Academy / Homeschool Affiliation"),
        ("hr_staff", "HR & Staff Management"),
        ("little_lambs", "Diadem Daycare Solutions"),
        ("transportation", "Transportation & Bus Routing"),
        ("health_office", "Health Office & Nurse Records"),
        ("alumni", "Alumni Tracking"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("trial", "Trial (30-day)"),
        ("expired", "Expired"),
        ("suspended", "Suspended"),
    ]

    BILLING_CYCLE_CHOICES = [
        ("annual", "Annual"),
        ("monthly", "Monthly"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="modules",
        db_index=True,
    )
    module_key = models.CharField(max_length=50, choices=MODULE_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="inactive")

    price_paid = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    billing_cycle = models.CharField(
        max_length=20,
        choices=BILLING_CYCLE_CHOICES,
        default="annual",
    )
    purchased_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)

    activated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="modules_activated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Internal Crown admin notes")

    class Meta:
        unique_together = ("school", "module_key")
        ordering = ["school", "module_key"]
        verbose_name = "School Module"
        verbose_name_plural = "School Modules"

    def __str__(self):
        return f"{self.school} - {self.get_module_key_display()} [{self.status}]"

    @property
    def is_active(self):
        if self.status != "active":
            return False
        if self.expiry_date and timezone.now() > self.expiry_date:
            return False
        return True

    @property
    def is_trial(self):
        if self.status != "trial":
            return False
        if self.expiry_date and timezone.now() > self.expiry_date:
            return False
        return True

    def activate(self, activated_by_user, price_paid=None, months=12):
        self.status = "active"
        self.activated_by = activated_by_user
        self.purchased_date = timezone.now()
        self.expiry_date = timezone.now() + timezone.timedelta(days=30 * months)
        if price_paid is not None:
            self.price_paid = price_paid
        self.save()

    def start_trial(self, days=30):
        self.status = "trial"
        self.purchased_date = timezone.now()
        self.expiry_date = timezone.now() + timezone.timedelta(days=days)
        self.save()

    def deactivate(self):
        self.status = "inactive"
        self.save()
