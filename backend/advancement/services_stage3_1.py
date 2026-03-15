"""
Stage 3.1 – Live seat availability grid + strict seat holding + purchase of held seats.

Key design decisions:
- SeatHold uses the existing Stage 3 model (school_id + event FK + seat FK).
- TicketSeat now carries event_id (added in models_stage3.py Stage 3.1 migration).
- All seat IDs are UUIDs (Crown pattern).
- `purchase_held_seats` is atomic – it converts holds → tickets + TicketSeat in one
  transaction and fails fast if any seat is already confirmed.
"""
from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone

from advancement.models import Event  # Event lives in models.py (core advancement model)
from advancement.models_stage3 import (
    EventSeating,
    Seat,
    SeatHold,
    TicketSeat,
)
from advancement.services import create_ticket_purchase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cleanup_expired_holds(school_id: uuid.UUID, event_id: uuid.UUID) -> int:
    """Delete SeatHold rows whose expires_at has passed. Returns deleted count."""
    deleted, _ = SeatHold.objects.filter(
        school_id=school_id,
        event__id=event_id,
        expires_at__lt=timezone.now(),
    ).delete()
    return deleted


# ---------------------------------------------------------------------------
# Availability grid
# ---------------------------------------------------------------------------

def build_availability_grid(*, school_id: uuid.UUID, event_id: uuid.UUID) -> dict[str, Any]:
    """
    Return the full seating availability grid for a buyer UI.

    Structure::

        {
          "event_id": str,
          "capacity": int,
          "sold": int,
          "held": int,
          "available": int,
          "sections": {
              "<section>": {
                  "rows": {
                      "<row>": [
                          {
                              "seat_id": str,
                              "label": str,
                              "status": "available" | "held" | "sold",
                          },
                          ...
                      ]
                  }
              },
              ...
          }
        }
    """
    _cleanup_expired_holds(school_id, event_id)

    # Fetch EventSeating to get the seating map
    try:
        event = Event.objects.get(pk=event_id, school_id=school_id)
    except Event.DoesNotExist:
        return {}

    # All seats for the event's seating map
    try:
        event_seating = EventSeating.objects.get(school_id=school_id, event=event)
    except EventSeating.DoesNotExist:
        return {
            "event_id": str(event_id),
            "capacity": 0,
            "sold": 0,
            "held": 0,
            "available": 0,
            "sections": {},
        }

    all_seats = list(
        Seat.objects.filter(
            school_id=school_id,
            seating_map=event_seating.seating_map,
        )
    )

    # Sold seat ids
    sold_ids: set[uuid.UUID] = set(
        TicketSeat.objects.filter(
            school_id=school_id,
            event_id=event_id,
        ).values_list("seat_id", flat=True)
    )

    # Active hold seat ids
    held_ids: set[uuid.UUID] = set(
        SeatHold.objects.filter(
            school_id=school_id,
            event=event,
            expires_at__gt=timezone.now(),
        ).values_list("seat_id", flat=True)
    )

    sections: dict[str, Any] = {}
    for seat in all_seats:
        section = seat.section or "default"
        row = seat.row or "A"
        if section not in sections:
            sections[section] = {"rows": {}}
        if row not in sections[section]["rows"]:
            sections[section]["rows"][row] = []

        if seat.id in sold_ids:
            status = "sold"
        elif seat.id in held_ids:
            status = "held"
        else:
            status = "available"

        sections[section]["rows"][row].append({
            "seat_id": str(seat.id),
            "label": f"{section}-{seat.row}-{seat.number}",
            "status": status,
        })

    sold = len(sold_ids)
    held = len(held_ids)
    total = len(all_seats)

    return {
        "event_id": str(event_id),
        "capacity": total,
        "sold": sold,
        "held": held,
        "available": max(0, total - sold - held),
        "sections": sections,
    }


# ---------------------------------------------------------------------------
# Strict seat hold
# ---------------------------------------------------------------------------

