from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from advancement.models import Ticket


@dataclass(frozen=True)
class FamilyTicketSummary:
    ticket_id: str
    event_id: str
    event_name: str
    event_date: str | None
    location: str
    purchaser_name: str
    purchaser_email: str
    checked_in: bool
    checked_in_at: str | None
    purchased_at: str | None

    def as_dict(self) -> dict:
        return {
            "ticket_id": self.ticket_id,
            "event_id": self.event_id,
            "event_name": self.event_name,
            "event_date": self.event_date,
            "location": self.location,
            "purchaser_name": self.purchaser_name,
            "purchaser_email": self.purchaser_email,
            "checked_in": self.checked_in,
            "checked_in_at": self.checked_in_at,
            "purchased_at": self.purchased_at,
        }


def _iso(value):
    return value.isoformat() if value else None


def family_ticket_queryset(*, school_id, user) -> Iterable[Ticket]:
    """
    Compatibility query for CrownPass "My Tickets".

    Existing Advancement tickets do not yet have a canonical holder/user FK.
    Until the CrownPass holder model is introduced, bind ownership to the
    authenticated user's normalized email within the asserted tenant.

    IMPORTANT: Do not expose qr_code here. Admission credentials are a separate
    security boundary and will be served through the CrownPass credential layer.
    """
    email = (getattr(user, "email", "") or "").strip()
    if not email:
        return Ticket.objects.none()

    return (
        Ticket.objects
        .filter(
            school_id=school_id,
            purchaser_email__iexact=email,
        )
        .select_related("event")
        .order_by("-purchased_at")
    )


def list_family_tickets(*, school_id, user) -> list[dict]:
    return [
        FamilyTicketSummary(
            ticket_id=str(ticket.id),
            event_id=str(ticket.event_id),
            event_name=ticket.event.name,
            event_date=_iso(getattr(ticket.event, "date", None)),
            location=getattr(ticket.event, "location", "") or "",
            purchaser_name=ticket.purchaser_name,
            purchaser_email=ticket.purchaser_email,
            checked_in=bool(ticket.checked_in),
            checked_in_at=_iso(ticket.checked_in_at),
            purchased_at=_iso(ticket.purchased_at),
        ).as_dict()
        for ticket in family_ticket_queryset(school_id=school_id, user=user)
    ]
