"""School-scoped intake, bounded requester views and audited resolution."""

from django.core.paginator import Paginator
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from households.scoping import get_request_school_id
from support.permissions import active_user, can_manage, can_submit, can_view_all
from support.models import SupportTicket
from support.serializers import TicketListSerializer
from support.services import create_ticket, resolve_ticket_for_school
from support.services_escalation import escalate_overdue_tickets


def _school(request):
    """Bind school only through the canonical validated tenant contract."""
    if not active_user(request.user):
        raise PermissionDenied()
    get_request_school_id(request)
    return request.school


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def tickets(request):
    """Requesters see their records; explicit school viewers see the queue."""
    school = _school(request)
    if request.method == "POST":
        ticket = create_ticket(actor=request.user, school=school, data=request.data)
        return Response(
            {"id": ticket.id, "sla_deadline": ticket.sla_deadline()},
            status=status.HTTP_201_CREATED,
        )
    if not (can_submit(request.user, school) or can_view_all(request.user, school)):
        raise PermissionDenied()
    serializer = TicketListSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    options = serializer.validated_data
    qs = SupportTicket.objects.filter(school_id=school.pk)
    if not can_view_all(request.user, school):
        qs = qs.filter(requester=request.user)
    selected_status = options.get("status")
    if selected_status and selected_status != "all":
        qs = qs.filter(status=selected_status)
    elif selected_status is None:
        qs = qs.filter(status__in=["open", "escalated"])
    paginator = Paginator(qs, options["per_page"])
    page = paginator.get_page(options["page"])
    return Response(
        {
            "total": paginator.count,
            "page": page.number,
            "per_page": options["per_page"],
            "tickets": [
                {
                    "id": ticket.id,
                    "title": ticket.title,
                    "priority": ticket.priority,
                    "status": ticket.status,
                    "created_at": ticket.created_at,
                    "sla_deadline": ticket.sla_deadline(),
                }
                for ticket in page.object_list
            ],
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resolve_ticket(request, ticket_id):
    """Require support.manage; generic dashboard access is insufficient."""
    school = _school(request)
    if not can_manage(request.user, school):
        raise PermissionDenied()
    ticket = resolve_ticket_for_school(
        actor=request.user,
        school=school,
        ticket_id=ticket_id,
        data=request.data,
    )
    return Response(
        {
            "id": ticket.id,
            "status": ticket.status,
            "resolved_at": ticket.resolved_at,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def run_escalation(request):
    """Authorized school support managers may request its escalation check."""
    school_id = get_request_school_id(request)
    if not can_manage(request.user, request.school):
        raise PermissionDenied()
    return Response(escalate_overdue_tickets(school_id=school_id))
