"""
Platform Operations models.

ProvisioningJob — tracks the lifecycle of an async school-onboarding job.
AuditEvent      — richer, platform-level audit record (complements audit.AuditLog).
"""
import uuid
from django.db import models


class ProvisioningJob(models.Model):
    """
    Represents one attempt to fully provision a new school tenant.

    Idempotency: callers pass an idempotency_key; the engine returns the
    existing job if one already exists for that key (create-or-get semantics).
    """

    STATE_QUEUED = "queued"
    STATE_RUNNING = "running"
    STATE_SUCCEEDED = "succeeded"
    STATE_FAILED = "failed"

    STATE_CHOICES = [
        (STATE_QUEUED, "Queued"),
        (STATE_RUNNING, "Running"),
        (STATE_SUCCEEDED, "Succeeded"),
        (STATE_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link to the authoritative tenant entity
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="provisioning_jobs",
    )

    # Caller-supplied idempotency key (UUID recommended)
    idempotency_key = models.CharField(max_length=255, unique=True)

    state = models.CharField(max_length=32, choices=STATE_CHOICES, default=STATE_QUEUED)

    # 0–100; updated as provisioning steps complete
    progress = models.IntegerField(default=0)

    # Human-readable error detail (non-empty only on failure)
    error = models.TextField(blank=True, default="")

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    # User who triggered provisioning (UUID, not FK — actor may be a service account)
    created_by_user_id = models.UUIDField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Provisioning Job"
        verbose_name_plural = "Provisioning Jobs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["state"]),
            models.Index(fields=["school_id"]),
        ]

    def __str__(self) -> str:
        return f"ProvisioningJob({self.id}, {self.state}, school={self.school_id})"


class AuditEvent(models.Model):
    """
    Platform-level audit record.

    Richer than audit.AuditLog — captures request correlation, IP, user-agent,
    and the full payload.  Intended for platform/super-admin operations only.
    Per-request CRUD auditing continues to use audit.AuditLog + AuditMiddleware.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # school_id stored as UUID (not FK) — some events are cross-tenant
    school_id = models.UUIDField(null=True, blank=True)

    # Actor (platform admin / service account); null for anonymous / system
    actor_user_id = models.UUIDField(null=True, blank=True)

    # Verb: e.g. "school.created", "provisioning.started", "provisioning.succeeded"
    action = models.CharField(max_length=255)

    # What kind of object was acted on
    resource_kind = models.CharField(max_length=128, blank=True, default="")

    # ID of the affected resource (UUID form)
    resource_id = models.UUIDField(null=True, blank=True)

    # HTTP request correlation — ties this audit event to APM/log streams
    request_id = models.CharField(max_length=128, blank=True, default="")

    # Request metadata
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")

    # Full request/event payload (sanitised — no secrets)
    payload = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Audit Event"
        verbose_name_plural = "Audit Events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["school_id"]),
            models.Index(fields=["actor_user_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"AuditEvent({self.action}, school={self.school_id}, actor={self.actor_user_id})"
