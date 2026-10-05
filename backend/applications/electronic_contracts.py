from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from applications.models import (
    ApplicationEvent,
    EnrollmentContract,
    EnrollmentContractStatus,
)
from electronic_forms.models import (
    ElectronicEnvelope,
    ElectronicFormTemplate,
)
from electronic_forms.services import (
    add_signer,
    create_envelope,
    send_envelope,
    void_envelope,
)


ENROLLMENT_CONTRACT_TEMPLATE_KEY = "enrollment-contract"
ENROLLMENT_CONTRACT_TEMPLATE_VERSION = 1
ENROLLMENT_CONTRACT_TEMPLATE_BODY = (
    "Enrollment agreement terms are contained in the retained contract data attached "
    "to this electronic record. Review all tuition, fee, aid, payment-plan, refund, "
    "and responsibility terms before signing."
)


def _guardian_signer_account(contract: EnrollmentContract):
    guardians = list(
        contract.application.household.guardians.select_related("account")
        .filter(account__isnull=False)
        .order_by("-is_primary", "created_at")[:2]
    )
    if not guardians:
        raise ValidationError(
            "An authenticated guardian account is required before an enrollment contract can be issued."
        )

    primary = next((row for row in guardians if row.is_primary), None)
    if primary is not None:
        return primary

    if len(guardians) == 1:
        return guardians[0]

    raise ValidationError(
        "A primary authenticated guardian must be identified before an enrollment contract can be issued."
    )


def _get_or_create_template(*, contract: EnrollmentContract, actor_user) -> ElectronicFormTemplate:
    template, _ = ElectronicFormTemplate.objects.get_or_create(
        school_id=contract.school_id,
        key=ENROLLMENT_CONTRACT_TEMPLATE_KEY,
        version=ENROLLMENT_CONTRACT_TEMPLATE_VERSION,
        defaults={
            "name": "Enrollment Agreement",
            "title": "Enrollment Agreement",
            "body": ENROLLMENT_CONTRACT_TEMPLATE_BODY,
            "form_schema": {
                "application_id": {"type": "string", "required": True},
                "contract_id": {"type": "string", "required": True},
                "contract_version": {"type": "integer", "required": True},
            },
            "created_by": actor_user,
        },
    )
    return template


def _contract_snapshot_data(contract: EnrollmentContract) -> dict:
    return {
        "application_id": str(contract.application_id),
        "contract_id": str(contract.id),
        "contract_version": contract.version,
        "line_items": contract.line_items or [],
        "contract_totals": contract.contract_totals or {},
        "net_amount_cents": int(contract.net_amount_cents or 0),
        "currency": contract.currency,
        "payment_plan": contract.payment_plan,
        "payment_schedule": contract.payment_schedule,
        "responsible_payer": contract.responsible_payer,
        "refund_terms": contract.refund_terms,
        "note": contract.note,
    }


@transaction.atomic
def ensure_enrollment_contract_envelope(
    *,
    contract: EnrollmentContract,
    actor_user,
) -> ElectronicEnvelope:
    locked = (
        EnrollmentContract.objects.select_for_update()
        .select_related("electronic_envelope", "application__household")
        .get(pk=contract.pk)
    )

    if locked.status != EnrollmentContractStatus.ISSUED:
        raise ValidationError("Only issued enrollment contracts may be sent for signature.")

    if (
        locked.electronic_envelope_id
        and locked.electronic_envelope.status != ElectronicEnvelope.Status.VOID
    ):
        return locked.electronic_envelope

    guardian = _guardian_signer_account(locked)
    template = _get_or_create_template(contract=locked, actor_user=actor_user)
    envelope = create_envelope(
        template=template,
        created_by=actor_user,
        form_data=_contract_snapshot_data(locked),
        subject_type="enrollment_contract",
        subject_id=str(locked.id),
        title=f"Enrollment Agreement v{locked.version}",
    )
    add_signer(
        envelope=envelope,
        user=guardian.account,
        display_name=f"{guardian.first_name} {guardian.last_name}".strip(),
        email=guardian.email or getattr(guardian.account, "email", ""),
        role_label="Parent/Guardian",
    )
    envelope = send_envelope(envelope)

    locked.electronic_envelope = envelope
    locked.save(update_fields=["electronic_envelope", "updated_at"])
    return envelope


@transaction.atomic
def void_pending_enrollment_contract_envelope(contract: EnrollmentContract) -> None:
    locked = (
        EnrollmentContract.objects.select_for_update()
        .select_related("electronic_envelope")
        .get(pk=contract.pk)
    )
    envelope = locked.electronic_envelope
    if envelope is None:
        return
    if envelope.status in {
        ElectronicEnvelope.Status.COMPLETED,
        ElectronicEnvelope.Status.VOID,
    }:
        return
    void_envelope(envelope=envelope)


@transaction.atomic
def sync_enrollment_contract_signature(
    *,
    envelope: ElectronicEnvelope,
    signed_at,
) -> EnrollmentContract | None:
    if envelope.subject_type != "enrollment_contract":
        return None

    contract = (
        EnrollmentContract.objects.select_for_update()
        .select_related("application")
        .filter(
            pk=envelope.subject_id,
            school_id=envelope.school_id,
            electronic_envelope=envelope,
        )
        .first()
    )
    if contract is None:
        raise ValidationError("Enrollment contract for completed envelope was not found.")

    if contract.status == EnrollmentContractStatus.SUPERSEDED:
        raise ValidationError("A superseded enrollment contract cannot be signed.")

    if contract.status in {
        EnrollmentContractStatus.SIGNED,
        EnrollmentContractStatus.COUNTERSIGNED,
    }:
        return contract

    if contract.status != EnrollmentContractStatus.ISSUED:
        raise ValidationError("Enrollment contract must be issued before signature completion.")

    if envelope.status != ElectronicEnvelope.Status.COMPLETED:
        return contract

    contract.status = EnrollmentContractStatus.SIGNED
    contract.signed_at = contract.signed_at or signed_at
    contract.save(update_fields=["status", "signed_at", "updated_at"])

    ApplicationEvent.objects.create(
        school_id=contract.school_id,
        application=contract.application,
        event_type="contract_signed_electronically",
        payload={
            "contract_id": str(contract.id),
            "contract_version": contract.version,
            "electronic_envelope_id": str(envelope.id),
            "document_sha256": envelope.document_sha256,
        },
    )
    return contract


def assert_contract_can_be_countersigned(contract: EnrollmentContract) -> None:
    envelope = contract.electronic_envelope
    if contract.status != EnrollmentContractStatus.SIGNED:
        raise ValidationError("Enrollment contract must be electronically signed before countersignature.")
    if envelope is None or envelope.status != ElectronicEnvelope.Status.COMPLETED:
        raise ValidationError("Completed electronic signature evidence is required before countersignature.")
