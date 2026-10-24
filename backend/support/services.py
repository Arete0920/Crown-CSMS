"""Transactional ticket writes with mandatory actor attribution."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied

from support.models import SupportTicket, SupportTicketEvent
from support.permissions import can_manage, can_submit
from support.serializers import TicketCreateSerializer, TicketResolutionSerializer


@transaction.atomic
def create_ticket(*, actor, school, data) -> SupportTicket:
    """Create a server-owned ticket and its event, or persist neither."""
    if not can_submit(actor, school):
        raise PermissionDenied()
    serializer = TicketCreateSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    ticket = SupportTicket.objects.create(
        school_id=school.pk,
        requester=actor,
        **serializer.validated_data,
    )
    SupportTicketEvent.objects.create(ticket=ticket, actor=actor, action="created")
    return ticket


@transaction.atomic
def resolve_ticket_for_school(*, actor, school, ticket_id: int, data) -> SupportTicket:
    """Lock resolution; repeats preserve original evidence and resolution time."""
    if not can_manage(actor, school):
        raise PermissionDenied()
    serializer = TicketResolutionSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    try:
        ticket = SupportTicket.objects.select_for_update().get(
            pk=ticket_id,
            school_id=school.pk,
        )
    except SupportTicket.DoesNotExist as exc:
        raise NotFound() from exc
    if ticket.status == SupportTicket.STATUS_CLOSED:
        return ticket
    ticket.status = SupportTicket.STATUS_CLOSED
    ticket.resolved_at = timezone.now()
    ticket.resolution_summary = serializer.validated_data["resolution_summary"]
    ticket.save(update_fields=["status", "resolved_at", "resolution_summary"])
    SupportTicketEvent.objects.create(ticket=ticket, actor=actor, action="resolved")
    return ticket