def hold_seats_strict(
    *,
    school_id: uuid.UUID,
    event_id: uuid.UUID,
    seat_ids: list[uuid.UUID],
    email: str,
    hold_minutes: int = 10,
) -> dict[str, Any]:
    """
    Atomically hold the given seats for ``email``.

    Returns::

        {
          "ok": True,
          "hold_expires_at": <iso>,
          "held_seat_ids": [<uuid>, ...]
        }

    or on conflict::

        {
          "ok": False,
          "conflict": [<uuid>, ...]
        }
    """
    _cleanup_expired_holds(school_id, event_id)

    with transaction.atomic():
        try:
            event = Event.objects.select_for_update().get(id=event_id, school_id=school_id)
        except Event.DoesNotExist:
            return {"ok": False, "conflict": [], "error": "event_not_found"}

        # Check already-sold
        sold_ids = set(
            TicketSeat.objects.filter(
                school_id=school_id,
                event_id=event_id,
                seat_id__in=seat_ids,
            ).values_list("seat_id", flat=True)
        )
        if sold_ids:
            return {"ok": False, "conflict": [str(s) for s in sold_ids]}

        # Check already-held (by someone else) – exclude requester's own active holds
        held_ids = set(
            SeatHold.objects.filter(
                school_id=school_id,
                event=event,
                seat_id__in=seat_ids,
                expires_at__gt=timezone.now(),
            ).exclude(held_by_email=email).values_list("seat_id", flat=True)
        )
        if held_ids:
            return {"ok": False, "conflict": [str(s) for s in held_ids]}

        expires_at = timezone.now() + timedelta(minutes=hold_minutes)

        # Remove any stale holds for this email on these seats
        SeatHold.objects.filter(
            school_id=school_id,
            event=event,
            seat_id__in=seat_ids,
            held_by_email=email,
        ).delete()

        # Create fresh holds
        seats_qs = Seat.objects.filter(school_id=school_id, id__in=seat_ids)
        holds = [
            SeatHold(
                school_id=school_id,
                event=event,
                seat=seat,
                held_by_email=email,
                expires_at=expires_at,
            )
            for seat in seats_qs
        ]
        SeatHold.objects.bulk_create(holds)

    return {
        "ok": True,
        "hold_expires_at": expires_at.isoformat(),
        "held_seat_ids": [str(s) for s in seat_ids],
    }


# ---------------------------------------------------------------------------
# Purchase held seats
# ---------------------------------------------------------------------------

def purchase_held_seats(
    *,
    school_id: uuid.UUID,
    event_id: uuid.UUID,
    email: str,
    purchaser_name: str,
    seat_ids: list[uuid.UUID],
) -> dict[str, Any]:
    """
    Convert active holds → Ticket + TicketSeat rows.

    Must be called while the caller still holds an active SeatHold for all
    listed seat_ids. Returns created ticket IDs.
    """
    with transaction.atomic():
        try:
            event = Event.objects.select_for_update().get(id=event_id, school_id=school_id)
        except Event.DoesNotExist:
            return {"ok": False, "error": "event_not_found"}

        # Verify holds exist and are still active
        active_holds = list(
            SeatHold.objects.select_for_update().filter(
                school_id=school_id,
                event=event,
                seat_id__in=seat_ids,
                held_by_email=email,
                expires_at__gt=timezone.now(),
            )
        )
        held_seat_ids = {h.seat_id for h in active_holds}
        missing = set(seat_ids) - held_seat_ids
        if missing:
            return {"ok": False, "error": "hold_expired_or_missing", "missing": [str(s) for s in missing]}

        # Double-check not already sold
        sold_ids = set(
            TicketSeat.objects.filter(
                school_id=school_id,
                event_id=event_id,
                seat_id__in=seat_ids,
            ).values_list("seat_id", flat=True)
        )
        if sold_ids:
            return {"ok": False, "error": "already_sold", "conflict": [str(s) for s in sold_ids]}

        # Fetch seat objects
        seat_map = {s.id: s for s in Seat.objects.filter(school_id=school_id, id__in=seat_ids)}

        ticket_ids = []
        for seat_id in seat_ids:
            seat = seat_map[seat_id]
            ticket = create_ticket_purchase(
                school_id=school_id,
                event=event,
                purchaser_name=purchaser_name,
                purchaser_email=email,
            )
            TicketSeat.objects.create(
                school_id=school_id,
                event_id=event_id,
                ticket=ticket,
                seat=seat,
            )
            ticket_ids.append(str(ticket.id))

        # Release holds
        SeatHold.objects.filter(
            school_id=school_id,
            event=event,
            seat_id__in=seat_ids,
        ).delete()

    return {"ok": True, "ticket_ids": ticket_ids}
