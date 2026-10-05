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
        if line.student.school_id != invoice.school_id or line.student.household_id != invoice.household_id:
            raise ValueError("Invoice student must belong to the same school and household.")
        rules = _rules_for_line(invoice, line)
        if not rules:
            continue
        any_rules = True
        for rule in rules:
            rule.full_clean()
            rule.payer.full_clean()
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


def payer_share_paid_amount(share):
    """Only active canonical allocations, less active canonical refund debits."""
    from django.db.models import Sum
    from .models import PayerAllocationAttribution, PayerRefundAttribution

    paid = PayerAllocationAttribution.objects.filter(
        school_id=share.school_id, share=share,
        allocation__payment__is_void=False, allocation__charge__is_void=False,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    refunded = PayerRefundAttribution.objects.filter(
        school_id=share.school_id, attribution__share=share,
        attribution__allocation__payment__is_void=False,
        attribution__allocation__charge__is_void=False,
        refund_charge__is_void=False,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    return paid - refunded


@transaction.atomic
def attribute_payer_refund(*, finance_payment, refund_charge):
    """Restore attributed responsibility without posting a second AR debit.

    Refunds consume this payer's attributions in stable creation order. An
    ambiguous refund (including a refund beyond attributed responsibility)
    fails closed rather than shifting liability to another payer.
    """
    from django.core.exceptions import ValidationError
    from django.db.models import Sum
    from ledger.models import Payment
    from .models import PayerAllocationAttribution, PayerRefundAttribution

    payment = Payment.objects.select_for_update().filter(
        school_id=finance_payment.school_id, source="FINANCE_SETTLED",
        reference=f"finance_payment:{finance_payment.id}",
    ).first()
    if payment is None:
        return
    rows = list(PayerAllocationAttribution.objects.select_for_update(of=("self",)).filter(
        school_id=finance_payment.school_id, allocation__payment=payment,
    ).select_related("share__payer__guardian", "allocation").order_by("created_at", "id"))
    if not rows:
        return
    if payment.is_void or refund_charge.account_id != payment.account_id:
        raise ValidationError("Refund payment or household mismatch.")
    if PayerRefundAttribution.objects.filter(refund_charge=refund_charge).exists():
        return
    capacities = []
    for row in rows:
        payer = row.share.payer
        identity = payer.account_id or (payer.guardian.account_id if payer.guardian_id else None)
        if identity != finance_payment.payer_user_id:
            raise ValidationError("Refund payer does not match attributed responsibility.")
        restored = row.refund_attributions.filter(refund_charge__is_void=False).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        capacities.append((row, row.amount - restored))
    remaining = refund_charge.amount
    if remaining <= 0 or remaining > sum((capacity for _, capacity in capacities), Decimal("0.00")):
        raise ValidationError("Refund exceeds attributable payer responsibility.")
    for row, capacity in capacities:
        amount = min(remaining, capacity)
        if amount > 0:
            PayerRefundAttribution.objects.create(
                school_id=finance_payment.school_id, attribution=row,
                refund_charge=refund_charge, amount=amount,
            )
            remaining -= amount


def payer_share_statement(share):
    """Allowlisted facts shared by payer statements and billing notice content."""
    share.full_clean()
    share.payer.full_clean()
    paid = payer_share_paid_amount(share)
    from ledger.models import Charge

    invoice_void = bool(share.invoice.ledger_charge_id and Charge.objects.filter(
        pk=share.invoice.ledger_charge_id, school_id=share.school_id, is_void=True
    ).exists())
    return {
        "share_id": str(share.id),
        "invoice_id": str(share.invoice_id),
        "term": share.invoice.billing_run.term,
        "charge_type": share.invoice.billing_run.run_type,
        "due_on": share.invoice.due_on.isoformat() if share.invoice.due_on else None,
        "assigned_amount": str(share.amount),
        "waived_amount": str(share.waived_amount),
        "paid_amount": str(paid),
        "balance": str(Decimal("0.00") if invoice_void else max(share.amount - share.waived_amount - paid, Decimal("0.00"))),
    }


def build_payer_billing_notice(*, share, recipient):
    """Build recipient-scoped notice content; delivery is deliberately separate."""
    from django.core.exceptions import PermissionDenied

    payer = share.payer
    identities = {payer.account_id}
    if payer.guardian_id:
        identities.add(payer.guardian.account_id)
    if not recipient.is_authenticated or recipient.pk not in identities or recipient.school_id != share.school_id:
        raise PermissionDenied("Notice recipient must be the assigned payer in this school.")
    facts = payer_share_statement(share)
    return {
        "recipient_id": recipient.pk,
        "subject": "Your CROWN billing responsibility",
        "body": f"Your assigned responsibility is {facts['assigned_amount']}. Your current balance is {facts['balance']}.",
    }
