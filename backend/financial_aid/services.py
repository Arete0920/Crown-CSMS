from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from .models import AidApplication, AidAward, AidDisbursement, AidEvent, AidStatus, AwardStatus


@dataclass(frozen=True)
class DecisionResult:
    award: AidAward | None


def submit_aid_application(app: AidApplication):
    if app.status != AidStatus.DRAFT:
        raise ValueError("Only DRAFT aid applications can be submitted.")
    app.status = AidStatus.SUBMITTED
    app.submitted_at = timezone.now()
    app.save(update_fields=["status", "submitted_at", "updated_at"])
    AidEvent.objects.create(
        school_id=app.school_id,
        aid_application=app,
        event_type="AID_APPLICATION_SUBMITTED",
        payload={},
    )


def decide_aid_application(app: AidApplication, decision: str, amount_annual: Decimal | None):
    """
    decision: "APPROVE" or "DENY"
    amount_annual required for APPROVE
    """
    if app.status != AidStatus.SUBMITTED:
        raise ValueError("Only SUBMITTED aid applications can be decided.")
    if decision not in ("APPROVE", "DENY"):
        raise ValueError("decision must be APPROVE or DENY")

    with transaction.atomic():
        app.status = AidStatus.DECIDED
        app.decided_at = timezone.now()
        app.save(update_fields=["status", "decided_at", "updated_at"])

        if decision == "DENY":
            award = AidAward.objects.create(
                school_id=app.school_id,
                aid_application=app,
                status=AwardStatus.DENIED,
                amount_annual=Decimal("0.00"),
            )
            AidEvent.objects.create(
                school_id=app.school_id,
                aid_application=app,
                event_type="AID_DENIED",
                payload={},
            )
            return award

        if amount_annual is None:
            raise ValueError("amount_annual is required for APPROVE")

        award = AidAward.objects.create(
            school_id=app.school_id,
            aid_application=app,
            status=AwardStatus.APPROVED,
            amount_annual=amount_annual,
        )
        AidEvent.objects.create(
            school_id=app.school_id,
            aid_application=app,
            event_type="AID_APPROVED",
            payload={"amount_annual": str(amount_annual)},
        )
        return award


def create_disbursement(award: AidAward, amount: Decimal, disbursed_on):
    if award.status != AwardStatus.APPROVED:
        raise ValueError("Only APPROVED awards can be disbursed.")
    d = AidDisbursement.objects.create(
        school_id=award.school_id,
        award=award,
        amount=amount,
        disbursed_on=disbursed_on,
    )
    AidEvent.objects.create(
        school_id=award.school_id,
        aid_application=award.aid_application,
        event_type="AID_DISBURSED",
        payload={"amount": str(amount), "disbursed_on": str(disbursed_on)},
    )
    return d
