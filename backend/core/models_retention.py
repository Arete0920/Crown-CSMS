"""
Data Retention Policy model.

Stores per-model purge windows and legal hold flags.
Used by core.management.commands.purge_expired_records and
core.services.retention_service.purge_expired_records().
"""
from django.db import models


class DataRetentionPolicy(models.Model):
    """
    Defines how long records of a given Django model are kept before purge.

    Fields
    ------
    model_name      : "<app_label>.<ModelName>" as understood by apps.get_model()
    retention_days  : records older than this (measured from created_at) are purged
    legal_hold      : when True the purge service skips this model entirely
    """

    model_name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Django app label + model, e.g. "audit.AuditLog"',
    )
    retention_days = models.IntegerField(
        default=365,
        help_text="Days to retain records from created_at before purging.",
    )
    legal_hold = models.BooleanField(
        default=False,
        help_text="When True, this model is excluded from automated purge.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Data Retention Policy"
        verbose_name_plural = "Data Retention Policies"
        ordering = ["model_name"]

    def __str__(self) -> str:
        hold = " [LEGAL HOLD]" if self.legal_hold else ""
        return f"{self.model_name} — {self.retention_days}d{hold}"


class RetentionPurgeAudit(models.Model):
    """
    Immutable audit record for each retention policy evaluation within a purge run.
    """

    run_id = models.UUIDField(db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    retention_days = models.IntegerField(default=0)
    legal_hold = models.BooleanField(default=False)
    deleted_count = models.IntegerField(default=0)
    skipped_reason = models.CharField(max_length=255, blank=True, default="")
    policy_snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Retention Purge Audit"
        verbose_name_plural = "Retention Purge Audits"
        ordering = ["-created_at", "model_name"]

    def __str__(self) -> str:
        return f"{self.model_name} run={self.run_id} deleted={self.deleted_count}"
