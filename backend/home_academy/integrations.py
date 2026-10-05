from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone


class HomeAcademyIntegrationError(ValueError):
    """Raised when a downstream Home Academy integration cannot be proven safe."""


def _to_cents(amount) -> int:
    value = (Decimal(amount) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(value)


def _resolve_payer_user(*, school_id, student_id):
    from core.models import Student, UserAccount

    student = (
        Student.objects.select_related("family")
        .filter(pk=student_id, school_id=school_id, status="ACTIVE")
        .first()
    )
    if student is None:
        raise HomeAcademyIntegrationError("Canonical student is not active in this school.")

    payers = list(
        UserAccount.objects.filter(
            school_id=school_id,
            guardian__school_id=school_id,
            guardian__family_id=student.family_id,
            guardian__portal_access=True,
            is_active=True,
        ).select_related("guardian")[:2]
    )
    if len(payers) != 1:
        raise HomeAcademyIntegrationError(
            "Exactly one active portal guardian payer is required before Home Academy billing."
        )
    return student, payers[0]


@transaction.atomic
def create_finance_obligation_for_registration(registration):
    """
    Create and ledger-post the canonical finance obligation for a Home Academy registration.

    Idempotent: an existing finance_obligation_id is returned unchanged.
    Zero-priced offerings create no obligation and return None.
    """
    from finance.models import FinanceObligation, ObligationType
    from finance.services import ledger_post_obligation
    from home_academy.models import OfferingEnrollment

    locked = (
        OfferingEnrollment.objects.select_for_update()
        .select_related("offering")
        .get(pk=registration.pk)
    )
    if locked.finance_obligation_id:
        obligation = FinanceObligation.objects.filter(
            pk=locked.finance_obligation_id,
            school_id=locked.school_id,
        ).first()
        if obligation is None:
            raise HomeAcademyIntegrationError(
                "Stored Home Academy finance obligation reference is invalid."
            )
        return obligation

    offering = locked.offering
    if offering.school_id != locked.school_id:
        raise HomeAcademyIntegrationError("Offering tenant does not match registration tenant.")

    amount_cents = _to_cents(offering.price)
    if amount_cents <= 0:
        locked.payment_status = "not_required"
        locked.save(update_fields=["payment_status", "updated_at"])
        return None

    student, payer = _resolve_payer_user(
        school_id=locked.school_id,
        student_id=locked.student_id,
    )

    obligation = FinanceObligation.objects.create(
        school_id=locked.school_id,
        payer_user=payer,
        obligation_type=ObligationType.FEE,
        description=f"Home Academy: {offering.title}",
        due_date=timezone.localdate(),
        amount_cents=amount_cents,
        academic_year_label=offering.school_year,
        reference=f"home-academy:{locked.pk}",
    )
    result = ledger_post_obligation(obligation)
    if not result.ok:
        raise HomeAcademyIntegrationError(
            f"Home Academy ledger posting failed: {result.reference}"
        )

    locked.finance_obligation_id = obligation.pk
    locked.payment_status = "pending"
    locked.save(update_fields=["finance_obligation_id", "payment_status", "updated_at"])
    return obligation
