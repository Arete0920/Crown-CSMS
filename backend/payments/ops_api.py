from decimal import Decimal

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.billing_api.permissions import has_finance_runtime_role
from households.scoping import get_request_school_id
from payments.models import ProviderDispute, ProviderPayoutBatch


def _finance_only(user):
    return has_finance_runtime_role(user)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def disputes_list(request):
    school_id = get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    qs = ProviderDispute.objects.filter(school_id=school_id).order_by("-id")

    rows = [
        {
            "id": row.id,
            "dispute_id": row.dispute_id,
            "provider_payment_id": row.provider_payment_id,
            "invoice_id": row.invoice_id,
            "household_id": row.household_id,
            "amount": str(row.amount),
            "currency": row.currency,
            "reason": row.reason,
            "status": row.status,
            "opened_at": row.opened_at,
            "closed_at": row.closed_at,
        }
        for row in qs
    ]
    return Response({"results": rows})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payout_batches_list(request):
    school_id = get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    qs = ProviderPayoutBatch.objects.filter(school_id=school_id).prefetch_related("entries").order_by("-id")

    rows = []
    for batch in qs:
        entry_net_total = sum((entry.net_amount for entry in batch.entries.all()), start=Decimal("0.00"))
        rows.append(
            {
                "id": batch.id,
                "payout_id": batch.payout_id,
                "status": batch.status,
                "gross_amount": str(batch.gross_amount),
                "fee_amount": str(batch.fee_amount),
                "net_amount": str(batch.net_amount),
                "entry_net_total": str(entry_net_total),
                "expected_payment_count": batch.expected_payment_count,
                "entry_count": batch.entries.count(),
                "settled_at": batch.settled_at,
            }
        )

    return Response({"results": rows})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payout_batch_detail(request, batch_id):
    school_id = get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    batch = ProviderPayoutBatch.objects.filter(
        school_id=school_id,
        id=batch_id,
    ).prefetch_related("entries").first()

    if not batch:
        return Response({"detail": "Payout batch not found."}, status=status.HTTP_404_NOT_FOUND)

    entries = [
        {
            "id": entry.id,
            "provider_payment_id": entry.provider_payment_id,
            "provider_intent_id": entry.provider_intent_id,
            "invoice_id": entry.invoice_id,
            "household_id": entry.household_id,
            "gross_amount": str(entry.gross_amount),
            "fee_amount": str(entry.fee_amount),
            "net_amount": str(entry.net_amount),
            "currency": entry.currency,
        }
        for entry in batch.entries.all()
    ]

    return Response(
        {
            "batch": {
                "id": batch.id,
                "payout_id": batch.payout_id,
                "status": batch.status,
                "gross_amount": str(batch.gross_amount),
                "fee_amount": str(batch.fee_amount),
                "net_amount": str(batch.net_amount),
                "expected_payment_count": batch.expected_payment_count,
                "settled_at": batch.settled_at,
            },
            "entries": entries,
        }
    )
