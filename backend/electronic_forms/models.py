from __future__ import annotations

import hashlib
import json
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def canonical_document_hash(snapshot) -> str:
    payload = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ElectronicFormTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.PROTECT, related_name="electronic_form_templates")
    key = models.CharField(max_length=100)
    version = models.PositiveIntegerField(default=1)
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=255)
    body = models.TextField()
    form_schema = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="electronic_form_templates_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "key", "version"],
                name="uniq_eform_template_school_key_version",
            )
        ]
        ordering = ["school_id", "key", "-version"]

    def save(self, *args, **kwargs):
        if self.pk:
            prior = type(self).objects.filter(pk=self.pk).values(
                "school_id", "key", "version", "name", "title", "body", "form_schema", "created_by_id"
            ).first()
            if prior:
                immutable = {
                    "school_id": self.school_id,
                    "key": self.key,
                    "version": self.version,
                    "name": self.name,
                    "title": self.title,
                    "body": self.body,
                    "form_schema": self.form_schema,
                    "created_by_id": self.created_by_id,
                }
                if prior != immutable:
                    raise ValidationError("Electronic form template versions are immutable; create a new version instead.")
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.key} v{self.version}"


class ElectronicEnvelope(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SENT = "SENT", "Sent"
        COMPLETED = "COMPLETED", "Completed"
        VOID = "VOID", "Void"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.PROTECT, related_name="electronic_envelopes")
    template = models.ForeignKey(
        ElectronicFormTemplate,
        on_delete=models.PROTECT,
        related_name="envelopes",
    )
    template_key = models.CharField(max_length=100)
    template_version = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    subject_type = models.CharField(max_length=100, blank=True, default="")
    subject_id = models.CharField(max_length=128, blank=True, default="")
    document_snapshot = models.JSONField(default=dict)
    document_sha256 = models.CharField(max_length=64, db_index=True)
    provider_code = models.CharField(max_length=64, default="crown_native")
    external_reference = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="electronic_envelopes_created",
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    voided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "status"], name="eform_env_school_status_idx"),
            models.Index(fields=["school", "subject_type", "subject_id"], name="eform_env_subject_idx"),
        ]
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.template_id and self.school_id != self.template.school_id:
            raise ValidationError({"template": "Template must belong to the same school."})
        expected = canonical_document_hash(self.document_snapshot)
        if self.document_sha256 and self.document_sha256 != expected:
            raise ValidationError({"document_sha256": "Document hash does not match the retained snapshot."})
        if not self.document_sha256:
            self.document_sha256 = expected
        if self.template_id:
            if self.template_key != self.template.key or self.template_version != self.template.version:
                raise ValidationError("Envelope template snapshot metadata must match the selected template.")

    def save(self, *args, **kwargs):
        if self.pk:
            prior = type(self).objects.filter(pk=self.pk).values(
                "school_id",
                "template_id",
                "template_key",
                "template_version",
                "document_snapshot",
                "document_sha256",
            ).first()
            if prior:
                immutable = {
                    "school_id": self.school_id,
                    "template_id": self.template_id,
                    "template_key": self.template_key,
                    "template_version": self.template_version,
                    "document_snapshot": self.document_snapshot,
                    "document_sha256": self.document_sha256,
                }
                if prior != immutable:
                    raise ValidationError("Electronic envelope document snapshots are immutable.")
        self.full_clean()
        return super().save(*args, **kwargs)


class ElectronicSigner(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONSENTED = "CONSENTED", "Consented"
        SIGNED = "SIGNED", "Signed"
        DECLINED = "DECLINED", "Declined"
        WITHDRAWN = "WITHDRAWN", "Electronic consent withdrawn"
        PAPER_REQUESTED = "PAPER_REQUESTED", "Paper copy requested"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.PROTECT, related_name="electronic_signers")
    envelope = models.ForeignKey(ElectronicEnvelope, on_delete=models.PROTECT, related_name="signers")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="electronic_signature_assignments",
    )
    role_label = models.CharField(max_length=100, blank=True, default="")
    display_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default="")
    signing_order = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING, db_index=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["envelope", "user"],
                name="uniq_eform_envelope_user_signer",
            )
        ]
        ordering = ["signing_order", "created_at"]

    def clean(self):
        super().clean()
        if self.envelope_id and self.school_id != self.envelope.school_id:
            raise ValidationError({"envelope": "Signer and envelope must belong to the same school."})
        user_school_id = getattr(self.user, "school_id", None) if self.user_id else None
        if user_school_id and user_school_id != self.school_id:
            raise ValidationError({"user": "Signer user must belong to the same school."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ElectronicSignatureEvidence(models.Model):
    class Action(models.TextChoices):
        CONSENT = "CONSENT", "Consent to electronic records"
        WITHDRAW_CONSENT = "WITHDRAW_CONSENT", "Withdraw electronic consent"
        PAPER_COPY_REQUEST = "PAPER_COPY_REQUEST", "Request paper copy"
        SIGN = "SIGN", "Sign"
        DECLINE = "DECLINE", "Decline"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.PROTECT, related_name="electronic_signature_evidence")
    envelope = models.ForeignKey(ElectronicEnvelope, on_delete=models.PROTECT, related_name="signature_evidence")
    signer = models.ForeignKey(ElectronicSigner, on_delete=models.PROTECT, related_name="evidence")
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="electronic_signature_evidence",
    )
    action = models.CharField(max_length=32, choices=Action.choices, db_index=True)
    document_sha256 = models.CharField(max_length=64, db_index=True)
    signed_name = models.CharField(max_length=255, blank=True, default="")
    intent_statement = models.TextField(blank=True, default="")
    consent_text = models.TextField(blank=True, default="")
    disclosure_version = models.CharField(max_length=64, blank=True, default="")
    hardware_software_ack = models.BooleanField(default=False)
    auth_method = models.CharField(max_length=64, default="authenticated_session")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True, default="")
    request_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    occurred_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "envelope", "action"], name="eform_evd_env_action_idx"),
            models.Index(fields=["school", "actor_user", "occurred_at"], name="eform_evd_actor_time_idx"),
        ]
        ordering = ["occurred_at", "created_at"]

    def clean(self):
        super().clean()
        if self.envelope_id and self.school_id != self.envelope.school_id:
            raise ValidationError({"envelope": "Evidence and envelope must belong to the same school."})
        if self.signer_id and self.school_id != self.signer.school_id:
            raise ValidationError({"signer": "Evidence and signer must belong to the same school."})
        if self.signer_id and self.envelope_id and self.signer.envelope_id != self.envelope_id:
            raise ValidationError({"signer": "Signer must belong to the same envelope."})
        if self.actor_user_id and self.signer_id and self.actor_user_id != self.signer.user_id:
            raise ValidationError({"actor_user": "Evidence actor must be the assigned signer."})
        if self.document_sha256 != self.envelope.document_sha256:
            raise ValidationError({"document_sha256": "Evidence must reference the retained envelope hash."})

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Electronic signature evidence is append-only and cannot be modified.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Electronic signature evidence is retained and cannot be deleted.")
