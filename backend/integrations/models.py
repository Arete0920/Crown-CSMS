from __future__ import annotations
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class WebhookEvent(models.Model):
    provider = models.CharField(max_length=64)
    event_id = models.CharField(max_length=128)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    payload = models.JSONField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "event_id"], name="uniq_webhook_provider_event"),
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.event_id}"


class TeamsPreviewAudit(models.Model):
    """
    Audit log for demo-mode Teams integration preview.
    No outbound calls are made; this just logs what WOULD be sent.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="teams_preview_audits")
    event_type = models.CharField(max_length=64)   # e.g. discipline_incident, comms_message
    payload = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["school","event_type","created_at"])]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"TeamsPreview({self.event_type}, {self.created_at})"


class MicrosoftTenantBinding(models.Model):
    """Bind one CROWN school to a Microsoft Entra tenant."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="microsoft_tenant_bindings",
    )
    tenant_id = models.UUIDField()
    display_name = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "tenant_id"],
                name="uniq_microsoft_school_tenant",
            ),
            models.UniqueConstraint(
                fields=["school"],
                condition=models.Q(is_active=True),
                name="uniq_active_microsoft_tenant_per_school",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant_id", "is_active"], name="integration_tenant__ee9b98_idx"),
            models.Index(fields=["school", "is_active"], name="integration_school__67d95b_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.school_id}:{self.tenant_id}"


class MicrosoftIdentityLink(models.Model):
    """Immutable Entra object-to-CROWN-user mapping within a school tenant binding."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    binding = models.ForeignKey(
        MicrosoftTenantBinding,
        on_delete=models.CASCADE,
        related_name="identity_links",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="microsoft_identity_links",
    )
    object_id = models.UUIDField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["binding", "object_id"],
                name="uniq_microsoft_binding_object",
            ),
            models.UniqueConstraint(
                fields=["binding", "user"],
                name="uniq_microsoft_binding_user",
            ),
        ]
        indexes = [
            models.Index(fields=["object_id", "is_active"], name="integration_object__8e587f_idx"),
            models.Index(fields=["user", "is_active"], name="integration_user_id_635f6e_idx"),
        ]

    def clean(self):
        super().clean()
        if not self.binding_id or not self.user_id:
            return
        school_id = self.binding.school_id
        direct_school_id = getattr(self.user, "school_id", None)
        if direct_school_id == school_id:
            return
        if self.user.roles.filter(school_id=school_id).exists():
            return
        raise ValidationError(
            {"user": "Microsoft identity user must belong to the bound CROWN school."}
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.binding.tenant_id}:{self.object_id}->{self.user_id}"
