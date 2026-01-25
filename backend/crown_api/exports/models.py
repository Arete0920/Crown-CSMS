from django.conf import settings
from django.db import models


class ExportAuditLog(models.Model):
    """Records an export action for auditability (who/what/when)."""

    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="export_audit_logs",
    )

    export_name = models.CharField(max_length=120)  # e.g. statements.csv
    path = models.CharField(max_length=255)  # request.path
    method = models.CharField(max_length=10, default="GET")
    status_code = models.IntegerField(default=200)

    # optional useful metadata
    school_id = models.CharField(max_length=64, blank=True, default="")
    row_count = models.IntegerField(null=True, blank=True)

    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")

    def __str__(self):
        who = getattr(self.user, "username", None) if self.user else "anonymous"
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} {who} {self.export_name} {self.status_code}"
