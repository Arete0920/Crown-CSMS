from __future__ import annotations

from django.core import signing
from rest_framework import status
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from advancement.models import Ticket
from core.permissions import CrownModulePermission
from households.scoping import get_request_school_id

from .credentials import (
    credential_fingerprint,
    issue_admission_credential,
    render_qr_data_url,
    verify_admission_credential,
)
from .services import get_owned_ticket, list_family_tickets, redeem_ticket


@extend_schema(
    responses=OpenApiTypes.OBJECT,
    description=(
        "Return CrownPass tickets owned by the authenticated user within the "
        "asserted school tenant. Raw admission credentials are intentionally "
        "excluded from this compatibility endpoint."
    ),
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_tickets(request):
    school_id = get_request_school_id(request, required=True)
    tickets = list_family_tickets(school_id=school_id, user=request.user)
    return Response({"count": len(tickets), "tickets": tickets})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_ticket_credential(request, ticket_id):
    """
    Issue a short-lived signed CrownPass admission credential for one ticket
    owned by the authenticated user in the asserted school tenant.
    """
    school_id = get_request_school_id(request, required=True)
    try:
        ticket = get_owned_ticket(
            school_id=school_id,
            user=request.user,
            ticket_id=ticket_id,
        )
    except Ticket.DoesNotExist:
        return Response({"detail": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)

    if ticket.checked_in:
        return Response(
            {"detail": "Ticket has already been used."},
            status=status.HTTP_409_CONFLICT,
        )

    credential = issue_admission_credential(ticket=ticket)
    return Response({
        "ticket_id": str(ticket.id),
        "event_id": str(ticket.event_id),
        "event_name": ticket.event.name,
        "credential": credential,
        "credential_type": "signed-v1",
        "qr_data_url": render_qr_data_url(credential),
    })


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@permission_classes([CrownModulePermission("crownpass.scan")])
def redeem_credential(request):
    """
    Validate and redeem a CrownPass signed admission credential.

    Scanner authority is isolated behind the dedicated crownpass.scan permission.
    """
    school_id = get_request_school_id(request, required=True)
    credential = (request.data.get("credential") or "").strip()
    if not credential:
        return Response({"detail": "credential is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        payload = verify_admission_credential(
            credential=credential,
            school_id=school_id,
        )
    except signing.SignatureExpired:
        return Response(
            {"result": "invalid", "reason": "expired"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except signing.BadSignature:
        return Response(
            {"result": "invalid", "reason": "invalid"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        scan = redeem_ticket(
            school_id=school_id,
            ticket_id=payload["ticket_id"],
            scanned_by_id=request.user.id if request.user else None,
            attempted=credential_fingerprint(credential),
        )
    except Ticket.DoesNotExist:
        return Response(
            {"result": "invalid", "reason": "ticket_not_found"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({
        "scan_id": str(scan.id),
        "ticket_id": str(scan.ticket_id),
        "result": scan.result,
        "scanned_at": scan.scanned_at.isoformat() if scan.scanned_at else None,
    })
