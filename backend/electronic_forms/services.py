from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    ElectronicEnvelope,
    ElectronicFormTemplate,
    ElectronicSigner,
    ElectronicSignatureEvidence,
    canonical_document_hash,
)
from .providers import get_signature_provider


ELECTRONIC_CONSENT_VERSION = "crown-electronic-consent-v1"
ELECTRONIC_CONSENT_TEXT = (
    "I agree to conduct this transaction electronically and to receive and sign "
    "this record in electronic form. I may request a paper copy at no charge and "
    "may withdraw consent for future electronic records before signing by using "
    "the paper-copy or withdrawal option provided by CROWN or by contacting the "
    "school office through its published contact information. Withdrawal does not "
    "invalidate electronic records already completed. I can download, save, and "
    "print the retained record. I understand that access requires a current web "
    "browser and a device capable of displaying, saving, or printing HTML/PDF records."
)
SIGNING_INTENT_TEXT = (
    "By submitting my signature, I intend to sign and adopt the exact electronic "
    "record identified by the displayed document hash."
)


def _assert_signer_actor(*, signer: ElectronicSigner, user):
    if not user or not getattr(user, "is_authenticated", False):
        raise ValidationError("Authentication is required.")
    if signer.user_id != user.id:
        raise ValidationError("Only the assigned signer may act on this envelope.")
    if getattr(user, "school_id", None) and user.school_id != signer.school_id:
        raise ValidationError("Signer does not belong to this school.")


def _assert_document_integrity(envelope: ElectronicEnvelope):
    current = canonical_document_hash(envelope.document_snapshot)
    if current != envelope.document_sha256:
        raise ValidationError("Retained envelope document hash verification failed.")


def consent_disclosure() -> dict:
    return {
        "version": ELECTRONIC_CONSENT_VERSION,
        "text": ELECTRONIC_CONSENT_TEXT,
        "paper_copy_fee": "0.00",
        "withdrawal_available_before_signature": True,
        "hardware_software_requirements": (
            "A current web browser and a device capable of displaying, saving, "
            "or printing HTML/PDF records."
        ),
    }


@transaction.atomic
def create_envelope(
    *,
    template: ElectronicFormTemplate,
    created_by,
    form_data: dict | None = None,
    subject_type: str = "",
    subject_id: str = "",
    title: str = "",
    provider_code: str = "crown_native",
) -> ElectronicEnvelope:
    if getattr(created_by, "school_id", None) and created_by.school_id != template.school_id:
        raise ValidationError("Envelope creator must belong to the template school.")

    snapshot = {
        "template": {
            "key": template.key,
            "version": template.version,
            "name": template.name,
            "title": template.title,
            "body": template.body,
            "form_schema": template.form_schema,
        },
        "data": form_data or {},
    }
    document_hash = canonical_document_hash(snapshot)
    provider = get_signature_provider(provider_code)

    envelope = ElectronicEnvelope.objects.create(
        school=template.school,
        template=template,
        template_key=template.key,
        template_version=template.version,
        title=title or template.title,
        subject_type=subject_type,
        subject_id=subject_id,
        document_snapshot=snapshot,
        document_sha256=document_hash,
        provider_code=provider.code,
        created_by=created_by,
    )
    provider.prepare_envelope(envelope)
    return envelope


@transaction.atomic
def add_signer(
    *,
    envelope: ElectronicEnvelope,
    user,
    display_name: str,
    email: str = "",
    role_label: str = "",
    signing_order: int = 1,
) -> ElectronicSigner:
    if envelope.status != ElectronicEnvelope.Status.DRAFT:
        raise ValidationError("Signers may only be added while the envelope is draft.")
    if getattr(user, "school_id", None) and user.school_id != envelope.school_id:
        raise ValidationError("Signer user must belong to the envelope school.")
    return ElectronicSigner.objects.create(
        school=envelope.school,
        envelope=envelope,
        user=user,
        display_name=display_name.strip(),
        email=email.strip(),
        role_label=role_label.strip(),
        signing_order=signing_order,
    )


@transaction.atomic
def send_envelope(envelope: ElectronicEnvelope) -> ElectronicEnvelope:
    locked = ElectronicEnvelope.objects.select_for_update().get(pk=envelope.pk)
    _assert_document_integrity(locked)
    if locked.status != ElectronicEnvelope.Status.DRAFT:
        raise ValidationError("Only draft envelopes may be sent.")
    if not locked.signers.exists():
        raise ValidationError("At least one signer is required before sending.")
    locked.status = ElectronicEnvelope.Status.SENT
    locked.sent_at = timezone.now()
    locked.save(update_fields=["status", "sent_at", "updated_at"])
    return locked


