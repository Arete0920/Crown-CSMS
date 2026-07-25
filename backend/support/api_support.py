"""
support/api_support.py

Stage 5 support + SLA API endpoints:

  POST /api/v1/support/tickets/               — create ticket
  GET  /api/v1/support/tickets/               — list open tickets for school
  POST /api/v1/support/tickets/<id>/resolve/  — mark resolved
  GET  /api/v1/support/escalation/run/        — trigger escalation check (platform ops)
"""
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from core.permissions import user_has_permission
from households.scoping import get_request_school_id
from support.models import SupportTicket
from support.services_escalation import escalate_overdue_tickets


def _can_administer_tenant(request) -> bool:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return True
    school = getattr(request, "school", None)
    return bool(
        school is not None
        and user_has_permission(user, "admin.view", school=school)
    )


def _is_platform_operator(user) -> bool:
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and (
            getattr(user, "is_staff", False)
            or getattr(user, "is_superuser", False)
        )
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resolve_ticket(request, ticket_id):
    school_id = get_request_school_id(request)
    if not _can_administer_tenant(request):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    try:
        ticket = SupportTicket.objects.get(pk=ticket_id, school_id=school_id)
    except SupportTicket.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    ticket.status = SupportTicket.STATUS_CLOSED
    ticket.resolved_at = timezone.now()
    ticket.save(update_fields=["status", "resolved_at"])
    return Response({"id": ticket.id, "status": ticket.status, "resolved_at": ticket.resolved_at})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def run_escalation(request):
    """Platform-ops endpoint: trigger SLA breach check immediately."""
    if not _is_platform_operator(request.user):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    result = escalate_overdue_tickets()
    return Response(result)
