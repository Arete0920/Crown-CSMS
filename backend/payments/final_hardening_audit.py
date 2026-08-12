"""Read-only Finance final-hardening audit for demo or target-school data."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from finance.models import FinanceAllocation
from households.models import Household
from journal.models import JournalEntry
from ledger.models import Allocation as LedgerAllocation
from ledger.models import Charge as LedgerCharge
from ledger.models import LedgerAccount
from ledger.models import Payment as LedgerPayment
from payments.compatibility_audit import audit_payment_compatibility
from payments.models import CanonicalPaymentStatus, CanonicalRefundStatus, Payment


@dataclass
class FinanceHardeningAuditResult:
    checked_payments: int = 0
    checked_journal_entries: int = 0
    checked_finance_allocations: int = 0
    checked_ledger_allocations: int = 0
    checked_trace_links: int = 0
    findings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings


def _finding(result, value):
    if value not in result.findings:
        result.findings.append(value)


def _audit_payment_trace(result, payment):
    """Prove canonical payment -> Finance -> Student Accounts -> Journal lineage."""
    if payment.status not in {
        CanonicalPaymentStatus.SETTLED,
        CanonicalPaymentStatus.PARTIALLY_REFUNDED,
        CanonicalPaymentStatus.REFUNDED,
    }:
        return
    if not payment.finance_payment_id:
        _finding(result, f"payment:{payment.pk}:settled without FinancePayment compatibility link")
        return

    ledger_payments = LedgerPayment.objects.filter(
        school_id=payment.school_id,
        reference=f"finance_payment:{payment.finance_payment_id}",
        is_void=False,
    )
    if ledger_payments.count() != 1:
        _finding(
            result,
            f"payment:{payment.pk}:expected one ledger payment for finance_payment:{payment.finance_payment_id}; found={ledger_payments.count()}",
        )
        return
    ledger_payment = ledger_payments.get()
    result.checked_trace_links += 1

    journal_count = JournalEntry.objects.filter(
        school_id=payment.school_id,
        reference_type="payment",
        reference_id=ledger_payment.pk,
    ).count()
    if journal_count != 1:
        _finding(
            result,
            f"payment:{payment.pk}:ledger payment:{ledger_payment.pk}:expected one journal payment entry; found={journal_count}",
        )
    else:
        result.checked_trace_links += 1

    finance_allocations = FinanceAllocation.objects.filter(
        school_id=payment.school_id,
        payment_id=payment.finance_payment_id,
    ).select_related("obligation")
    for allocation in finance_allocations:
        charges = LedgerCharge.objects.filter(
            school_id=payment.school_id,
            account_id=ledger_payment.account_id,
            description=f"finance_obligation:{allocation.obligation_id}",
            is_void=False,
        )
        if charges.count() != 1:
            _finding(
                result,
                f"payment:{payment.pk}:obligation:{allocation.obligation_id}:expected one ledger charge; found={charges.count()}",
            )
            continue
        charge = charges.get()
        result.checked_trace_links += 1
        ledger_allocations = LedgerAllocation.objects.filter(
            school_id=payment.school_id,
            payment=ledger_payment,
            charge=charge,
        )
        if ledger_allocations.count() != 1:
            _finding(
                result,
                f"payment:{payment.pk}:obligation:{allocation.obligation_id}:expected one ledger allocation; found={ledger_allocations.count()}",
            )
            continue
        ledger_allocation = ledger_allocations.get()
        expected = (Decimal(int(allocation.amount_cents)) / Decimal("100")).quantize(Decimal("0.01"))
        if ledger_allocation.amount != expected:
            _finding(
                result,
                f"payment:{payment.pk}:obligation:{allocation.obligation_id}:allocation amount mismatch finance={expected} ledger={ledger_allocation.amount}",
            )
        else:
            result.checked_trace_links += 1

    for refund in payment.refunds.filter(status=CanonicalRefundStatus.SETTLED):
        if not refund.finance_refund_id:
            _finding(result, f"refund:{refund.pk}:settled without FinanceRefund compatibility link")
            continue
        refund_charges = LedgerCharge.objects.filter(
            school_id=payment.school_id,
            description=f"finance_refund:{refund.finance_refund_id}",
            is_void=False,
        )
        if refund_charges.count() != 1:
            _finding(
                result,
                f"refund:{refund.pk}:expected one refund ledger charge; found={refund_charges.count()}",
            )
            continue
        refund_charge = refund_charges.get()
        result.checked_trace_links += 1
        journal_count = JournalEntry.objects.filter(
            school_id=payment.school_id,
            reference_type="finance_refund",
            reference_id=refund_charge.pk,
        ).count()
        if journal_count != 1:
            _finding(
                result,
                f"refund:{refund.pk}:ledger charge:{refund_charge.pk}:expected one refund journal entry; found={journal_count}",
            )
        else:
            result.checked_trace_links += 1


def audit_finance_hardening(*, school_id) -> FinanceHardeningAuditResult:
    """Run strict, read-only money, traceability, and tenant invariants for one school."""
    result = FinanceHardeningAuditResult()

    compatibility = audit_payment_compatibility(school_id=school_id)
    result.findings.extend(f"compatibility:{item}" for item in compatibility.mismatches)
    result.findings.extend(
        f"compatibility:orphan FinancePayment:{legacy_id}"
        for legacy_id in compatibility.orphan_legacy_payments
    )

    payments = Payment.objects.filter(school_id=school_id).prefetch_related("refunds")
    for payment in payments.order_by("pk"):
        result.checked_payments += 1
        refunds = list(payment.refunds.all())
        active_refunds = [
            refund
            for refund in refunds
            if refund.status in {
                CanonicalRefundStatus.REQUESTED,
                CanonicalRefundStatus.PENDING,
                CanonicalRefundStatus.SETTLED,
            }
        ]
        reserved = sum(int(refund.amount_cents) for refund in active_refunds)
        settled = sum(
            int(refund.amount_cents)
            for refund in refunds
            if refund.status == CanonicalRefundStatus.SETTLED
        )
        if reserved > int(payment.amount_cents):
            _finding(result, f"payment:{payment.pk}:refund reservations {reserved} exceed payment {payment.amount_cents}")
        if payment.status == CanonicalPaymentStatus.REFUNDED and settled != int(payment.amount_cents):
            _finding(result, f"payment:{payment.pk}:REFUNDED status but settled refunds={settled} payment={payment.amount_cents}")
        if payment.status == CanonicalPaymentStatus.PARTIALLY_REFUNDED and not (0 < settled < int(payment.amount_cents)):
            _finding(result, f"payment:{payment.pk}:PARTIALLY_REFUNDED status inconsistent with settled refunds={settled}")
        if payment.household_id is not None:
            household = Household.objects.filter(pk=payment.household_id).first()
            if household is None:
                _finding(result, f"payment:{payment.pk}:household:{payment.household_id}:missing")
            elif str(household.school_id) != str(payment.school_id):
                _finding(result, f"payment:{payment.pk}:household school mismatch household={household.school_id} payment={payment.school_id}")
        _audit_payment_trace(result, payment)

    finance_allocations = FinanceAllocation.objects.filter(school_id=school_id).select_related("payment", "obligation")
    for allocation in finance_allocations:
        result.checked_finance_allocations += 1
        if str(allocation.payment.school_id) != str(allocation.school_id):
            _finding(result, f"finance_allocation:{allocation.pk}:payment school mismatch")
        if str(allocation.obligation.school_id) != str(allocation.school_id):
            _finding(result, f"finance_allocation:{allocation.pk}:obligation school mismatch")
        if allocation.payment.payer_user_id != allocation.obligation.payer_user_id:
            _finding(result, f"finance_allocation:{allocation.pk}:payment/obligation payer mismatch")

    ledger_accounts = LedgerAccount.objects.filter(school_id=school_id).select_related("household")
    for account in ledger_accounts:
        if str(account.household.school_id) != str(account.school_id):
            _finding(result, f"ledger_account:{account.pk}:household school mismatch")

    ledger_allocations = LedgerAllocation.objects.filter(school_id=school_id).select_related(
        "payment", "payment__account", "charge", "charge__account"
    )
    payment_totals: dict[object, Decimal] = {}
    charge_totals: dict[object, Decimal] = {}
    for allocation in ledger_allocations:
        result.checked_ledger_allocations += 1
        if str(allocation.payment.school_id) != str(allocation.school_id):
            _finding(result, f"ledger_allocation:{allocation.pk}:payment school mismatch")
        if str(allocation.charge.school_id) != str(allocation.school_id):
            _finding(result, f"ledger_allocation:{allocation.pk}:charge school mismatch")
        if allocation.payment.account_id != allocation.charge.account_id:
            _finding(result, f"ledger_allocation:{allocation.pk}:payment and charge belong to different ledger accounts")
        payment_totals[allocation.payment_id] = payment_totals.get(allocation.payment_id, Decimal("0.00")) + allocation.amount
        charge_totals[allocation.charge_id] = charge_totals.get(allocation.charge_id, Decimal("0.00")) + allocation.amount

    seen_payments = set()
    seen_charges = set()
    for allocation in ledger_allocations:
        if allocation.payment_id not in seen_payments:
            seen_payments.add(allocation.payment_id)
            payment_total = payment_totals.get(allocation.payment_id, Decimal("0.00"))
            if payment_total > allocation.payment.amount:
                _finding(result, f"ledger_payment:{allocation.payment_id}:allocated={payment_total} exceeds amount={allocation.payment.amount}")
        if allocation.charge_id not in seen_charges:
            seen_charges.add(allocation.charge_id)
            charge_total = charge_totals.get(allocation.charge_id, Decimal("0.00"))
            if charge_total > allocation.charge.amount:
                _finding(result, f"ledger_charge:{allocation.charge_id}:allocated={charge_total} exceeds amount={allocation.charge.amount}")

    entries = JournalEntry.objects.filter(school_id=school_id).prefetch_related("lines__account")
    for entry in entries:
        result.checked_journal_entries += 1
        lines = list(entry.lines.all())
        if len(lines) < 2:
            _finding(result, f"journal_entry:{entry.pk}:fewer than two lines")
            continue
        debit = sum((line.debit for line in lines), Decimal("0.00"))
        credit = sum((line.credit for line in lines), Decimal("0.00"))
        if debit != credit:
            _finding(result, f"journal_entry:{entry.pk}:unbalanced debit={debit} credit={credit}")
        for line in lines:
            if str(line.account.school_id) != str(entry.school_id):
                _finding(result, f"journal_entry:{entry.pk}:line:{line.pk}:cross-tenant GL account")

    return result
