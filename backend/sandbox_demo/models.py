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



class SandboxBuyerWorkspace(models.Model):
    """Guarded binding for one fictional buyer invite and one isolated school.

    Creating this record is not provisioning or proof of safe buyer access.
    Hosted sessions remain blocked unless the existing school and actor are
    independently verified. Existing historical invites are not bound.
    """

    invite = models.OneToOneField(
        SandboxInvite, on_delete=models.PROTECT, related_name="buyer_workspace"
    )
    school = models.OneToOneField(
        "core.School", on_delete=models.PROTECT, related_name="buyer_sandbox_workspace"
    )
    source_sha = models.CharField(max_length=40)
    provisioned_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


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

class SandboxBuyerAidFamily(models.Model):
    """A single explicitly authorized invented family per buyer workspace."""
    workspace = models.OneToOneField(SandboxBuyerWorkspace, on_delete=models.PROTECT, related_name="fictional_aid_family")
    family = models.OneToOneField("core.Family", on_delete=models.PROTECT, related_name="fictional_buyer_aid_family")
    guardian = models.OneToOneField("core.Guardian", on_delete=models.PROTECT, related_name="fictional_buyer_guardian")


class SandboxBuyerSGOPartner(models.Model):
    """Fictional external SGO partner bound to the buyer, not school authority."""
    workspace = models.ForeignKey(SandboxBuyerWorkspace, on_delete=models.PROTECT, related_name="fictional_sgo_partners")
    organization = models.OneToOneField("jireh_sgo.SGOOrganization", on_delete=models.PROTECT, related_name="fictional_buyer_partner")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["workspace", "organization"], name="unique_buyer_sgo_partner")]


class SandboxBuyerSGOProgram(models.Model):
    """Exact delegated fictional program provenance."""
    partner = models.ForeignKey(SandboxBuyerSGOPartner, on_delete=models.PROTECT, related_name="programs")
    program = models.OneToOneField("jireh_sgo.SGOProgram", on_delete=models.PROTECT, related_name="sandbox_buyer_program")
