import uuid
from django.conf import settings
from django.db import models


class BillingWizardSession(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_CONFIGURED = "configured"
    STATUS_PLANS_SAVED = "plans_saved"
    STATUS_FEES_SAVED = "fees_saved"
    STATUS_COMMITTED = "committed"
    STATUS_VERIFIED = "verified"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_CONFIGURED, "Configured"),
        (STATUS_PLANS_SAVED, "Plans Saved"),
        (STATUS_FEES_SAVED, "Fees Saved"),
        (STATUS_COMMITTED, "Committed"),
        (STATUS_VERIFIED, "Verified"),
    ]

    BILLING_MODE_SIMPLE = "simple"
    BILLING_MODE_ADVANCED = "advanced"
    BILLING_MODE_CHOICES = [
        (BILLING_MODE_SIMPLE, "Simple"),
        (BILLING_MODE_ADVANCED, "Advanced"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School",
        on_delete=models.PROTECT,
        related_name="billing_wizard_sessions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="billing_wizard_sessions",
    )

    # Step 1: Mode + Term
    term = models.CharField(max_length=24, default="")
    billing_mode = models.CharField(
        max_length=16,
        choices=BILLING_MODE_CHOICES,
        default=BILLING_MODE_SIMPLE,
    )

    # Step 2: Plans config — list of dicts:
    # {name, installment_count, first_due_on (ISO date), cadence_days, total_amount}
    plans_config = models.JSONField(default=list)

    # Step 3: Fees config — list of dicts:
    # {name, fee_type, amount, is_recurring, grade_level (optional)}
    fees_config = models.JSONField(default=list)

    # Commit result — set on commit, maps plan names to created InstallmentPlan IDs
    commit_result = models.JSONField(null=True, blank=True)

    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_wizard_session"
        indexes = [
            models.Index(fields=["school", "status"]),
            models.Index(fields=["school", "term"]),
        ]

    def __str__(self):
        return f"BillingWizardSession({self.term}, {self.status})"
