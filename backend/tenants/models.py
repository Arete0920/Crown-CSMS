"""
Tenant Registry models.

These models *extend* core.School with platform-level metadata.
core.School is the tenant root entity — never duplicate it here.

TenantProfile: operational/billing fields per school tenant.
SchoolSettings: configurable per-school JSON knobs (brand, modules, security, comms).
"""
import uuid
from django.db import models


class TenantProfile(models.Model):
    """
    One-to-one extension of core.School with platform-level metadata.

    Adds fields required for multi-tenant SaaS operations that are
    intentionally kept out of core.School (which owns identity only).
    """

    PLAN_CHOICES = [
        ("starter", "Starter"),
        ("growth", "Growth"),
        ("enterprise", "Enterprise"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("provisioning", "Provisioning"),
        ("active", "Active"),
        ("suspended", "Suspended"),
        ("offboarded", "Offboarded"),
    ]

    PAYMENT_PROVIDER_CHOICES = [
        ("manual", "Manual / Invoice"),
        ("none", "None / Disabled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link back to the authoritative tenant entity
    school = models.OneToOneField(
        "core.School",
        on_delete=models.CASCADE,
        related_name="tenant_profile",
    )

    # Human-readable URL slug (e.g. "lincoln-academy")
    slug = models.SlugField(max_length=128, unique=True)

    # Billing / commercial tier
    plan_code = models.CharField(max_length=32, choices=PLAN_CHOICES, default="starter")

    # Custom domain for portal (optional)
    domain = models.CharField(max_length=255, blank=True, default="")

    # IANA timezone string (e.g. "America/Chicago")
    timezone = models.CharField(max_length=64, default="America/New_York")

    # Payment orchestration mode. External processors remain disabled.
    payment_provider = models.CharField(
        max_length=32, choices=PAYMENT_PROVIDER_CHOICES, default="none"
    )

    # Legacy provider account reference retained for read compatibility only.
    # No current runtime selects or contacts that provider.
    stripe_account_id = models.CharField(max_length=128, blank=True, default="")

    # Lifecycle state
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tenant Profile"
        verbose_name_plural = "Tenant Profiles"

    def __str__(self) -> str:
        return f"TenantProfile({self.slug}, {self.status})"


class SchoolSettings(models.Model):
    """
    Per-school JSON configuration knobs.

    Kept as structured JSONFields rather than normalized columns so
    that new knobs can be added without schema migrations.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.OneToOneField(
        "core.School",
        on_delete=models.CASCADE,
        related_name="school_settings",
    )

    # Brand: colors, logo URL, display name overrides
    brand = models.JSONField(default=dict, blank=True)

    # Feature flags: which modules are enabled for this school
    modules = models.JSONField(default=dict, blank=True)

    # Security settings: MFA policy, session timeouts, IP allowlists
    security = models.JSONField(default=dict, blank=True)

    # Communications: notification channels, email provider config
    comms = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "School Settings"
        verbose_name_plural = "School Settings"

    def __str__(self) -> str:
        return f"SchoolSettings({self.school_id})"
