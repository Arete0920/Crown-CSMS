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
from decimal import Decimal
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
from households.models import Guardian as HouseholdGuardian
from ledger.models import Allocation as LedgerAllocation
from ledger.models import Charge as LedgerCharge
from ledger.models import LedgerAccount
from ledger.models import Payment as LedgerPayment


# ---------------------------------------------------------------------------
# Ledger bridge
# These functions perform real postings into the ledger app models.
# Mapping rule: UserAccount.email -> households.Guardian.email (single household).
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LedgerPostResult:
    ok: bool
    reference: str = ""


def _money_from_cents(cents: int) -> Decimal:
    return (Decimal(int(cents)) / Decimal("100")).quantize(Decimal("0.01"))


def _resolve_ledger_account_for_user(*, school_id, user) -> LedgerAccount | None:
    email = (getattr(user, "email", "") or "").strip()
    if not email:
        return None

    household_ids = list(
        HouseholdGuardian.objects
        .filter(school_id=school_id, email__iexact=email)
        .values_list("household_id", flat=True)
        .distinct()
    )
    if len(household_ids) != 1:
        return None

    acct, _ = LedgerAccount.objects.get_or_create(
        school_id=school_id,
        household_id=household_ids[0],
    )
    return acct


def ledger_post_obligation(obligation: FinanceObligation) -> LedgerPostResult:
    """
    Post A/R debit + Tuition/Fee revenue credit for a new obligation.
    """
    account = _resolve_ledger_account_for_user(
        school_id=obligation.school_id,
        user=obligation.payer_user,
    )
    if account is None:
        return LedgerPostResult(ok=False, reference=f"unmapped_payer:{obligation.payer_user_id}")

    amount = _money_from_cents(obligation.amount_cents)
    charge, _ = LedgerCharge.objects.get_or_create(
        school_id=obligation.school_id,
        account=account,
        description=f"finance_obligation:{obligation.id}",
        defaults={"amount": amount},
    )
    return LedgerPostResult(ok=True, reference=f"charge:{charge.id}")


def ledger_post_payment_settled(
    payment: FinancePayment,
    allocations: Iterable[FinanceAllocation],
) -> LedgerPostResult:
    """
    Post Cash debit + A/R credit for each allocation on settlement.
    """
    account = _resolve_ledger_account_for_user(
        school_id=payment.school_id,
        user=payment.payer_user,
    )
    if account is None:
        return LedgerPostResult(ok=False, reference=f"unmapped_payer:{payment.payer_user_id}")

    ledger_payment, _ = LedgerPayment.objects.get_or_create(
        school_id=payment.school_id,
        account=account,
        source="FINANCE_SETTLED",
        reference=f"finance_payment:{payment.id}",
        defaults={"amount": _money_from_cents(payment.amount_cents)},
    )

    for alloc in allocations:
        post_result = ledger_post_obligation(alloc.obligation)
        if not post_result.ok:
            return post_result

        charge_id = str(post_result.reference).split("charge:", 1)[-1]
        charge = LedgerCharge.objects.filter(
            school_id=payment.school_id,
            id=charge_id,
            account=account,
        ).first()
        if charge is None:
            return LedgerPostResult(ok=False, reference=f"missing_charge_for_obligation:{alloc.obligation_id}")

        LedgerAllocation.objects.get_or_create(
            school_id=payment.school_id,
            payment=ledger_payment,
            charge=charge,
            defaults={"amount": _money_from_cents(alloc.amount_cents)},
        )

    return LedgerPostResult(ok=True, reference=f"payment:{ledger_payment.id}")


def ledger_post_refund(refund: FinanceRefund) -> LedgerPostResult:
    """
    Post reversal pair: Cash credit + A/R debit (or Refund expense).
    """
    account = _resolve_ledger_account_for_user(
        school_id=refund.school_id,
        user=refund.payment.payer_user,
    )
    if account is None:
        return LedgerPostResult(ok=False, reference=f"unmapped_payer:{refund.payment.payer_user_id}")

    charge, _ = LedgerCharge.objects.get_or_create(
        school_id=refund.school_id,
        account=account,
        description=f"finance_refund:{refund.id}",
        defaults={"amount": _money_from_cents(refund.amount_cents)},
    )
    return LedgerPostResult(ok=True, reference=f"refund_charge:{charge.id}")


def ledger_post_donation(
    donation: FinanceDonation,
    payment: FinancePayment | None = None,
) -> LedgerPostResult:
    """
    Post Cash debit + Donation revenue credit.
    """
    account = _resolve_ledger_account_for_user(
        school_id=donation.school_id,
        user=donation.donor_user,
    )
    if account is None:
        return LedgerPostResult(ok=False, reference=f"unmapped_donor:{donation.donor_user_id}")

    ledger_payment, _ = LedgerPayment.objects.get_or_create(
        school_id=donation.school_id,
        account=account,
        source="DONATION",
        reference=f"finance_donation:{donation.id}",
        defaults={"amount": _money_from_cents(donation.amount_cents)},
    )
    return LedgerPostResult(ok=True, reference=f"donation_payment:{ledger_payment.id}")


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

    post_result = ledger_post_payment_settled(payment, allocations)
    if not post_result.ok:
        raise ValueError(f"Ledger posting failed: {post_result.reference}")
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
    post_result = ledger_post_refund(refund)
    if not post_result.ok:
        raise ValueError(f"Ledger refund posting failed: {post_result.reference}")
    return refund
