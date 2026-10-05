from __future__ import annotations

import hashlib
import json

from django.db import transaction
from django.utils import timezone

from households.models import Guardian

from .models import ContractAssentEvidence, EnrollmentContract, EnrollmentContractStatus


ASSENT_CONSENT_VERSION = "crown-contract-assent-v1"
SIGN_CONSENT_TEXT = (
    "I confirm that I reviewed this exact enrollment contract version and agree to its terms."
)
COUNTERSIGN_CONSENT_TEXT = (
    "I confirm that I am authorized by the school to countersign this exact enrollment contract version."
)


def contract_digest(contract: EnrollmentContract) -> str:
    """Stable SHA-256 digest over the material terms of one contract version."""
    payload = {
        "contract_id": str(contract.id),
        "application_id": str(contract.application_id),
        "school_id": str(contract.school_id),
        "version": int(contract.version),
        "line_items": contract.line_items or [],
        "contract_totals": contract.contract_totals or {},
        "net_amount_cents": int(contract.net_amount_cents or 0),
        "currency": contract.currency,
        "payment_plan": contract.payment_plan,
        "payment_schedule": contract.payment_schedule,
        "responsible_payer": contract.responsible_payer,
        "refund_terms": contract.refund_terms,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def actor_is_household_guardian(*, contract: EnrollmentContract, user) -> bool:
    return Guardian.objects.filter(
        school_id=contract.school_id,
        household_id=contract.application.household_id,
        account=user,
    ).exists()


@transaction.atomic
def record_contract_assent(
    *,
    contract: EnrollmentContract,
    user,
    action: str,
    signer_name: str,
    signer_email: str = "",
    ip_address=None,
    user_agent: str = "",
    request_id: str = "",
) -> ContractAssentEvidence:
    """Record append-only assent and transition the exact contract version."""
    contract = (
        EnrollmentContract.objects.select_for_update()
        .select_related("application")
        .get(pk=contract.pk)
    )

    if action == ContractAssentEvidence.Action.SIGN:
        if contract.status == EnrollmentContractStatus.SIGNED:
            existing = ContractAssentEvidence.objects.filter(
                contract=contract,
                action=action,
                actor_user=user,
                contract_sha256=contract_digest(contract),
            ).first()
            if existing:
                return existing
        if contract.status != EnrollmentContractStatus.ISSUED:
            raise ValueError("Only an issued contract can be signed.")
        consent_text = SIGN_CONSENT_TEXT
        target_status = EnrollmentContractStatus.SIGNED
        timestamp_field = "signed_at"
    elif action == ContractAssentEvidence.Action.COUNTERSIGN:
        if contract.status == EnrollmentContractStatus.COUNTERSIGNED:
            existing = ContractAssentEvidence.objects.filter(
                contract=contract,
                action=action,
                actor_user=user,
                contract_sha256=contract_digest(contract),
            ).first()
            if existing:
                return existing
        if contract.status != EnrollmentContractStatus.SIGNED:
            raise ValueError("Only a signed contract can be countersigned.")
        consent_text = COUNTERSIGN_CONSENT_TEXT
        target_status = EnrollmentContractStatus.COUNTERSIGNED
        timestamp_field = "countersigned_at"
    else:
        raise ValueError("Unsupported contract assent action.")

    digest = contract_digest(contract)
    accepted_at = timezone.now()
    evidence = ContractAssentEvidence(
        school_id=contract.school_id,
        contract=contract,
        action=action,
        actor_user=user,
        signer_name=(signer_name or "").strip()[:255],
        signer_email=(signer_email or "").strip()[:254],
        contract_sha256=digest,
        consent_version=ASSENT_CONSENT_VERSION,
        consent_text=consent_text,
        accepted_at=accepted_at,
        ip_address=ip_address,
        user_agent=(user_agent or "")[:512],
        request_id=(request_id or "")[:128],
    )
    if not evidence.signer_name:
        raise ValueError("signer_name is required.")
    evidence.save()

    contract.status = target_status
    if not getattr(contract, timestamp_field):
        setattr(contract, timestamp_field, accepted_at)
    contract.save(update_fields=["status", timestamp_field, "updated_at"])
    return evidence
