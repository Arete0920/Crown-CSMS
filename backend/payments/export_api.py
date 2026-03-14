import csv
from io import StringIO

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from households.scoping import get_request_school_id
from ledger.models import Payment
from payments.access import user_can_access_household_finance
from payments.account_api import household_finance_summary
from payments.models import StatementExportRequest, StatementExportStatus


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
def payment_receipt_html(request, payment_id):
    school_id = get_request_school_id(request, required=True)

    payment = Payment.objects.select_related("account").filter(school_id=school_id, id=payment_id).first()
    if not payment:
        return Response({"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

    household_id = getattr(getattr(payment, "account", None), "household_id", None)
    if household_id and not user_can_access_household_finance(request.user, household_id):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    html = f"""
    <html>
      <head><title>Payment Receipt #{payment.id}</title></head>
      <body style=\"font-family: Arial, sans-serif; padding: 24px;\">
        <h1>Payment Receipt</h1>
        <p><strong>Receipt ID:</strong> {payment.id}</p>
        <p><strong>Amount:</strong> {getattr(payment, 'amount', '')}</p>
        <p><strong>Source:</strong> {getattr(payment, 'source', '')}</p>
        <p><strong>Reference:</strong> {getattr(payment, 'reference', '')}</p>
      </body>
    </html>
    """.strip()

    return HttpResponse(html, content_type="text/html")
