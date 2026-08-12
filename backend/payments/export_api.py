import csv
from decimal import Decimal
from html import escape
from io import StringIO

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from aid.models import AidAward
from billing.models import Invoice
from billing.reconciliation import compute_invoice_balance_due
from crown_api.billing_api.permissions import has_finance_runtime_role
from households.scoping import get_request_school_id
from journal.models import JournalLine
from ledger.models import Payment
from payments.access import user_can_access_household_finance
from payments.account_api import household_finance_summary
from payments.models import (
    BankStatementEntry,
    CanonicalRefundStatus,
    Payment as CanonicalPayment,
    ProviderPayoutBatch,
    Refund,
    StatementExportRequest,
    StatementExportStatus,
)


ZERO = Decimal("0.00")


def _money_from_cents(value):
    return (Decimal(int(value or 0)) / Decimal("100")).quantize(Decimal("0.01"))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def household_statement_csv(request, household_id):
    school_id = get_request_school_id(request, required=True)

    if not user_can_access_household_finance(request.user, household_id, school_id):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    export_request = StatementExportRequest.objects.create(
        school_id=school_id,
        household_id=household_id,
        format="csv",
        created_by=request.user,
    )

    summary_response = household_finance_summary(request, household_id)
    if summary_response.status_code != 200:
        export_request.status = StatementExportStatus.FAILED
        export_request.error_message = "Unable to generate household summary."
        export_request.save(update_fields=["status", "error_message"])
        return summary_response

    data = summary_response.data

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Section", "Field", "Value"])

    for key, value in (data.get("summary") or {}).items():
        writer.writerow(["summary", key, value])

    for row in data.get("invoices") or []:
        writer.writerow(["invoice", row.get("invoice_number") or row.get("id"), row.get("balance_due")])

    for row in data.get("payments") or []:
        writer.writerow(["payment", row.get("id"), row.get("amount")])

    export_request.status = StatementExportStatus.GENERATED
    export_request.file_name = f"household_{household_id}_statement_{timezone.now().date()}.csv"
    export_request.generated_at = timezone.now()
    export_request.save(update_fields=["status", "file_name", "generated_at"])

    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{export_request.file_name}"'
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def finance_handoff_csv(request):
    """Export school-scoped Finance control data from authoritative transactional sources."""
    school_id = get_request_school_id(request, required=True)
    if not has_finance_runtime_role(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "section",
            "record_id",
            "date",
            "household_id",
            "status",
            "amount",
            "debit",
            "credit",
            "currency",
            "reference",
            "detail",
        ]
    )

    payments = list(CanonicalPayment.objects.filter(school_id=school_id).order_by("id"))
    refunds = list(Refund.objects.filter(school_id=school_id).order_by("id"))
    settled_refund_total = ZERO
    payment_total = ZERO
    for payment in payments:
        amount = _money_from_cents(payment.amount_cents)
        payment_total += amount
        writer.writerow(
            [
                "payment_register",
                payment.id,
                payment.settled_at or payment.created_at,
                payment.household_id or "",
                payment.status,
                amount,
                "",
                "",
                payment.currency,
                payment.provider_payment_id or payment.idempotency_key,
                payment.provider,
            ]
        )
    for refund in refunds:
        amount = _money_from_cents(refund.amount_cents)
        if refund.status == CanonicalRefundStatus.SETTLED:
            settled_refund_total += amount
        writer.writerow(
            [
                "refund_register",
                refund.id,
                refund.settled_at or refund.requested_at,
                refund.payment.household_id or "",
                refund.status,
                amount,
                "",
                "",
                refund.currency,
                refund.provider_refund_id or refund.idempotency_key,
                f"payment:{refund.payment_id}",
            ]
        )

    today = timezone.localdate()
    ar_total = ZERO
    aging = {"current": ZERO, "1-30": ZERO, "31-60": ZERO, "61-90": ZERO, "90+": ZERO}
    invoices = Invoice.objects.filter(school_id=school_id).select_related("household").order_by("id")
    for invoice in invoices:
        balance = compute_invoice_balance_due(invoice)
        if balance <= ZERO:
            continue
        ar_total += balance
        days = (today - invoice.due_on).days if invoice.due_on else 0
        bucket = "current"
        if days > 90:
            bucket = "90+"
        elif days > 60:
            bucket = "61-90"
        elif days > 30:
            bucket = "31-60"
        elif days > 0:
            bucket = "1-30"
        aging[bucket] += balance
        writer.writerow(
            [
                "ar_aging",
                invoice.id,
                invoice.due_on or invoice.created_at,
                invoice.household_id,
                bucket,
                balance,
                "",
                "",
                "USD",
                invoice.ledger_charge_id or "",
                "open_invoice_balance",
            ]
        )

    debit_total = ZERO
    credit_total = ZERO
    journal_lines = JournalLine.objects.filter(entry__school_id=school_id).select_related("entry", "account").order_by("entry_id", "id")
    for line in journal_lines:
        debit_total += line.debit
        credit_total += line.credit
        writer.writerow(
            [
                "general_ledger",
                line.entry_id,
                line.entry.posting_date or line.entry.created_at,
                "",
                "posted",
                "",
                line.debit,
                line.credit,
                line.entry.currency,
                f"{line.entry.reference_type or ''}:{line.entry.reference_id or ''}",
                f"{line.account.code} {line.account.name}",
            ]
        )

    aid_total = ZERO
    for award in AidAward.objects.filter(school_id=school_id).select_related("student").order_by("id"):
        amount = _money_from_cents(award.awarded_cents)
        if award.decision_status == AidAward.DECISION_ACCEPTED:
            aid_total += amount
        writer.writerow(
            [
                "aid_credit",
                award.id,
                award.decided_at or award.created_at,
                "",
                award.decision_status,
                amount,
                "",
                "",
                "USD",
                award.ledger_entry_id or "",
                f"student:{award.student_id};type:{award.award_type}",
            ]
        )

    for batch in ProviderPayoutBatch.objects.filter(school_id=school_id).order_by("id"):
        writer.writerow(
            [
                "deposit_reconciliation",
                batch.id,
                batch.settled_at or batch.created_at,
                "",
                batch.status,
                batch.net_amount,
                "",
                "",
                batch.currency,
                batch.payout_id,
                f"gross={batch.gross_amount};fee={batch.fee_amount};payments={batch.expected_payment_count}",
            ]
        )
    for entry in BankStatementEntry.objects.filter(school_id=school_id).order_by("posted_date", "id"):
        writer.writerow(
            [
                "bank_statement",
                entry.id,
                entry.posted_date,
                "",
                "matched" if entry.is_matched else "unmatched",
                entry.amount,
                "",
                "",
                entry.currency,
                entry.reference,
                entry.description,
            ]
        )

    summary_rows = {
        "canonical_payment_total": payment_total,
        "settled_refund_total": settled_refund_total,
        "net_canonical_cash": payment_total - settled_refund_total,
        "ar_outstanding_total": ar_total,
        "journal_debit_total": debit_total,
        "journal_credit_total": credit_total,
        "accepted_aid_total": aid_total,
        **{f"ar_{key}": value for key, value in aging.items()},
    }
    for key, value in summary_rows.items():
        writer.writerow(["control_total", key, today, "", "", value, "", "", "USD", "", ""])

    writer.writerow(
        [
            "control_assertion",
            "journal_balanced",
            today,
            "",
            "PASS" if debit_total == credit_total else "FAIL",
            "",
            debit_total,
            credit_total,
            "USD",
            "",
            "debits must equal credits",
        ]
    )

    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="finance_handoff_{school_id}_{today}.csv"'
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_receipt_html(request, payment_id):
    school_id = get_request_school_id(request, required=True)

    payment = Payment.objects.select_related("account").filter(school_id=school_id, id=payment_id).first()
    if not payment:
        return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

    household_id = getattr(getattr(payment, "account", None), "household_id", None)
    if household_id and not user_can_access_household_finance(request.user, household_id, school_id):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    receipt_id = escape(str(payment.id))
    amount = escape(str(getattr(payment, "amount", "")))
    source = escape(str(getattr(payment, "source", "")))
    reference = escape(str(getattr(payment, "reference", "")))

    html = f"""
    <html>
      <head><title>Payment Receipt #{receipt_id}</title></head>
      <body style=\"font-family: Arial, sans-serif; padding: 24px;\">
        <h1>Payment Receipt</h1>
        <p><strong>Receipt ID:</strong> {receipt_id}</p>
        <p><strong>Amount:</strong> {amount}</p>
        <p><strong>Source:</strong> {source}</p>
        <p><strong>Reference:</strong> {reference}</p>
      </body>
    </html>
    """.strip()

    return HttpResponse(html, content_type="text/html")
