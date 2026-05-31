from __future__ import annotations

import secrets
from django.db import models
from django.utils import timezone


def make_invite_id() -> str:
    return "sbx_inv_" + secrets.token_urlsafe(18).replace("-", "").replace("_", "")[:24]


class SandboxInvite(models.Model):
    id = models.CharField(primary_key=True, max_length=40, default=make_invite_id, editable=False)
    organization_label = models.CharField(max_length=180)
    track = models.CharField(max_length=32, default="school")
    allowed_roles = models.JSONField(default=list, blank=True)
    allowed_seed_packs = models.JSONField(default=list, blank=True)
    default_guidance = models.CharField(max_length=32, default="guided")
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey("core.UserAccount", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["track", "expires_at"]),
            models.Index(fields=["revoked_at"]),
        ]

    def is_usable(self) -> bool:
        now = timezone.now()
        return self.revoked_at is None and self.expires_at > now

    def mark_used(self) -> None:
        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])


class SandboxEvent(models.Model):
    event = models.CharField(max_length=80)
    invite = models.ForeignKey(SandboxInvite, null=True, blank=True, on_delete=models.SET_NULL)
    track = models.CharField(max_length=32)
    guidance = models.CharField(max_length=32)
    persona = models.CharField(max_length=64)
    school = models.CharField(max_length=100)
    tour = models.CharField(max_length=180, blank=True, default="")
    step = models.IntegerField(null=True, blank=True)
    route = models.CharField(max_length=180, blank=True, default="")
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["event", "occurred_at"]),
            models.Index(fields=["track", "persona", "occurred_at"]),
        ]


class SandboxFeedback(models.Model):
    RATING_CHOICES = [
        ("clear", "Clear"),
        ("unclear", "Unclear"),
        ("not_relevant", "Not Relevant"),
        ("blocked", "Blocked"),
    ]

    invite = models.ForeignKey(SandboxInvite, null=True, blank=True, on_delete=models.SET_NULL)
    track = models.CharField(max_length=32)
    guidance = models.CharField(max_length=32)
    persona = models.CharField(max_length=64)
    school = models.CharField(max_length=100)
    scenario = models.CharField(max_length=180)
    step = models.IntegerField(null=True, blank=True)
    rating = models.CharField(max_length=24, choices=RATING_CHOICES)
    note = models.TextField(blank=True, default="")
    follow_up_requested = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["rating", "created_at"]),
            models.Index(fields=["track", "persona", "created_at"]),
        ]
