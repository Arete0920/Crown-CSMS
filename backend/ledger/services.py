from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from django.db import transaction
from django.db.models import Sum

from .models import LedgerAccount, Charge, Payment, PaymentAllocation


@dataclass(frozen=True)
class AllocationResult:
    payment_id: UUID
    allocated_total: Decimal
    remaining_unallocated: Decimal
    allocations_created: int


def _sum_allocated_for_charge(charge: Charge) -> Decimal:
    s = charge.allocations.aggregate(total=Sum("amount"))["total"]
    return s if s is not None else Decimal("0.00")


def _sum_allocated_for_payment(payment: Payment) -> Decimal:
    s = payment.allocations.aggregate(total=Sum("amount"))["total"]
    return s if s is not None else Decimal("0.00")


def charge_remaining_balance(charge: Charge) -> Decimal:
    allocated = _sum_allocated_for_charge(charge)
    amt = getattr(charge, "amount", None)
    if amt is None:
        raise ValueError("Charge.amount field not found")
    remaining = Decimal(str(amt)) - Decimal(str(allocated))
    if remaining < Decimal("0.00"):
        remaining = Decimal("0.00")
    return remaining


def account_balance(account: LedgerAccount) -> Decimal:
    # balance = sum(charges) - sum(payments allocations)
    charges_total = account.charges.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    alloc_total = PaymentAllocation.objects.filter(school_id=account.school_id, charge__account=account).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")
    bal = Decimal(str(charges_total)) - Decimal(str(alloc_total))
    return bal


@transaction.atomic
def allocate_payment_fifo(*, school_id, payment: Payment) -> AllocationResult:
    """
    FIFO allocation across oldest charges with remaining balance.
    - Does NOT modify Charge rows (purely allocation rows).
    - Idempotent-ish: will not duplicate allocation rows per (payment, charge).
    """
    if payment.school_id != school_id:
        raise ValueError("school_id mismatch")

    pay_amount = getattr(payment, "amount", None)
    if pay_amount is None:
        raise ValueError("Payment.amount field not found")

    pay_amount = Decimal(str(pay_amount))
    already_alloc = _sum_allocated_for_payment(payment)
    remaining_to_allocate = pay_amount - Decimal(str(already_alloc))
    if remaining_to_allocate <= Decimal("0.00"):
        return AllocationResult(
            payment_id=payment.id,
            allocated_total=Decimal(str(already_alloc)),
            remaining_unallocated=Decimal("0.00"),
            allocations_created=0,
        )

    # charges FIFO (oldest first). If your Charge has a different timestamp field,
    # keep ordering by created_at if present.
    qs = Charge.objects.filter(school_id=school_id, account=payment.account).order_by("created_at", "id")

    allocations_created = 0

    for ch in qs:
        ch_rem = charge_remaining_balance(ch)
        if ch_rem <= Decimal("0.00"):
            continue
        if remaining_to_allocate <= Decimal("0.00"):
            break

        alloc_amt = ch_rem if ch_rem <= remaining_to_allocate else remaining_to_allocate

        alloc, created = PaymentAllocation.objects.get_or_create(
            school_id=school_id,
            payment=payment,
            charge=ch,
            defaults={"amount": alloc_amt},
        )
        if not created:
            # If row already exists, top it up (still keeps uniq constraint)
            current = Decimal(str(alloc.amount))
            new_amt = current + alloc_amt
            alloc.amount = new_amt
            alloc.save(update_fields=["amount"])
        allocations_created += 1

        remaining_to_allocate -= alloc_amt

    final_alloc = _sum_allocated_for_payment(payment)

    return AllocationResult(
        payment_id=payment.id,
        allocated_total=Decimal(str(final_alloc)),
        remaining_unallocated=(
            pay_amount - Decimal(str(final_alloc)) if pay_amount > Decimal(str(final_alloc)) else Decimal("0.00")
        ),
        allocations_created=allocations_created,
    )
