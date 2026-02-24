from django.db.models import Max, Sum
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.access_households import resolve_household_access
from crown_api.models import Household, Invoice, Payment
from crown_api.serializers_billing import InvoiceMiniSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def household_billing_summary(request, household_id):
    if not getattr(getattr(request, "user", None), "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )

    access = resolve_household_access(request)

    if not access.is_staff:
        # No existence leak: if household isn't in-scope, return 404
        if household_id not in access.household_ids:
            raise Http404()

    invoices_total = Invoice.objects.filter(household_id=household_id).count()

    invoices_open_qs = Invoice.objects.filter(
        household_id=household_id,
        status=Invoice.STATUS_OPEN,
    )
    invoices_count_open = invoices_open_qs.count()

    open_balance_cents = (
        invoices_open_qs.aggregate(total=Coalesce(Sum("amount_cents"), 0))["total"]
        or 0
    )

    last_payment_date = Payment.objects.filter(household_id=household_id).aggregate(
        last=Max("payment_date")
    )["last"]

    recent_invoices_qs = Invoice.objects.filter(household_id=household_id).order_by(
        "-issued_date", "-created_at"
    )[:5]

    # Force 404 if household doesn't exist at all (staff or in-scope parent)
    # This preserves the existing behavior for valid-but-empty finance rows.
    get_object_or_404(Household, id=household_id)

    return Response(
        {
            "household_id": str(household_id),
            "open_balance_cents": int(open_balance_cents),
            "invoices_count_open": int(invoices_count_open),
            "invoices_count_total": int(invoices_total),
            "last_payment_date": last_payment_date.isoformat() if last_payment_date else None,
            "recent_invoices": InvoiceMiniSerializer(recent_invoices_qs, many=True).data,
        }
    )
