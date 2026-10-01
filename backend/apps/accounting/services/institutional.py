from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounting.models.institutional import PayableBill, PurchaseOrder
from journal.services import create_reversal_entry, post_journal_entry


def _dimension_payload(*, fund=None, dimension=None):
    payload = {
        "fund_code": fund.code if fund else "",
        "department_code": "",
        "program_code": "",
        "campus_code": "",
        "project_code": "",
    }
    if dimension:
        field = {
            "DEPARTMENT": "department_code",
            "PROGRAM": "program_code",
            "CAMPUS": "campus_code",
            "PROJECT": "project_code",
        }.get(dimension.kind)
        if not field:
            raise ValidationError("Unsupported accounting dimension kind.")
        payload[field] = dimension.code
    return payload


def _assert_bill_lines_match_total(bill: PayableBill) -> None:
    lines = list(bill.lines.select_related("expense_account", "fund", "dimension").all())
    if not lines:
        raise ValidationError("Payable bill requires at least one line.")
    line_total = sum((line.amount for line in lines), Decimal("0.00"))
    if line_total != bill.total_amount:
        raise ValidationError(
            f"Payable bill lines total {line_total} does not equal bill total {bill.total_amount}."
        )


@transaction.atomic
def submit_purchase_order(*, purchase_order: PurchaseOrder) -> PurchaseOrder:
    purchase_order = PurchaseOrder.objects.select_for_update().get(pk=purchase_order.pk)
    if purchase_order.status != PurchaseOrder.Status.DRAFT:
        raise ValidationError("Only draft purchase orders may be submitted.")
    if not purchase_order.lines.exists():
        raise ValidationError("Purchase order requires at least one line.")
    purchase_order.status = PurchaseOrder.Status.SUBMITTED
    purchase_order.save(update_fields=["status", "updated_at"])
    return purchase_order


@transaction.atomic
def approve_purchase_order(*, purchase_order: PurchaseOrder, actor_id) -> PurchaseOrder:
    purchase_order = PurchaseOrder.objects.select_for_update().get(pk=purchase_order.pk)
    if purchase_order.status not in {PurchaseOrder.Status.DRAFT, PurchaseOrder.Status.SUBMITTED}:
        raise ValidationError("Purchase order is not eligible for approval.")
    lines = list(purchase_order.lines.select_related("account", "fund", "dimension"))
    if not lines:
        raise ValidationError("Purchase order requires at least one line.")
    for line in lines:
        line.full_clean()
    purchase_order.status = PurchaseOrder.Status.APPROVED
    purchase_order.approved_by = actor_id
    purchase_order.approved_at = timezone.now()
    purchase_order.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    return purchase_order


@transaction.atomic
def approve_payable_bill(*, bill: PayableBill, actor_id) -> PayableBill:
    bill = PayableBill.objects.select_for_update().get(pk=bill.pk)
    if bill.status != PayableBill.Status.DRAFT:
        raise ValidationError("Only draft payable bills may be approved.")
    _assert_bill_lines_match_total(bill)
    for line in bill.lines.select_related("expense_account", "fund", "dimension"):
        line.full_clean()
    bill.status = PayableBill.Status.APPROVED
    bill.approved_by = actor_id
    bill.approved_at = timezone.now()
    bill.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    return bill


@transaction.atomic
def post_payable_bill(*, bill: PayableBill, created_by) -> PayableBill:
    """Post an approved vendor bill into the canonical journal.

    Vendor payment itself is intentionally not created here. External money
    movement remains owned by the Payments bounded context.
    """
    bill = (
        PayableBill.objects.select_for_update()
        .select_related("liability_account", "vendor", "journal_entry")
        .get(pk=bill.pk)
    )
    if bill.status == PayableBill.Status.POSTED and bill.journal_entry_id:
        return bill
    if bill.status != PayableBill.Status.APPROVED:
        raise ValidationError("Only approved payable bills may be posted.")
    _assert_bill_lines_match_total(bill)

    journal_lines = []
    for line in bill.lines.select_related("expense_account", "fund", "dimension"):
        journal_lines.append(
            {
                "account": line.expense_account,
                "debit": line.amount,
                "credit": Decimal("0.00"),
                **_dimension_payload(fund=line.fund, dimension=line.dimension),
            }
        )
    journal_lines.append(
        {
            "account": bill.liability_account,
            "debit": Decimal("0.00"),
            "credit": bill.total_amount,
        }
    )

    entry = post_journal_entry(
        school=bill.liability_account.school,
        created_by=created_by,
        lines=journal_lines,
        memo=f"Vendor bill {bill.bill_number} - {bill.vendor}",
        reference_type="accounts_payable_bill",
        reference_id=bill.id,
        source_system="apps.accounting",
        currency=bill.currency,
        posting_date=bill.bill_date,
    )
    bill.journal_entry = entry
    bill.status = PayableBill.Status.POSTED
    bill.posted_at = timezone.now()
    bill.save(update_fields=["journal_entry", "status", "posted_at", "updated_at"])
    return bill


@transaction.atomic
def void_payable_bill(*, bill: PayableBill, reason: str) -> PayableBill:
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Voiding a payable bill requires a reason.")
    bill = PayableBill.objects.select_for_update().select_related("journal_entry").get(pk=bill.pk)
    if bill.status == PayableBill.Status.VOID:
        return bill
    if bill.status == PayableBill.Status.PAID:
        raise ValidationError("Paid bills cannot be voided; reverse the payment first.")
    if bill.journal_entry_id:
        create_reversal_entry(
            original_entry=bill.journal_entry,
            reason=reason,
            reference_type="accounts_payable_bill_void",
        )
    bill.status = PayableBill.Status.VOID
    bill.save(update_fields=["status", "updated_at"])
    return bill
