"""
Aid Ledger Bridge
=================
Transactional award approval: budget enforcement → ledger posting → audit log.

Architecture note:
  Ledger entry creation is handled by AidAward.mark_accepted_and_post(), which
  already writes a LedgerEntry credit and emits AWARD_ACCEPTED + LEDGER_POSTED
  audit events.  This bridge layer adds budget-bucket enforcement
  (via AidBudgetTracker.select_for_update) and an explicit approval audit event
  *before* delegating to the model method.

All operations are wrapped in a single transaction.atomic() block.
Idempotent: an already-approved award is returned without error or side effect.
"""

from __future__ import annotations

from django.db import transaction

from aid.models import AidAuditEvent, AidAward, AidBudgetTracker


class AidBudgetError(Exception):
    """
    Raised when an award would exceed the remaining bucket budget.
    Maps to HTTP 409 at the API layer.
    """


@transaction.atomic
def approve_award(
    *,
    award: AidAward,
    actor_user,
    reason: str = "",
) -> AidAward:
    """
    Approve an AidAward atomically.

    Operations (all-or-nothing):
      1. Lock the award and its budget row for update.
      2. Enforce bucket budget — raise AidBudgetError if overrun.
      3. Decrement bucket awarded_cents.
      4. Call award.mark_accepted_and_post() — posts ledger entry, emits
         AWARD_ACCEPTED + LEDGER_POSTED audit events.
      5. Write an explicit AWARD_APPROVED audit event with actor + reason.

    Args:
        award:       AidAward instance (any decision_status).
        actor_user:  UserAccount instance or None.
        reason:      Human-readable reason for the approval (stored in audit log).

    Returns:
        The (mutated) AidAward after approval.

    Raises:
        AidBudgetError: bucket budget would be exceeded.
        AidBudgetTracker.DoesNotExist: no budget row for this school/year/bucket.
    """
    # Lock the award row to prevent concurrent mutations
    award = AidAward.objects.select_for_update().get(pk=award.pk)

    # Idempotent: already approved — return as-is
    if award.decision_status == AidAward.DECISION_ACCEPTED:
        return award

    # Lock the budget row for this bucket
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

    # Decrement budget *before* posting so concurrent approvals can't both succeed
    budget.awarded_cents += award.awarded_cents
    budget.save(update_fields=["awarded_cents"])

    # Ledger posting + AWARD_ACCEPTED + LEDGER_POSTED audit events (existing method)
    award.mark_accepted_and_post(actor_user=actor_user)

    # Explicit approval audit event (captures actor + reason at this level)
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
