from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from django.db import transaction
from django.db.models import Sum

from .models import Charge, LedgerAccount, Payment, PaymentAllocation


@dataclass(frozen=True)
class AllocationResult:
    payment_id: UUID
    allocated_total: Decimal
    remaining_unallocated: Decimal
    allocations_created: int


def _sum_allocated_for_charge(charge: Charge) -> Decimal:
    value = charge.allocations.filter(payment__is_void=False).aggregate(total=Sum("amount"))["total"]
    return value if value is not None else Decimal("0.00")


def _sum_allocated_for_payment(payment: Payment) -> Decimal:
    value = payment.allocations.filter(charge__is_void=False).aggregate(total=Sum("amount"))["total"]
    return value if value is not None else Decimal("0.00")


def charge_remaining_balance(charge: Charge) -> Decimal:
    if charge.is_void:
        return Decimal("0.00")
    allocated = _sum_allocated_for_charge(charge)
    amount = getattr(charge, "amount", None)
    if amount is None:
        raise ValueError("Charge.amount field not found")
    remaining = Decimal(str(amount)) - Decimal(str(allocated))
    return max(remaining, Decimal("0.00"))


def account_balance(account: LedgerAccount) -> Decimal:
    charges_total = (
        account.charges.filter(is_void=False).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )
    alloc_total = (
        PaymentAllocation.objects.filter(
            school_id=account.school_id,
            charge__account=account,
            charge__is_void=False,
            payment__is_void=False,
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )
    return Decimal(str(charges_total)) - Decimal(str(alloc_total))


@transaction.atomic
def allocate_payment_fifo(*, school_id, payment: Payment) -> AllocationResult:
    """Allocate an active payment FIFO with row locks for concurrency safety."""
    payment = (
        Payment.objects.select_for_update()
        .select_related("account")
        .get(pk=payment.pk)
    )
    if payment.school_id != school_id:
        raise ValueError("school_id mismatch")
    if payment.is_void:
        raise ValueError("cannot allocate a void payment")
    if payment.account.school_id != school_id:
        raise ValueError("payment account school mismatch")

    pay_amount = Decimal(str(payment.amount))
    already_alloc = _sum_allocated_for_payment(payment)
    remaining_to_allocate = pay_amount - already_alloc
    if remaining_to_allocate <= Decimal("0.00"):
        return AllocationResult(payment.id, already_alloc, Decimal("0.00"), 0)

    charges = (
        Charge.objects.select_for_update()
        .filter(school_id=school_id, account=payment.account, is_void=False)
        .order_by("created_at", "id")
    )

    allocations_created = 0
    for charge in charges:
        if remaining_to_allocate <= Decimal("0.00"):
            break
        charge_remaining = charge_remaining_balance(charge)
        if charge_remaining <= Decimal("0.00"):
            continue

        allocation_amount = min(charge_remaining, remaining_to_allocate)
        allocation, created = PaymentAllocation.objects.get_or_create(
            school_id=school_id,
            payment=payment,
            charge=charge,
            defaults={"amount": allocation_amount},
        )
        if not created:
            current = Decimal(str(allocation.amount))
            allocation.amount = current + allocation_amount
            allocation.save(update_fields=["amount"])
        allocations_created += 1
        remaining_to_allocate -= allocation_amount

    final_alloc = _sum_allocated_for_payment(payment)
    return AllocationResult(
        payment_id=payment.id,
        allocated_total=final_alloc,
        remaining_unallocated=max(pay_amount - final_alloc, Decimal("0.00")),
        allocations_created=allocations_created,
    )


def _d(value) -> Decimal:
    return Decimal(str(value))


def build_account_statement(*, school_id, account) -> dict:
    """Read-only statement based on active charges and active payment allocations."""
    charges = Charge.objects.filter(
        school_id=school_id, account=account, is_void=False
    ).order_by("created_at", "id")
    allocations = (
        PaymentAllocation.objects.filter(
            school_id=school_id,
            charge__account=account,
            charge__is_void=False,
            payment__is_void=False,
        )
        .select_related("payment", "charge")
        .order_by("created_at", "id")
    )

    entries = []
    for charge in charges:
        entries.append({
            "type": "CHARGE",
            "id": str(charge.id),
            "charge_id": str(charge.id),
            "payment_id": None,
            "source": None,
            "description": charge.description,
            "amount": str(_d(charge.amount)),
            "direction": "DEBIT",
            "created_at": charge.created_at.isoformat() if charge.created_at else None,
            "running_balance": None,
        })

    for allocation in allocations:
        payment = allocation.payment
        entries.append({
            "type": "PAYMENT_ALLOCATION",
            "id": str(allocation.id),
            "charge_id": str(allocation.charge_id),
            "payment_id": str(allocation.payment_id),
            "source": payment.source,
            "reference": payment.reference,
            "description": payment.reference or payment.source,
            "amount": str(_d(allocation.amount)),
            "direction": "CREDIT",
            "created_at": allocation.created_at.isoformat() if allocation.created_at else None,
            "running_balance": None,
        })

    entries.sort(key=lambda entry: (entry["created_at"] or "", entry["id"]))
    running = Decimal("0.00")
    for entry in entries:
        amount = _d(entry["amount"])
        running += amount if entry["direction"] == "DEBIT" else -amount
        entry["running_balance"] = str(running)

    return {
        "account_id": str(account.id),
        "school_id": str(school_id),
        "balance": str(running),
        "entries": entries,
    }


def billing_run_summary(*, school_id, billing_run) -> dict:
    """Compatibility summary; aid-as-payment remains until the Aid credit cutover."""
    from billing.models import Invoice

    invoices = Invoice.objects.filter(school_id=school_id, billing_run=billing_run)
    gross = invoices.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    charge_ids = [invoice.ledger_charge_id for invoice in invoices if invoice.ledger_charge_id]
    aid_total = Decimal("0.00")
    if charge_ids:
        aid_total = (
            PaymentAllocation.objects.filter(
                school_id=school_id,
                charge_id__in=charge_ids,
                charge__is_void=False,
                payment__is_void=False,
                payment__source="FINANCIAL_AID",
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

    net = max(_d(gross) - _d(aid_total), Decimal("0.00"))
    return {
        "billing_run_id": str(billing_run.id),
        "term": getattr(billing_run, "term", ""),
        "gross_total": str(_d(gross)),
        "aid_applied_total": str(_d(aid_total)),
        "net_due_total": str(net),
        "invoice_count": invoices.count(),
    }
