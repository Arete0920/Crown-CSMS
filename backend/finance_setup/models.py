from django.db import models
from django.utils import timezone


class FinancePolicyVersion(models.Model):
    """
    One immutable policy snapshot per school_id + academic_year.
    Once locked, cannot be edited. New year => new row.
    """
    school_id = models.IntegerField(db_index=True)
    academic_year = models.CharField(max_length=9, db_index=True)  # e.g. "2026-2027"

    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.CharField(max_length=120, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("school_id", "academic_year")

    def __str__(self):
        status = "LOCKED" if self.is_locked else "draft"
        return f"FinancePolicyVersion school={self.school_id} year={self.academic_year} [{status}]"

    def lock(self, locked_by=None):
        self.is_locked = True
        self.locked_at = timezone.now()
        self.locked_by = locked_by or self.locked_by
        self.save(update_fields=["is_locked", "locked_at", "locked_by"])


class TuitionPolicy(models.Model):
    version = models.OneToOneField(
        FinancePolicyVersion, on_delete=models.CASCADE, related_name="tuition"
    )

    tuition_mode = models.CharField(max_length=32, default="grade_based")  # grade_based | flat
    currency = models.CharField(max_length=3, default="USD")

    # Optional flat fallback (cents)
    flat_annual_tuition_cents = models.IntegerField(default=0)

    # Fee policy toggles
    fees_apply_to_aid = models.BooleanField(default=False)
    fees_apply_to_discounts = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Tuition Policy"


class DiscountPolicy(models.Model):
    version = models.OneToOneField(
        FinancePolicyVersion, on_delete=models.CASCADE, related_name="discounts"
    )

    discounts_apply_to = models.CharField(
        max_length=16, default="tuition_only"
    )  # tuition_only | tuition_and_fees

    stacking_enabled = models.BooleanField(default=True)

    # Sibling discount
    sibling_discount_enabled = models.BooleanField(default=True)
    sibling_discount_percent_bp = models.IntegerField(default=1000)  # basis points: 1000 = 10%
    sibling_discount_applies_from_child = models.IntegerField(default=2)

    # Staff discount
    staff_discount_enabled = models.BooleanField(default=True)
    staff_discount_percent_bp = models.IntegerField(default=0)

    # Ministry discount
    ministry_discount_enabled = models.BooleanField(default=False)
    ministry_discount_percent_bp = models.IntegerField(default=0)

    # Guardrail
    max_discount_percent_bp = models.IntegerField(default=10000)  # 100% max

    class Meta:
        verbose_name = "Discount Policy"


class FinancialAidPolicy(models.Model):
    version = models.OneToOneField(
        FinancePolicyVersion, on_delete=models.CASCADE, related_name="aid"
    )

    application_fee_cents = models.IntegerField(default=5500)

    aid_applies_to = models.CharField(max_length=16, default="tuition_only")  # tuition_only | tuition_and_fees
    distribute_aid_evenly = models.BooleanField(default=True)

    max_aid_per_student_cents = models.IntegerField(default=0)  # 0 = no cap
    max_aid_per_family_cents = models.IntegerField(default=0)   # 0 = no cap

    class Meta:
        verbose_name = "Financial Aid Policy"


class PaymentPlanPolicy(models.Model):
    version = models.OneToOneField(
        FinancePolicyVersion, on_delete=models.CASCADE, related_name="payment_plans"
    )

    allow_pay_in_full = models.BooleanField(default=True)
    allow_semi_annual = models.BooleanField(default=True)
    allow_quarterly = models.BooleanField(default=True)
    allow_10_month = models.BooleanField(default=True)
    allow_12_month = models.BooleanField(default=True)

    ach_required_for_installments = models.BooleanField(default=True)

    pay_in_full_discount_percent_bp = models.IntegerField(default=0)

    late_fee_grace_days = models.IntegerField(default=5)
    late_fee_flat_cents = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Payment Plan Policy"


class ExtendedCarePolicy(models.Model):
    version = models.OneToOneField(
        FinancePolicyVersion, on_delete=models.CASCADE, related_name="extended_care"
    )

    supports_annual = models.BooleanField(default=False)
    supports_monthly = models.BooleanField(default=True)
    supports_weekly = models.BooleanField(default=False)
    supports_drop_in_daily = models.BooleanField(default=True)
    supports_hybrid = models.BooleanField(default=True)

    late_pickup_grace_minutes = models.IntegerField(default=5)
    late_pickup_fee_cents = models.IntegerField(default=0)
    late_pickup_per_minute_cents = models.IntegerField(default=0)

    post_to_ledger = models.BooleanField(default=True)
    include_in_tuition_plan = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Extended Care Policy"
