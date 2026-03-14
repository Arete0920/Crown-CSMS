from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.billing_api.permissions import has_finance_runtime_role
from households.scoping import get_request_school_id
from payments.models import ProviderDispute, ProviderDisputeAction
from payments.providers import get_gateway


def _finance_only(user):
    return has_finance_runtime_role(user)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dispute_detail(request, dispute_id: int):
    school_id = get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    dispute = ProviderDispute.objects.filter(school_id=school_id, id=dispute_id).first()
    if not dispute:
        return Response({"detail": "Dispute not found."}, status=status.HTTP_404_NOT_FOUND)

    actions = [
        {
            "id": action.id,
            "action_type": action.action_type,
            "note": action.note,
            "provider_response_id": action.provider_response_id,
            "created_at": action.created_at,
        }
        for action in dispute.actions.all()
    ]

    return Response(
        {
            "dispute": {
                "id": dispute.id,
                "dispute_id": dispute.dispute_id,
                "status": dispute.status,
                "amount": str(dispute.amount),
                "currency": dispute.currency,
                "reason": dispute.reason,
                "invoice_id": dispute.invoice_id,
                "household_id": dispute.household_id,
            },
            "actions": actions,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def dispute_action_create(request, dispute_id: int):
    school_id = get_request_school_id(request, required=True)

    if not _finance_only(request.user):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    dispute = ProviderDispute.objects.filter(school_id=school_id, id=dispute_id).first()
    if not dispute:
        return Response({"detail": "Dispute not found."}, status=status.HTTP_404_NOT_FOUND)

    action_type = request.data.get("action_type", "").strip()
    note = request.data.get("note", "").strip()
    evidence = request.data.get("evidence") or {}

    gateway = get_gateway(dispute.provider)
    result = gateway.update_dispute(
        dispute_id=dispute.dispute_id,
        action_type=action_type,
        note=note,
        evidence=evidence,
    )

    if not result.ok:
        return Response({"ok": False, "error": result.error}, status=status.HTTP_502_BAD_GATEWAY)

    action = ProviderDisputeAction.objects.create(
        dispute=dispute,
        action_type=action_type,
        note=note,
        provider_response_id=result.provider_response_id,
        payload=result.raw or {},
        created_by=request.user,
    )

    if result.status:
        dispute.status = result.status
        if result.status in {"won", "lost", "closed"}:
            dispute.closed_at = timezone.now()
        dispute.save(update_fields=["status", "closed_at", "updated_at"])

    return Response(
        {
            "ok": True,
            "action_id": action.id,
            "status": dispute.status,
        }
    )
