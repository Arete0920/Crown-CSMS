from decimal import Decimal

from ledger.models import Allocation


ZERO = Decimal("0.00")


def _to_decimal(value) -> Decimal:
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def compute_charge_allocated_total(charge) -> Decimal:
    """
    Computes all allocations applied to a single charge.

    IMPORTANT:
    If your related_name is not `allocations`, change only that token.
    """
    total = ZERO
    allocations = getattr(charge, "allocations", None)
    if allocations is None:
        return total

    for allocation in allocations.all():
        total += _to_decimal(getattr(allocation, "amount", ZERO))

    return total


def compute_invoice_allocated_total(invoice) -> Decimal:
    """
    Computes all allocations across all charges on an invoice.

    IMPORTANT:
    If your related_name is not `charges`, change only that token.

    Crown adaptation:
    If invoices do not expose a `charges` related_name, this function falls back
    to the invoice's `ledger_charge_id` link.
    """
    total = ZERO
    charges = getattr(invoice, "charges", None)

    if charges is not None:
        for charge in charges.all():
            total += compute_charge_allocated_total(charge)
        return total

    ledger_charge_id = getattr(invoice, "ledger_charge_id", None)
    if ledger_charge_id:
        row_total = (
            Allocation.objects.filter(
                school_id=getattr(invoice, "school_id", None),
                charge_id=ledger_charge_id,
            )
            .values_list("amount", flat=True)
        )
        for amount in row_total:
            total += _to_decimal(amount)

    return total


def compute_invoice_balance_due(invoice) -> Decimal:
    """
    Returns the real net outstanding balance:
    total invoice amount - applied allocations, never below zero.
    """
    total_amount = _to_decimal(getattr(invoice, "total_amount", ZERO))
    allocated_total = compute_invoice_allocated_total(invoice)
    balance = total_amount - allocated_total
    return balance if balance > ZERO else ZERO
