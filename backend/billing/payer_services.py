from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_DOWN

from django.db import transaction

from .models import BillingResponsibilityRule, Invoice, InvoicePayerShare


_CENT = Decimal("0.01")
_FULL_BPS = 10000


def _allocate_by_bps(amount: Decimal, rules: list[BillingResponsibilityRule]) -> dict:
    """Allocate one line amount exactly to cents; final payer receives rounding remainder."""
    if not rules:
        return {}
    total_bps = sum(int(rule.percentage_bps) for rule in rules)
    if total_bps != _FULL_BPS:
        raise ValueError("Active payer responsibility percentages must total 10000 basis points.")

    amount = Decimal(str(amount)).quantize(_CENT)
    allocations = {}
    assigned = Decimal("0.00")
    for rule in rules[:-1]:
        share = (amount * Decimal(rule.percentage_bps) / Decimal(_FULL_BPS)).quantize(
            _CENT, rounding=ROUND_DOWN
        )
        allocations[rule.payer_id] = allocations.get(rule.payer_id, Decimal("0.00")) + share
        assigned += share

    last = rules[-1]
    remainder = (amount - assigned).quantize(_CENT)
    allocations[last.payer_id] = allocations.get(last.payer_id, Decimal("0.00")) + remainder
    return allocations


def _rules_for_line(invoice: Invoice, line) -> list[BillingResponsibilityRule]:
    common = BillingResponsibilityRule.objects.filter(
        school_id=invoice.school_id,
        household_id=invoice.household_id,
        charge_type=invoice.billing_run.run_type,
        is_active=True,
        payer__is_active=True,
    ).select_related("payer")

    student_rules = list(common.filter(student_id=line.student_id).order_by("created_at", "id"))
    if student_rules:
        return student_rules
    return list(common.filter(student__isnull=True).order_by("created_at", "id"))


@transaction.atomic
def generate_payer_shares_for_invoice(invoice: Invoice) -> list[InvoicePayerShare]:
    """
    Build payer-facing sub-obligations from invoice lines.

    The household invoice and its ledger charge remain canonical AR truth.
    Existing shares make this operation idempotent. Responsibility rules are
    snapshotted into InvoicePayerShare amounts at invoice creation time so later
    rule changes do not rewrite historical responsibility.
    """
    existing = list(
        InvoicePayerShare.objects.filter(
            school_id=invoice.school_id,
            invoice=invoice,
        ).select_related("payer")
    )
    if existing:
        return existing

    totals = defaultdict(lambda: Decimal("0.00"))
    any_rules = False

    for line in invoice.lines.select_related("student").order_by("id"):
        rules = _rules_for_line(invoice, line)
        if not rules:
            continue
        any_rules = True
        for payer_id, amount in _allocate_by_bps(line.amount, rules).items():
            totals[payer_id] += amount

    if not any_rules:
        return []

    allocated_total = sum(totals.values(), Decimal("0.00")).quantize(_CENT)
    invoice_total = Decimal(str(invoice.total_amount)).quantize(_CENT)
    if allocated_total != invoice_total:
        raise ValueError("Payer responsibility rules do not cover the full invoice amount.")

    return [
        InvoicePayerShare.objects.create(
            school_id=invoice.school_id,
            invoice=invoice,
            payer_id=payer_id,
            amount=amount.quantize(_CENT),
        )
        for payer_id, amount in sorted(totals.items(), key=lambda item: str(item[0]))
    ]