def _evidence_metadata(request_meta: dict | None) -> dict:
    meta = request_meta or {}
    forwarded = str(meta.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
    remote = str(meta.get("REMOTE_ADDR") or "").strip()
    return {
        "ip_address": forwarded or remote or None,
        "user_agent": str(meta.get("HTTP_USER_AGENT") or "")[:512],
        "request_id": str(
            meta.get("HTTP_X_REQUEST_ID")
            or meta.get("HTTP_X_CORRELATION_ID")
            or ""
        )[:128],
    }


@transaction.atomic
def record_consent(
    *,
    signer: ElectronicSigner,
    user,
    disclosure_version: str,
    hardware_software_ack: bool,
    request_meta: dict | None = None,
) -> ElectronicSignatureEvidence:
    signer = ElectronicSigner.objects.select_for_update().select_related("envelope").get(pk=signer.pk)
    _assert_signer_actor(signer=signer, user=user)
    _assert_document_integrity(signer.envelope)

    if signer.envelope.status != ElectronicEnvelope.Status.SENT:
        raise ValidationError("Envelope is not available for consent.")
    if signer.status == ElectronicSigner.Status.SIGNED:
        raise ValidationError("Signed evidence cannot be replaced.")
    if disclosure_version != ELECTRONIC_CONSENT_VERSION:
        raise ValidationError("Electronic-consent disclosure version is not current.")
    if hardware_software_ack is not True:
        raise ValidationError("Access and retention capability must be acknowledged.")

    meta = _evidence_metadata(request_meta)
    evidence = ElectronicSignatureEvidence.objects.create(
        school=signer.school,
        envelope=signer.envelope,
        signer=signer,
        actor_user=user,
        action=ElectronicSignatureEvidence.Action.CONSENT,
        document_sha256=signer.envelope.document_sha256,
        consent_text=ELECTRONIC_CONSENT_TEXT,
        disclosure_version=ELECTRONIC_CONSENT_VERSION,
        hardware_software_ack=True,
        occurred_at=timezone.now(),
        **meta,
    )
    signer.status = ElectronicSigner.Status.CONSENTED
    signer.save(update_fields=["status"])
    return evidence


@transaction.atomic
def withdraw_consent(*, signer: ElectronicSigner, user, request_meta: dict | None = None):
    signer = ElectronicSigner.objects.select_for_update().select_related("envelope").get(pk=signer.pk)
    _assert_signer_actor(signer=signer, user=user)
    if signer.status == ElectronicSigner.Status.SIGNED:
        raise ValidationError("Completed signatures remain valid; use the paper-copy process for future records.")

    meta = _evidence_metadata(request_meta)
    evidence = ElectronicSignatureEvidence.objects.create(
        school=signer.school,
        envelope=signer.envelope,
        signer=signer,
        actor_user=user,
        action=ElectronicSignatureEvidence.Action.WITHDRAW_CONSENT,
        document_sha256=signer.envelope.document_sha256,
        consent_text=ELECTRONIC_CONSENT_TEXT,
        disclosure_version=ELECTRONIC_CONSENT_VERSION,
        occurred_at=timezone.now(),
        **meta,
    )
    signer.status = ElectronicSigner.Status.WITHDRAWN
    signer.save(update_fields=["status"])
    return evidence


@transaction.atomic
def request_paper_copy(*, signer: ElectronicSigner, user, request_meta: dict | None = None):
    signer = ElectronicSigner.objects.select_for_update().select_related("envelope").get(pk=signer.pk)
    _assert_signer_actor(signer=signer, user=user)

    meta = _evidence_metadata(request_meta)
    evidence = ElectronicSignatureEvidence.objects.create(
        school=signer.school,
        envelope=signer.envelope,
        signer=signer,
        actor_user=user,
        action=ElectronicSignatureEvidence.Action.PAPER_COPY_REQUEST,
        document_sha256=signer.envelope.document_sha256,
        disclosure_version=ELECTRONIC_CONSENT_VERSION,
        occurred_at=timezone.now(),
        **meta,
    )
    if signer.status != ElectronicSigner.Status.SIGNED:
        signer.status = ElectronicSigner.Status.PAPER_REQUESTED
        signer.save(update_fields=["status"])
    return evidence


@transaction.atomic
def sign_envelope(
    *,
    signer: ElectronicSigner,
    user,
    signed_name: str,
    intent_to_sign: bool,
    request_meta: dict | None = None,
) -> ElectronicSignatureEvidence:
    signer = (
        ElectronicSigner.objects.select_for_update()
        .select_related("envelope")
        .get(pk=signer.pk)
    )
    envelope = ElectronicEnvelope.objects.select_for_update().get(pk=signer.envelope_id)
    signer.envelope = envelope

    _assert_signer_actor(signer=signer, user=user)
    _assert_document_integrity(envelope)

    if envelope.status != ElectronicEnvelope.Status.SENT:
        raise ValidationError("Envelope is not available for signature.")
    if signer.status != ElectronicSigner.Status.CONSENTED:
        raise ValidationError("Current electronic-record consent is required before signing.")
    if not signed_name.strip():
        raise ValidationError("Signed name is required.")
    if intent_to_sign is not True:
        raise ValidationError("Explicit intent to sign is required.")

    consent_exists = ElectronicSignatureEvidence.objects.filter(
        signer=signer,
        action=ElectronicSignatureEvidence.Action.CONSENT,
        document_sha256=envelope.document_sha256,
        disclosure_version=ELECTRONIC_CONSENT_VERSION,
    ).exists()
    if not consent_exists:
        raise ValidationError("Consent evidence for this exact document is missing.")

    now = timezone.now()
    meta = _evidence_metadata(request_meta)
    evidence = ElectronicSignatureEvidence.objects.create(
        school=signer.school,
        envelope=envelope,
        signer=signer,
        actor_user=user,
        action=ElectronicSignatureEvidence.Action.SIGN,
        document_sha256=envelope.document_sha256,
        signed_name=signed_name.strip(),
        intent_statement=SIGNING_INTENT_TEXT,
        disclosure_version=ELECTRONIC_CONSENT_VERSION,
        hardware_software_ack=True,
        occurred_at=now,
        **meta,
    )
    signer.status = ElectronicSigner.Status.SIGNED
    signer.signed_at = now
    signer.save(update_fields=["status", "signed_at"])

    if not envelope.signers.exclude(status=ElectronicSigner.Status.SIGNED).exists():
        envelope.status = ElectronicEnvelope.Status.COMPLETED
        envelope.completed_at = now
        envelope.save(update_fields=["status", "completed_at", "updated_at"])

    return evidence
