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

from django.core.exceptions import ValidationError
from django.db import transaction

from aid.models import AidAuditEvent, AidAward, AidBudgetTracker
from core.models import HouseholdFamilyLink, LedgerEntry
from households.models import Household
from ledger.models import Credit, LedgerAccount
from ledger.services import post_account_credit


class AidBudgetError(Exception):
    """Raised when an award would exceed the remaining bucket budget."""


class AidApprovalConflictError(ValidationError):
    """Known financial-integrity conflict; never a general validation failure."""


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
    HouseholdFamilyLink. Before a Credit exists, missing/ambiguous mappings
    defer projection with an audit event. Reusing a Credit requires a unique
    mapping to its original household; unverifiable history is never repaired.
    """
    # The award lock held by both callers serializes approval/decline. Bind
    # projection and replay to the original posting, even when no Credit exists
    # yet; an accepted row alone is not proof of its current financial facts.
    original = award.ledger_entry
    if (
        original is None
        or award.awarded_cents <= 0
        or original.school_id != award.school_id
        or original.student_id != award.student_id
        or original.family_id != award.student.family_id
        or original.academic_year_id != award.academic_year_id
        or original.source != LedgerEntry.SOURCE_AID_AWARD
        or original.family.school_id != award.school_id
        or original.account.school_id != award.school_id
        or original.amount_cents != -int(award.awarded_cents)
        or original.is_reversal
        or original.reversal_of_id is not None
        or original.reversals.exists()
    ):
        raise AidApprovalConflictError("Legacy aid entry requires controlled reconciliation")

    reference = _award_credit_reference(award)
    household_ids = list(
        HouseholdFamilyLink.objects.filter(
            school=award.school,
            family=award.student.family,
        )
        .values_list("household_id", flat=True)
        .distinct()
    )
    existing = Credit.objects.filter(
        school_id=award.school_id,
        source=Credit.SOURCE_FINANCIAL_AID,
        reference=reference,
    ).first()
    if existing is not None:
        # Reusing an idempotency key must never silently accept changed financial
        # facts or a voided credit. Reconciliation requires an explicit,
        # separately authorized correction; do not recreate/rehydrate history.
        expected_amount = (
            Decimal(int(award.awarded_cents)) / Decimal("100")
        ).quantize(Decimal("0.01"))
        if (
            existing.is_void
            or existing.amount != expected_amount
            or len(household_ids) != 1
            or existing.account.household_id != household_ids[0]
            or existing.account.school_id != award.school_id
            or existing.account.household.school_id != award.school_id
        ):
            raise AidApprovalConflictError(
                "Existing financial aid credit requires controlled reconciliation"
            )
        return existing

    if len(household_ids) != 1:
        reason = "household_family_link_missing" if not household_ids else "household_family_link_ambiguous"
        _log_credit_deferred_once(award=award, actor_user=actor_user, reason=reason)
        return None

    household_id = household_ids[0]
    # HouseholdFamilyLink stores a UUID rather than a protected foreign key.
    # Validate the actual household's tenant before creating an account.
    if not Household.objects.filter(
        pk=household_id, school_id=award.school_id,
    ).exists():
        _log_credit_deferred_once(
            award=award, actor_user=actor_user,
            reason="household_missing_or_wrong_school",
        )
        return None

    account = LedgerAccount.objects.filter(household_id=household_id).first()
    if account is not None and account.school_id != award.school_id:
        _log_credit_deferred_once(
            award=award,
            actor_user=actor_user,
            reason="ledger_account_school_mismatch",
        )
        return None
    if account is None:
        account = LedgerAccount.objects.create(
            school_id=award.school_id,
            household_id=household_id,
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
def ensure_accepted_award_credit(*, award: AidAward, actor_user) -> Credit | None:
    """Idempotently project an already-posted legacy award as a non-cash Credit.

    The director action may post an accepted legacy award without running the
    separate new-approval budget decision. The existing canonical family-to-
    household bridge handles unique mappings and auditable deferral.
    """
    # Re-read under the decline/approval lock before projecting a Credit.
    # Callers may hold an ACCEPTED instance from before a concurrent decline.
    award = AidAward.objects.select_for_update().get(pk=award.pk)
    if (
        award.decision_status != AidAward.DECISION_ACCEPTED
        or award.ledger_entry_id is None
    ):
        raise RuntimeError("An accepted, legacy-posted award is required")
    if (
        award.student.school_id != award.school_id
        or award.student.family.school_id != award.school_id
        or award.academic_year.school_id != award.school_id
    ):
        raise RuntimeError("Award student/family/year school mismatch")
    if award.awarded_cents <= 0:
        raise RuntimeError("Award amount must be positive")
    return _ensure_student_account_credit(award=award, actor_user=actor_user)


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
    if (
        award.student.school_id != award.school_id
        or award.student.family.school_id != award.school_id
        or award.academic_year.school_id != award.school_id
    ):
        raise AidApprovalConflictError("Award student/family/year school mismatch")

    if award.decision_status == AidAward.DECISION_DECLINED:
        raise AidApprovalConflictError("Declined aid award requires controlled reinstatement")

    # Retry-safe migration behavior: an already-approved award does not consume
    # budget again, but can repair a previously missing Student Accounts credit
    # after its household-family mapping becomes available.
    if award.decision_status == AidAward.DECISION_ACCEPTED:
        if award.ledger_entry_id is None:
            raise AidApprovalConflictError("Accepted award without legacy posting requires controlled reconciliation")
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
