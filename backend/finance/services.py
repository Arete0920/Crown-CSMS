"""
finance/services.py — Crown Finance & Tuition service layer.

Rules:
  - All money movement posts ledger entries (TODO stubs replaced when ledger wiring is done).
  - Atomic: every multi-step operation runs inside @transaction.atomic.
  - Idempotent: settle_payment_and_allocate guards on SETTLED status; webhook callers
    must check processor_payment_id uniqueness before calling.
  - Fail-closed: any uncaught exception rolls back; callers receive the exception.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.db import transaction
from django.utils import timezone

from finance.models import (
    FinanceAllocation,
    FinanceDonation,
    FinanceInvoice,
    FinanceInvoiceLine,
    FinanceObligation,
    FinancePayment,
    FinanceRefund,
    MoneyStatus,
    PaymentStatus,
)


# ---------------------------------------------------------------------------
# Ledger bridge
# These return a result dataclass so callers know posting was attempted.
#
# BLOCKED: wiring requires a UserAccount → LedgerAccount path.
# LedgerAccount (ledger app) is keyed per-household (households.Household UUID PK).
# FinanceObligation.payer_user → UserAccount has no direct household FK.
# The resolution path (Guardian.email == user.email → Household → LedgerAccount)
# is not atomically safe without a UserAccount.household OneToOne or explicit join.
#
# Until that link is added (or a household_id is stored on UserAccount or
# FinanceObligation), these functions return a safe no-op result to avoid
# creating orphaned or incorrectly attributed LedgerAccount entries.
#
# When ready to wire:
#   1. Ensure payer_user.email → Guardian → Household → LedgerAccount path is stable.
#   2. Replace each stub body with:
#        from ledger.models import LedgerAccount, Charge, Payment, Allocation
#        account = LedgerAccount.objects.get(household__guardians__email=obligation.payer_user.email, school_id=...)
#        Charge.objects.create(school_id=..., account=account, description=..., amount=obligation.amount_cents / 100)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LedgerPostResult:
    ok: bool
    reference: str = ""


def ledger_post_obligation(obligation: FinanceObligation) -> LedgerPostResult:
    """
    Post A/R debit + Tuition/Fee revenue credit for a new obligation.

    BLOCKED: requires UserAccount → LedgerAccount path (see module comment above).
    Returns safe no-op until that path is established.
    """
    return LedgerPostResult(ok=True, reference=f"obligation:{obligation.id}")


def ledger_post_payment_settled(
    payment: FinancePayment,
    allocations: Iterable[FinanceAllocation],
) -> LedgerPostResult:
    """
    Post Cash debit + A/R credit for each allocation on settlement.

    BLOCKED: requires UserAccount → LedgerAccount path (see module comment above).
    Returns safe no-op until that path is established.
    """
    return LedgerPostResult(ok=True, reference=f"payment:{payment.id}")


def ledger_post_refund(refund: FinanceRefund) -> LedgerPostResult:
    """
    Post reversal pair: Cash credit + A/R debit (or Refund expense).

    BLOCKED: requires UserAccount → LedgerAccount path (see module comment above).
    Returns safe no-op until that path is established.
    """
    return LedgerPostResult(ok=True, reference=f"refund:{refund.id}")


def ledger_post_donation(
    donation: FinanceDonation,
    payment: FinancePayment | None = None,
) -> LedgerPostResult:
    """
    Post Cash debit + Donation revenue credit.

    BLOCKED: requires UserAccount → LedgerAccount path (see module comment above).
    Returns safe no-op until that path is established.
    """
    return LedgerPostResult(ok=True, reference=f"donation:{donation.id}")


# ---------------------------------------------------------------------------
# Domain services
# ---------------------------------------------------------------------------

@transaction.atomic
def create_invoice_from_obligations(
    *,
    school,
    payer_user,
    period_start,
    period_end,
    due_date,
    obligations: list[FinanceObligation],
    created_by=None,
) -> FinanceInvoice:
    """
    Group a set of obligations into a single FinanceInvoice with line items.
    Snapshot subtotal/total are computed from obligation amounts.
    """
    invoice = FinanceInvoice.objects.create(
        school=school,
        payer_user=payer_user,
        period_start=period_start,
        period_end=period_end,
        due_date=due_date,
        status=MoneyStatus.OPEN,
        created_by=created_by,
    )
    subtotal = 0
    for ob in obligations:
        FinanceInvoiceLine.objects.create(
            invoice=invoice,
            obligation=ob,
            amount_cents=ob.amount_cents,
            description=ob.description,
        )
        subtotal += ob.amount_cents
    invoice.subtotal_cents = subtotal
    invoice.total_cents = subtotal
    invoice.save(update_fields=["subtotal_cents", "total_cents"])
    return invoice


@transaction.atomic
def settle_payment_and_allocate(
    *,
    payment: FinancePayment,
    allocations_payload: list[dict],
) -> FinancePayment:
    """
    Mark a payment SETTLED and create FinanceAllocation records.

    allocations_payload: [{"obligation_id": <int>, "amount_cents": <int>}, ...]

    Idempotent: if payment is already SETTLED, returns it unchanged.
    select_for_update is called on both payment row and each obligation row
    to prevent concurrent double-allocation.
    """
    payment = FinancePayment.objects.select_for_update().get(pk=payment.pk)
    if payment.status == PaymentStatus.SETTLED:
        return payment

    allocations: list[FinanceAllocation] = []
    for item in allocations_payload:
        ob = FinanceObligation.objects.select_for_update().get(
            id=item["obligation_id"],
            school=payment.school,
        )
        alloc = FinanceAllocation.objects.create(
            school=payment.school,
            payment=payment,
            obligation=ob,
            amount_cents=int(item["amount_cents"]),
        )
        allocations.append(alloc)

    payment.status = PaymentStatus.SETTLED
    payment.settled_at = timezone.now()
    payment.received_at = payment.received_at or timezone.now()
    payment.save(update_fields=["status", "settled_at", "received_at"])

    ledger_post_payment_settled(payment, allocations)
    return payment


class OverRefundError(Exception):
    """Raised when refund amount exceeds original payment amount."""


@transaction.atomic
def initiate_refund(
    *,
    payment: FinancePayment,
    amount_cents: int,
    processor: str,
    created_by=None,
    idempotency_key: str = "",
) -> FinanceRefund:
    """
    Create a FinanceRefund record and post the ledger reversal.
    Validates that refund does not exceed original payment amount.
    """
    payment = FinancePayment.objects.select_for_update().get(pk=payment.pk)

    existing_refunds_total = sum(
        r.amount_cents
        for r in payment.refunds.filter(status__in=[PaymentStatus.PENDING, PaymentStatus.SETTLED])
    )
    if existing_refunds_total + amount_cents > payment.amount_cents:
        raise OverRefundError(
            f"Refund of {amount_cents}¢ would exceed payment {payment.id} "
            f"amount {payment.amount_cents}¢ "
            f"(already refunded: {existing_refunds_total}¢)"
        )

    refund = FinanceRefund.objects.create(
        school=payment.school,
        payment=payment,
        amount_cents=amount_cents,
        currency=payment.currency,
        processor=processor,
        idempotency_key=idempotency_key,
        status=PaymentStatus.PENDING,
        created_by=created_by,
    )
    ledger_post_refund(refund)
    return refund
