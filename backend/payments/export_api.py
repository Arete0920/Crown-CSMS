import csv
from html import escape
from io import StringIO

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.billing_api.permissions import has_finance_runtime_role
from households.scoping import get_request_school_id
from journal.models import JournalEntry
from ledger.models import Credit, Payment as LedgerPayment
from payments.access import user_can_access_household_finance
from payments.account_api import household_finance_summary
from payments.models import (
    CanonicalRefundStatus,
    Payment as CanonicalPayment,
    Refund,
    StatementExportRequest,
    StatementExportStatus,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def household_statement_csv(request, household_id):
    school_id = get_request_school_id(request, required=True)

    if not user_can_access_household_finance(request.user, household_id):
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

    # Statement exports include the complete payment history, not merely the
    # 25-row UI preview returned by household_finance_summary.
    ledger_account = getattr(
        __import__("ledger.models", fromlist=["LedgerAccount"]),
        "LedgerAccount",
    ).objects.filter(school_id=school_id, household_id=household_id).first()
    if ledger_account is not None:
        for payment in LedgerPayment.objects.filter(
            school_id=school_id,
            account=ledger_account,
        ).order_by("created_at", "id"):
            writer.writerow(
                [
                    "payment",
                    str(payment.id),
                    str(payment.amount),
                ]
            )

    export_request.status = StatementExportStatus.GENERATED
    export_request.file_name = f"household_{household_id}_statement_{timezone.now().date()}.csv"
    export_request.generated_at = timezone.now()
    export_request.save(update_fields=["status", "file_name", "generated_at"])

    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{export_request.file_name}"'
    return response


def _require_finance_export_access(request):
    if not has_finance_runtime_role(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    return None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def finance_transaction_register_csv(request):
    """School-scoped canonical transaction/credit register for finance handoff."""
    school_id = get_request_school_id(request, required=True)
    denied = _require_finance_export_access(request)
    if denied is not None:
        return denied

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "record_type",
            "id",
            "household_id",
            "status_or_source",
            "amount",
            "currency",
            "reference",
            "created_at",
        ]
    )

    for payment in CanonicalPayment.objects.filter(school_id=school_id).order_by("created_at", "id"):
        writer.writerow(
            [
                "payment",
                str(payment.id),
                str(payment.household_id or ""),
                payment.status,
                f"{payment.amount_cents / 100:.2f}",
                payment.currency,
                payment.provider_payment_id or payment.provider_intent_id or payment.idempotency_key,
                payment.created_at.isoformat(),
            ]
        )

    for refund in Refund.objects.filter(school_id=school_id).order_by("created_at", "id"):
        writer.writerow(
            [
                "refund",
                str(refund.id),
                str(refund.payment.household_id or ""),
                refund.status,
                f"{refund.amount_cents / 100:.2f}",
                refund.currency,
                refund.provider_refund_id or refund.idempotency_key,
                refund.created_at.isoformat(),
            ]
        )

    for credit in Credit.objects.filter(school_id=school_id).order_by("created_at", "id"):
        writer.writerow(
            [
                "credit",
                str(credit.id),
                str(credit.account.household_id),
                credit.source,
                str(credit.amount),
                "USD",
                credit.reference,
                credit.created_at.isoformat(),
            ]
        )

    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="finance_transaction_register_{school_id}_{timezone.now().date()}.csv"'
    )
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def finance_journal_export_csv(request):
    """School-scoped immutable GL/journal handoff export."""
    school_id = get_request_school_id(request, required=True)
    denied = _require_finance_export_access(request)
    if denied is not None:
        return denied

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "entry_id",
            "posting_date",
            "created_at",
            "reference_type",
            "reference_id",
            "source_system",
            "currency",
            "account_code",
            "account_name",
            "debit",
            "credit",
            "memo",
        ]
    )

    entries = (
        JournalEntry.objects.filter(school_id=school_id)
        .prefetch_related("lines__account")
        .order_by("created_at", "id")
    )
    for entry in entries:
        for line in entry.lines.all():
            writer.writerow(
                [
                    str(entry.id),
                    entry.posting_date.isoformat() if entry.posting_date else "",
                    entry.created_at.isoformat(),
                    entry.reference_type or "",
                    str(entry.reference_id or ""),
                    entry.source_system,
                    entry.currency,
                    line.account.code,
                    line.account.name,
                    str(line.debit),
                    str(line.credit),
                    entry.memo,
                ]
            )

    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="finance_journal_{school_id}_{timezone.now().date()}.csv"'
    )
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_receipt_html(request, payment_id):
    school_id = get_request_school_id(request, required=True)

    payment = LedgerPayment.objects.select_related("account").filter(school_id=school_id, id=payment_id).first()
    if not payment:
        return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

    household_id = getattr(getattr(payment, "account", None), "household_id", None)
    if household_id and not user_can_access_household_finance(request.user, household_id):
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
