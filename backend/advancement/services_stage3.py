"""
Advancement Stage 3 service layer.

All public functions are @transaction.atomic where writes occur.
Crown pattern: school_id = UUIDField — services accept school_id: uuid.UUID,
not a School instance. Spec's hold_seats / transition_move_stage have been
adapted accordingly.
"""
from __future__ import annotations

import uuid
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models_stage3 import (
    Move,
    Prospect,
    Seat,
    SeatHold,
    SeatingMap,
    SponsorImpression,
    SponsorshipDeliverable,
    TicketSeat,
)
from .models import Event, Ticket


# ---------------------------------------------------------------------------
# Moves Management
# ---------------------------------------------------------------------------

@transaction.atomic
def transition_move_stage(
    *,
    school_id: uuid.UUID,
    prospect_id: uuid.UUID,
    new_stage: str,
    user=None,
    action_type: str = "other",
    summary: str = "",
    notes: str = "",
) -> Move:
    """
    Record a stage transition for a major-gift prospect.
    Inserts a new Move row (full history preserved — do NOT update existing rows).

    Raises Prospect.DoesNotExist if prospect not found for this school.
    """
    valid_stages = {
        "identified", "qualified", "cultivating", "soliciting",
        "stewarding", "closed_won", "closed_lost",
    }
    if new_stage not in valid_stages:
        raise ValueError(f"Invalid stage: '{new_stage}'. Valid: {sorted(valid_stages)}")

    prospect = Prospect.objects.select_for_update().get(
        id=prospect_id, school_id=school_id
    )

    move = Move.objects.create(
        school_id=school_id,
        prospect=prospect,
        stage=new_stage,
        action_type=action_type,
        summary=summary or f"Stage → {new_stage}",
        notes=notes,
        created_by=user if (user and getattr(user, "is_authenticated", False)) else None,
        created_at=timezone.now(),
    )
    return move


# ---------------------------------------------------------------------------
# Seating
# ---------------------------------------------------------------------------

@transaction.atomic
def create_or_replace_seats_from_layout(
    *,
    school_id: uuid.UUID,
    seating_map_id: uuid.UUID,
    layout: dict,
) -> int:
    """
    Persist layout JSON onto SeatingMap then regenerate all Seat rows.
    Deletes existing seats before re-creating (safe: only call before tickets sold).

    Layout schema:
    {
      "sections": [
        {"name": "A", "rows": [{"name": "1", "seats": 10}, ...]},
        ...
      ]
    }

    Returns count of seats created.
    """
    seating_map = SeatingMap.objects.select_for_update().get(
        id=seating_map_id, school_id=school_id
    )
    seating_map.layout_json = layout
    seating_map.save(update_fields=["layout_json"])

    Seat.objects.filter(school_id=school_id, seating_map=seating_map).delete()

    seats_to_create = []
    for sec in layout.get("sections", []):
        sec_name = str(sec.get("name", ""))
        for row in sec.get("rows", []):
            row_name = str(row.get("name", ""))
            n = int(row.get("seats", 0))
            for i in range(1, n + 1):
                seats_to_create.append(
                    Seat(
                        school_id=school_id,
                        seating_map=seating_map,
                        section=sec_name,
                        row=row_name,
                        number=str(i),
                    )
                )

    Seat.objects.bulk_create(seats_to_create)
    return len(seats_to_create)


@transaction.atomic
def hold_seats(
    *,
    school_id: uuid.UUID,
    event_id: uuid.UUID,
    seat_ids: list[uuid.UUID],
    email: str,
    hold_minutes: int = 10,
) -> dict:
    """
    Attempt to place temporary holds on the given seats for an event checkout.

    - Clears expired holds first.
    - For each seat: creates new hold OR refreshes existing hold if same email.
    - If a seat is held by a different active email: returns ok=False immediately.

    Returns {"ok": True, "holds": [...]} or {"ok": False, "message": "..."}
    """
    now = timezone.now()
    expires = now + timedelta(minutes=hold_minutes)

    # Purge stale holds for this event
    SeatHold.objects.filter(school_id=school_id, event_id=event_id, expires_at__lt=now).delete()

    holds_out = []
    for seat_id in seat_ids:
        try:
            seat = Seat.objects.get(id=seat_id, school_id=school_id)
        except Seat.DoesNotExist:
            return {"ok": False, "message": f"Seat {seat_id} not found"}

        hold, created = SeatHold.objects.get_or_create(
            school_id=school_id,
            event_id=event_id,
            seat=seat,
            defaults={"held_by_email": email, "expires_at": expires},
        )

        if not created:
            if hold.held_by_email != email:
                return {"ok": False, "message": f"Seat {seat_id} is held by another party"}
            # Refresh expiry for same-email re-hold
            hold.expires_at = expires
            hold.save(update_fields=["expires_at"])

        holds_out.append({
            "seat_id": str(seat.id),
            "section": seat.section,
            "row": seat.row,
            "number": seat.number,
            "expires_at": hold.expires_at.isoformat(),
        })

    return {"ok": True, "holds": holds_out}


@transaction.atomic
def assign_seat_to_ticket(
    *,
    school_id: uuid.UUID,
    ticket_id: uuid.UUID,
    seat_id: uuid.UUID,
) -> TicketSeat:
    """
    Assign a Ticket to a confirmed Seat (post-checkout safety assignment).
    Raises ValueError if seat is already assigned to a different ticket.
    Raises Ticket.DoesNotExist / Seat.DoesNotExist if not found for school.
    """
    ticket = Ticket.objects.get(id=ticket_id, school_id=school_id)
    seat = Seat.objects.get(id=seat_id, school_id=school_id)

    if TicketSeat.objects.filter(school_id=school_id, seat=seat).exists():
        raise ValueError(f"Seat {seat_id} is already assigned to a ticket.")

    ts = TicketSeat.objects.create(
        school_id=school_id,
        ticket=ticket,
        seat=seat,
    )
    return ts


# ---------------------------------------------------------------------------
# Sponsorship Impressions
# ---------------------------------------------------------------------------

def log_impressions(
    *,
    school_id: uuid.UUID,
    deliverable_id: uuid.UUID,
    channel: str = "unknown",
    count: int = 1,
    metadata: dict | None = None,
) -> SponsorImpression:
    """
    Log an impression event against a SponsorshipDeliverable.
    Not atomic — impression logging is append-only, no conflict possible.
    Raises SponsorshipDeliverable.DoesNotExist if not found for this school.
    """
    deliverable = SponsorshipDeliverable.objects.get(
        id=deliverable_id, school_id=school_id
    )
    return SponsorImpression.objects.create(
        school_id=school_id,
        deliverable=deliverable,
        channel=channel or "unknown",
        count=max(1, int(count)),
        metadata=metadata or {},
    )
