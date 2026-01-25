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


from decimal import Decimal
from django.db.models import Sum

from .models import Charge, Payment
from .models import Allocation as PaymentAllocation


def _d(x) -> Decimal:
    return Decimal(str(x))


def build_account_statement(*, school_id, account) -> dict:
    """
    Read-only statement.
    - Entries: CHARGE, PAYMENT_ALLOCATION (with payment source)
    - Sorted by timestamp (created_at) then id
    - Running balance = charges - allocations applied to charges
    """
    charges = (
        Charge.objects.filter(school_id=school_id, account=account)
        .order_by("created_at", "id")
    )

    allocs = (
        PaymentAllocation.objects.filter(school_id=school_id, charge__account=account)
        .select_related("payment", "charge")
        .order_by("created_at", "id")
    )

    entries = []
    running = Decimal("0.00")

    for ch in charges:
        amt = _d(ch.amount)
        running += amt
        entries.append(
            {
                "type": "CHARGE",
                "id": str(ch.id),
                "charge_id": str(ch.id),
                "payment_id": None,
                "source": None,
                "description": getattr(ch, "description", ""),
                "amount": str(amt),
                "direction": "DEBIT",
                "created_at": ch.created_at.isoformat() if getattr(ch, "created_at", None) else None,
                "running_balance": str(running),
            }
        )

    for al in allocs:
        amt = _d(al.amount)
        running -= amt
        p = al.payment
        entries.append(
            {
                "type": "PAYMENT_ALLOCATION",
                "id": str(al.id),
                "charge_id": str(al.charge_id),
                "payment_id": str(al.payment_id),
                "source": getattr(p, "source", "EXTERNAL"),
                "reference": getattr(p, "reference", ""),
                "description": getattr(p, "reference", "") or getattr(p, "source", "EXTERNAL"),
                "amount": str(amt),
                "direction": "CREDIT",
                "created_at": al.created_at.isoformat() if getattr(al, "created_at", None) else None,
                "running_balance": None,  # computed after sorting
            }
        )

    # Re-sort merged events by created_at then id, then recompute running
    def _sort_key(e):
        return (e["created_at"] or "", e["id"])

    entries = sorted(entries, key=_sort_key)

    running = Decimal("0.00")
    for e in entries:
        amt = _d(e["amount"])
        if e["direction"] == "DEBIT":
            running += amt
        else:
            running -= amt
        e["running_balance"] = str(running)

    return {
        "account_id": str(account.id),
        "school_id": str(school_id),
        "balance": str(running),
        "entries": entries,
    }


def billing_run_summary(*, school_id, billing_run) -> dict:
    """
    Read-only billing run summary (gross vs aid vs net due).
    - gross_total: sum(invoice.total_amount)
    - aid_applied_total: allocations where payment.source == FINANCIAL_AID against invoice charge
    - net_due_total: gross_total - aid_applied_total (clamped >= 0)
    """
    from django.db.models import Sum
    from billing.models import Invoice

    invoices = Invoice.objects.filter(school_id=school_id, billing_run=billing_run)

    gross = invoices.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")

    # collect charge ids from invoices
    charge_ids = [inv.ledger_charge_id for inv in invoices if inv.ledger_charge_id]
    aid_total = Decimal("0.00")
    if charge_ids:
        aid_total = (
            PaymentAllocation.objects.filter(
                school_id=school_id,
                charge_id__in=charge_ids,
                payment__source="FINANCIAL_AID",
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

    net = _d(gross) - _d(aid_total)
    if net < Decimal("0.00"):
        net = Decimal("0.00")

    return {
        "billing_run_id": str(billing_run.id),
        "term": getattr(billing_run, "term", ""),
        "gross_total": str(_d(gross)),
        "aid_applied_total": str(_d(aid_total)),
        "net_due_total": str(net),
        "invoice_count": invoices.count(),
    }
