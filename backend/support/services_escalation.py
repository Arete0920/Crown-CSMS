"""
support/services_escalation.py

SLA escalation engine — finds overdue tickets for one school tenant and
escalates them. Called via management command or Celery beat task.
"""
import logging
from datetime import timedelta

from django.utils import timezone

from support.models import SupportTicket, SLA_HOURS

logger = logging.getLogger("crown.support")


def _notify_engineering(ticket: SupportTicket) -> None:
    """Fire-and-forget notification stub. Wire to email/Teams/PagerDuty as needed."""
    logger.warning(
        "SLA_BREACH ticket_id=%s priority=%s school_id=%s created_at=%s",
        ticket.id,
        ticket.priority,
        ticket.school_id,
        ticket.created_at,
    )


def escalate_overdue_tickets(*, school_id) -> dict:
    """
    Find open tickets for exactly one school that have breached their SLA
    window and mark them escalated.
    """
    now = timezone.now()
    escalated_ids: list[int] = []

    for priority, hours in SLA_HOURS.items():
        deadline_cutoff = now - timedelta(hours=hours)
        overdue = SupportTicket.objects.filter(
            school_id=school_id,
            priority=priority,
            status=SupportTicket.STATUS_OPEN,
            created_at__lte=deadline_cutoff,
        )
        for ticket in overdue:
            ticket.status = SupportTicket.STATUS_ESCALATED
            ticket.escalated_at = now
            ticket.save(update_fields=["status", "escalated_at"])
            _notify_engineering(ticket)
            escalated_ids.append(ticket.id)

    return {"school_id": str(school_id), "escalated": escalated_ids}
