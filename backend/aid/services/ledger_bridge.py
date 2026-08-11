"""
Aid financial bridge.

Option A migration rule:
- preserve the proven Aid decision/budget engine;
- preserve the legacy core.LedgerEntry posting while active readers still use it;
- additionally project approved awards into canonical Student Accounts as a
  non-cash Credit when the existing HouseholdFamilyLink resolves uniquely;
- never synthesize a Payment for financial aid.

The entire approval path remains atomic and idempotent.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from aid.models import AidAuditEvent, AidAward, AidBudgetTracker
from core.models import HouseholdFamilyLink
from ledger.models import Credit, LedgerAccount
from ledger.services import post_account_credit


class AidBudgetError(Exception):
    """Raised when an award would exceed the remaining bucket budget."""


def _award_credit_reference(award: AidAward) -> str:
    return f"aid_award:{award.id}"


def _log_credit_deferred_once(*, award: AidAward, actor_user, reason: str) -> None:
    exists = AidAuditEvent.objects.filter(
        school=award.school,
        entity_type=AidAuditEvent.ENTITY_AWARD,
        entity_id=award.id,
        action="STUDENT_ACCOUNT_CREDIT_DEFERRED",
    ).exists()
    if exists:
        return
    AidAuditEvent.log(
        school=award.school,
        entity_type=AidAuditEvent.ENTITY_AWARD,
        entity_id=award.id,
        action="STUDENT_ACCOUNT_CREDIT_DEFERRED",
        actor_user=actor_user,
        details={"reason": reason},
    )


def _ensure_student_account_credit(*, award: AidAward, actor_user):
    """
    Idempotently dual-write an accepted Aid award into Student Accounts.

    Household identity is resolved only through the existing canonical
    HouseholdFamilyLink. Missing/ambiguous mappings are recorded as migration
    exceptions and do not break the still-active legacy posting path.
    """
    reference = _award_credit_reference(award)
    existing = Credit.objects.filter(
        school_id=award.school_id,
        source=Credit.SOURCE_FINANCIAL_AID,
        reference=reference,
    ).first()
    if existing is not None:
        return existing

    household_ids = list(
        HouseholdFamilyLink.objects.filter(
            school=award.school,
            family=award.student.family,
        )
        .values_list("household_id", flat=True)
        .distinct()
    )
    if len(household_ids) != 1:
        reason = "household_family_link_missing" if not household_ids else "household_family_link_ambiguous"
        _log_credit_deferred_once(award=award, actor_user=actor_user, reason=reason)
        return None

    account, _ = LedgerAccount.objects.get_or_create(
        school_id=award.school_id,
        household_id=household_ids[0],
    )
    credit = post_account_credit(
        school_id=award.school_id,
        account=account,
        amount=(Decimal(int(award.awarded_cents)) / Decimal("100")).quantize(Decimal("0.01")),
        source=Credit.SOURCE_FINANCIAL_AID,
        reference=reference,
        description=f"Financial Aid Award ({award.award_type})",
    )

    if not AidAuditEvent.objects.filter(
        school=award.school,
        entity_type=AidAuditEvent.ENTITY_AWARD,
        entity_id=award.id,
        action="STUDENT_ACCOUNT_CREDIT_POSTED",
    ).exists():
        AidAuditEvent.log(
            school=award.school,
            entity_type=AidAuditEvent.ENTITY_AWARD,
            entity_id=award.id,
            action="STUDENT_ACCOUNT_CREDIT_POSTED",
            actor_user=actor_user,
            details={
                "credit_id": str(credit.id),
                "amount": str(credit.amount),
                "reference": credit.reference,
            },
        )
    return credit


@transaction.atomic
def approve_award(
    *,
    award: AidAward,
    actor_user,
    reason: str = "",
) -> AidAward:
    """
    Approve an AidAward atomically while dual-writing the Option A Student
    Accounts credit projection.
    """
    award = AidAward.objects.select_for_update().select_related("student__family", "school").get(pk=award.pk)

    # Retry-safe migration behavior: an already-approved award does not consume
    # budget again, but can repair a previously missing Student Accounts credit
    # after its household-family mapping becomes available.
    if award.decision_status == AidAward.DECISION_ACCEPTED:
        _ensure_student_account_credit(award=award, actor_user=actor_user)
        return award

    budget = AidBudgetTracker.objects.select_for_update().get(
        school=award.school,
        academic_year=award.academic_year,
        bucket=award.award_type,
    )

    if award.awarded_cents <= 0:
        raise ValueError("awarded_cents must be > 0 before approval")

    remaining = budget.allocated_cents - budget.awarded_cents
    if award.awarded_cents > remaining:
        raise AidBudgetError(
            f"Bucket '{award.award_type}' budget overrun. "
            f"Requested: {award.awarded_cents}. Remaining: {remaining}."
        )

    budget.awarded_cents += award.awarded_cents
    budget.save(update_fields=["awarded_cents"])

    # Compatibility posting remains until all readers are migrated and
    # comparison proof is complete.
    award.mark_accepted_and_post(actor_user=actor_user)

    # Option A canonical Student Accounts projection. This is a Credit, never a
    # Payment, so approved aid cannot be mistaken for external cash movement.
    _ensure_student_account_credit(award=award, actor_user=actor_user)

    AidAuditEvent.log(
        school=award.school,
        entity_type=AidAuditEvent.ENTITY_AWARD,
        entity_id=award.id,
        action="AWARD_APPROVED",
        actor_user=actor_user,
        details={
            "reason": reason,
            "bucket": award.award_type,
            "awarded_cents": award.awarded_cents,
            "budget_remaining_before": remaining,
        },
    )

    return award
