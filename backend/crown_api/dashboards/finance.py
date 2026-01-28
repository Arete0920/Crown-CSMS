"""Read-only Finance dashboard endpoints."""

from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from billing.models import Invoice
from crown_api.dashboards.tenant import get_dashboard_school_id
from ledger.models import Payment


class FinanceSummaryDashboard(APIView):
    """Finance summary: billed/paid/outstanding totals."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        school_id = get_dashboard_school_id(request, required=True)

        billed = (
            Invoice.objects.filter(school_id=school_id).aggregate(total=Sum("total_amount"))["total"]
            or 0
        )
        paid = (
            Payment.objects.filter(school_id=school_id).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        outstanding = billed - paid

        return Response(
            {
                "school_id": str(school_id),
                "billed_total": str(billed),
                "paid_total": str(paid),
                "outstanding_total": str(outstanding),
            }
        )


# Back-compat with existing URL imports
FinanceSummaryView = FinanceSummaryDashboard
