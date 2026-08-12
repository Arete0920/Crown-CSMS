"""Canonical Payments versus legacy Finance compatibility reconciliation."""
from __future__ import annotations

from dataclasses import dataclass, field

from finance.models import FinancePayment
from payments.models import (
    CanonicalPaymentStatus,
    CanonicalRefundStatus,
    Payment,
    Refund,
)


@dataclass
class CompatibilityAuditResult:
    checked_payments: int = 0
    checked_refunds: int = 0
    orphan_legacy_payments: list[int] = field(default_factory=list)
    mismatches: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.mismatches and not self.orphan_legacy_payments


def audit_payment_compatibility(*, school_id=None) -> CompatibilityAuditResult:
    """Compare canonical Payment/Refund facts with Finance compatibility rows.

    This is intentionally read-only. Any mismatch means legacy authority cannot be
    retired for the affected data set.
    """
    result = CompatibilityAuditResult()
    canonical_qs = Payment.objects.select_related("created_by").prefetch_related(
        "refunds"
    )
    legacy_qs = FinancePayment.objects.prefetch_related("allocations", "refunds")
    if school_id is not None:
        canonical_qs = canonical_qs.filter(school_id=school_id)
        legacy_qs = legacy_qs.filter(school_id=school_id)

    canonical_by_legacy_id = {}
    for payment in canonical_qs.order_by("pk"):
        result.checked_payments += 1
        legacy_id = payment.finance_payment_id
        if not legacy_id:
            result.mismatches.append(
                f"payment:{payment.pk}:missing finance_payment_id compatibility link"
            )
            continue
        canonical_by_legacy_id[legacy_id] = payment
        try:
            legacy = legacy_qs.get(pk=legacy_id)
        except FinancePayment.DoesNotExist:
            result.mismatches.append(
                f"payment:{payment.pk}:FinancePayment:{legacy_id}:missing"
            )
            continue

        if str(legacy.school_id) != str(payment.school_id):
            result.mismatches.append(
                f"payment:{payment.pk}:school mismatch canonical={payment.school_id} legacy={legacy.school_id}"
            )
        if int(legacy.amount_cents) != int(payment.amount_cents):
            result.mismatches.append(
                f"payment:{payment.pk}:amount mismatch canonical={payment.amount_cents} legacy={legacy.amount_cents}"
            )
        if (legacy.currency or "USD").upper() != (payment.currency or "USD").upper():
            result.mismatches.append(
                f"payment:{payment.pk}:currency mismatch canonical={payment.currency} legacy={legacy.currency}"
            )

        canonical_settled = payment.status in {
            CanonicalPaymentStatus.SETTLED,
            CanonicalPaymentStatus.PARTIALLY_REFUNDED,
            CanonicalPaymentStatus.REFUNDED,
        }
        legacy_settled = legacy.status == "settled"
        if canonical_settled != legacy_settled:
            result.mismatches.append(
                f"payment:{payment.pk}:settlement mismatch canonical={payment.status} legacy={legacy.status}"
            )

        for refund in payment.refunds.all():
            result.checked_refunds += 1
            if refund.status != CanonicalRefundStatus.SETTLED:
                continue
            if not refund.finance_refund_id:
                result.mismatches.append(
                    f"refund:{refund.pk}:settled refund missing finance_refund_id"
                )
                continue
            legacy_refund = legacy.refunds.filter(pk=refund.finance_refund_id).first()
            if legacy_refund is None:
                result.mismatches.append(
                    f"refund:{refund.pk}:FinanceRefund:{refund.finance_refund_id}:missing"
                )
                continue
            if int(legacy_refund.amount_cents) != int(refund.amount_cents):
                result.mismatches.append(
                    f"refund:{refund.pk}:amount mismatch canonical={refund.amount_cents} legacy={legacy_refund.amount_cents}"
                )
            if legacy_refund.status != "settled":
                result.mismatches.append(
                    f"refund:{refund.pk}:status mismatch canonical={refund.status} legacy={legacy_refund.status}"
                )

    for legacy in legacy_qs.order_by("pk"):
        if legacy.pk not in canonical_by_legacy_id:
            result.orphan_legacy_payments.append(legacy.pk)

    return result
