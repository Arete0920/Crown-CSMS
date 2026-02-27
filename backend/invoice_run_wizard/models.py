import uuid

from django.conf import settings
from django.db import models

from core.models import School


class InvoiceRunWizardSession(models.Model):
    """
    5-state wizard session for generating finance invoices from open obligations.

    State machine:
      draft
        → configured        (POST /configure/         — period_start, period_end, due_date)
        → obligations_loaded (POST /load/              — queries FinanceObligation)
        → committed         (POST /commit/             — creates FinanceInvoice + Lines)
        → verified          (GET  /verify/             — returns invoice_count + line_count)
    """

    STATUS_DRAFT               = "draft"
    STATUS_CONFIGURED          = "configured"
    STATUS_OBLIGATIONS_LOADED  = "obligations_loaded"
    STATUS_COMMITTED           = "committed"
    STATUS_VERIFIED            = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT,               "Draft"),
        (STATUS_CONFIGURED,          "Configured"),
        (STATUS_OBLIGATIONS_LOADED,  "Obligations Loaded"),
        (STATUS_COMMITTED,           "Committed"),
        (STATUS_VERIFIED,            "Verified"),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school      = models.ForeignKey(School, on_delete=models.CASCADE, related_name="invoice_run_wizard_sessions")
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="invoice_run_wizard_sessions_created",
    )

    period_start     = models.DateField(null=True, blank=True)
    period_end       = models.DateField(null=True, blank=True)
    due_date         = models.DateField(null=True, blank=True)
    obligation_ids   = models.JSONField(default=list)   # list of UUID strings
    commit_result    = models.JSONField(null=True, blank=True)

    status     = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "invoice_run_wizard"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["school", "status"])]

    def __str__(self) -> str:
        return f"InvoiceRunWizardSession({self.school_id}, {self.period_start}→{self.period_end}, {self.status})"
