"""
support/api_support.py

Stage 5 support + SLA API endpoints:

  POST /api/v1/support/tickets/               — create ticket
  GET  /api/v1/support/tickets/               — list open tickets for school
  POST /api/v1/support/tickets/<id>/resolve/  — mark resolved
  GET  /api/v1/support/escalation/run/        — trigger escalation check (platform ops)
"""
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from households.scoping import get_request_school_id
from support.models import SupportTicket
from support.services_escalation import escalate_overdue_tickets


class SupportTicketCreateRequestSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    priority = serializers.ChoiceField(choices=SupportTicket.PRIORITY_CHOICES)


class SupportTicketSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    priority = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    sla_deadline = serializers.DateTimeField(allow_null=True)


class SupportTicketListResponseSerializer(serializers.Serializer):
    tickets = SupportTicketSummarySerializer(many=True)


class SupportTicketCreateResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sla_deadline = serializers.DateTimeField(allow_null=True)


class SupportTicketResolveResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    resolved_at = serializers.DateTimeField(allow_null=True)


class SupportEscalationResponseSerializer(serializers.Serializer):
    checked = serializers.IntegerField(required=False)
    escalated = serializers.IntegerField(required=False)
    detail = serializers.CharField(required=False)


@extend_schema(methods=["GET"], responses={200: SupportTicketListResponseSerializer})
@extend_schema(
    methods=["POST"],
    request=SupportTicketCreateRequestSerializer,
    responses={201: SupportTicketCreateResponseSerializer},
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def tickets(request):
    school_id = get_request_school_id(request)

    if request.method == "POST":
        data = request.data
        required = ("title", "description", "priority")
        missing = [f for f in required if not data.get(f)]
        if missing:
            return Response({"detail": f"Missing fields: {missing}"}, status=status.HTTP_400_BAD_REQUEST)

        valid_priorities = [p for p, _ in SupportTicket.PRIORITY_CHOICES]
        if data["priority"] not in valid_priorities:
            return Response({"detail": "Invalid priority."}, status=status.HTTP_400_BAD_REQUEST)

        ticket = SupportTicket.objects.create(
            school_id=school_id,
            title=data["title"],
            description=data["description"],
            priority=data["priority"],
        )
        return Response(
            {"id": ticket.id, "sla_deadline": ticket.sla_deadline()},
            status=status.HTTP_201_CREATED,
        )

    # GET — list open tickets for this school
    qs = SupportTicket.objects.filter(school_id=school_id, status__in=["open", "escalated"])
    out = [
        {
            "id": t.id,
            "title": t.title,
            "priority": t.priority,
            "status": t.status,
            "created_at": t.created_at,
            "sla_deadline": t.sla_deadline(),
        }
        for t in qs
    ]
    return Response({"tickets": out})


@extend_schema(responses={200: SupportTicketResolveResponseSerializer})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resolve_ticket(request, ticket_id):
    school_id = get_request_school_id(request)
    try:
        ticket = SupportTicket.objects.get(pk=ticket_id, school_id=school_id)
    except SupportTicket.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    ticket.status = SupportTicket.STATUS_CLOSED
    ticket.resolved_at = timezone.now()
    ticket.save(update_fields=["status", "resolved_at"])
    return Response({"id": ticket.id, "status": ticket.status, "resolved_at": ticket.resolved_at})


@extend_schema(responses={200: SupportEscalationResponseSerializer})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def run_escalation(request):
    """Platform-ops endpoint: trigger SLA breach check immediately."""
    result = escalate_overdue_tickets()
    return Response(result)
