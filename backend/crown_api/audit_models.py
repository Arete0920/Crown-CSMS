# backend/crown_api/audit_models.py
import uuid
from django.db import models
from django.utils import timezone


class AuditEvent(models.Model):
    """
    Minimal immutable audit event record.
    NOTE: We use default=timezone.now (not auto_now_add) so tests can set deterministic timestamps.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ts = models.DateTimeField(default=timezone.now, db_index=True)

    # Optional multi-tenant fields (safe to be null until full tenancy is wired)
    school_id = models.UUIDField(null=True, blank=True, db_index=True)
    actor_id = models.UUIDField(null=True, blank=True, db_index=True)
    actor_role = models.CharField(max_length=50, null=True, blank=True)

    # Core audit fields
    action = models.CharField(max_length=120, db_index=True)
    object_type = models.CharField(max_length=120, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True, db_index=True)

    # Flexible metadata (keep small; do not store secrets)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-ts"]

    def __str__(self) -> str:
        return f"{self.ts.isoformat()} {self.action} ({self.object_type}:{self.object_id})"
