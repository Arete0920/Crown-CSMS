"""Read-only Finance dashboard endpoints."""

from decimal import Decimal

from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from crown_api.dashboards.tenant import get_dashboard_school_id
from ledger.models import Allocation, Charge, Credit, Payment
from payments.models import CanonicalRefundStatus, Refund


def _sum_decimal(queryset, field):
    return queryset.aggregate(total=Sum(field))["total"] or Decimal("0.00")


def _cents_to_decimal(value):
    return (Decimal(int(value or 0)) / Decimal("100")).quantize(Decimal("0.01"))


class FinanceSummaryDashboard(APIView):
    """
    Finance summary reconciled to canonical Student Accounts effects.

    Receivables are derived from ledger charges - cash allocations - non-cash
    credits. Gross cash, settled refunds, net cash, and unapplied cash are
    reported separately so the dashboard never hides a reconciliation gap by
    subtracting unrelated gross payments from invoice totals.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        school_id = get_dashboard_school_id(request, required=True)

        charge_total = _sum_decimal(
            Charge.objects.filter(school_id=school_id, is_void=False),
            "amount",
        )
        gross_cash_total = _sum_decimal(
            Payment.objects.filter(school_id=school_id, is_void=False),
            "amount",
        )
        allocated_cash_total = _sum_decimal(
            Allocation.objects.filter(
                school_id=school_id,
                charge__is_void=False,
                payment__is_void=False,
            ),
            "amount",
        )
        credit_total = _sum_decimal(
            Credit.objects.filter(school_id=school_id, is_void=False),
            "amount",
        )
        settled_refund_cents = (
            Refund.objects.filter(
                school_id=school_id,
                status=CanonicalRefundStatus.SETTLED,
            ).aggregate(total=Sum("amount_cents"))["total"]
            or 0
        )
        refund_total = _cents_to_decimal(settled_refund_cents)

        outstanding_total = charge_total - allocated_cash_total - credit_total
        unapplied_cash_total = gross_cash_total - allocated_cash_total
        net_cash_total = gross_cash_total - refund_total

        return Response(
            {
                "school_id": str(school_id),
                # Backward-compatible keys now reconciled to Student Accounts truth.
                "billed_total": str(charge_total),
                "paid_total": str(gross_cash_total),
                "outstanding_total": str(outstanding_total),
                # Explicit control totals for finance operators and audit proof.
                "charge_total": str(charge_total),
                "allocated_cash_total": str(allocated_cash_total),
                "credit_total": str(credit_total),
                "gross_cash_total": str(gross_cash_total),
                "refund_total": str(refund_total),
                "net_cash_total": str(net_cash_total),
                "unapplied_cash_total": str(unapplied_cash_total),
            }
        )


# Back-compat with existing URL imports
FinanceSummaryView = FinanceSummaryDashboard
