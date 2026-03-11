"""
Stage 3.3 – Section pricing, best-available seat selection, checkout creation.
"""
from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction
from django.utils import timezone

from advancement.models import Event  # Event lives in models.py
from advancement.models_stage3 import EventSeating, Seat, SeatHold, TicketSeat
from advancement.models_stage3_3 import EventSectionPrice
from advancement.services_stage3_1 import _cleanup_expired_holds
from advancement.services_stage3_2 import create_seat_checkout_session


# ---------------------------------------------------------------------------
# Section pricing helpers
# ---------------------------------------------------------------------------

def get_section_price(*, school_id: uuid.UUID, event_id: uuid.UUID, section: str) -> int:
    """
    Return price_cents for (school_id, event_id, section).
    Returns 0 if no specific price is configured.
    """
    try:
        esp = EventSectionPrice.objects.get(
            school_id=school_id, event_id=event_id, section=section
        )
        return esp.price_cents
    except EventSectionPrice.DoesNotExist:
        return 0


def compute_seats_amount(
    *, school_id: uuid.UUID, event_id: uuid.UUID, seat_ids: list[uuid.UUID]
) -> int:
    """
    Compute total price_cents for the given seat IDs using their section prices.
    Seats without a section price contribute 0 to the total.
    """
    seats = Seat.objects.filter(school_id=school_id, id__in=seat_ids)
    total = 0
    for seat in seats:
        section = seat.section or "default"
        total += get_section_price(school_id=school_id, event_id=event_id, section=section)
    return total


# ---------------------------------------------------------------------------
# Best-available seat selection
# ---------------------------------------------------------------------------

def best_available(
    *,
    school_id: uuid.UUID,
    event_id: uuid.UUID,
    count: int,
    preferred_sections: list[str] | None = None,
) -> list[Seat]:
    """
    Return up to ``count`` available (not sold, not held) seats.

    Preference order:
    1. Seats in ``preferred_sections`` (in section/row/seat_number order)
    2. Remaining seats in section/row/seat_number order

    Returns an empty list if fewer than ``count`` available seats exist.
    """
    _cleanup_expired_holds(school_id, event_id)

    # Sold seat ids
    sold_ids = set(
        TicketSeat.objects.filter(
            school_id=school_id,
            event_id=event_id,
        ).values_list("seat_id", flat=True)
    )

    # Held seat ids
    held_ids = set(
        SeatHold.objects.filter(
            school_id=school_id,
            event__id=event_id,
            expires_at__gt=timezone.now(),
        ).values_list("seat_id", flat=True)
    )

    # Get all seats for the event
    try:
        event = Event.objects.get(pk=event_id, school_id=school_id)
        event_seating = EventSeating.objects.get(school_id=school_id, event=event)
    except (Event.DoesNotExist, EventSeating.DoesNotExist):
        return []

    unavailable = sold_ids | held_ids
    all_available = list(
        Seat.objects.filter(
            school_id=school_id,
            seating_map=event_seating.seating_map,
        ).exclude(id__in=unavailable).order_by("section", "row", "number")
    )

    if not all_available:
        return []

    if preferred_sections:
        pref_set = set(preferred_sections)
        preferred = [s for s in all_available if s.section in pref_set]
        others = [s for s in all_available if s.section not in pref_set]
        ordered = preferred + others
    else:
        ordered = all_available

    return ordered[:count]


# ---------------------------------------------------------------------------
# Best-available + checkout in one call
# ---------------------------------------------------------------------------

def create_checkout_for_best_available(
    *,
    school_id: uuid.UUID,
    event_id: uuid.UUID,
    purchaser_name: str,
    purchaser_email: str,
    count: int,
    preferred_sections: list[str] | None = None,
    success_url: str | None = None,
    cancel_url: str | None = None,
) -> dict[str, Any]:
    """
    Find the best ``count`` available seats and create a Stripe checkout session.

    Returns a dict with order info and checkout_url, or an error dict if not
    enough seats are available.
    """
    seats = best_available(
        school_id=school_id,
        event_id=event_id,
        count=count,
        preferred_sections=preferred_sections,
    )

    if len(seats) < count:
        return {
            "ok": False,
            "error": "not_enough_seats",
            "requested": count,
            "available": len(seats),
        }

    seat_ids = [s.id for s in seats]
    amount_cents = compute_seats_amount(
        school_id=school_id, event_id=event_id, seat_ids=seat_ids
    )

    order = create_seat_checkout_session(
        school_id=school_id,
        event_id=event_id,
        purchaser_name=purchaser_name,
        purchaser_email=purchaser_email,
        seat_ids=seat_ids,
        amount_cents=amount_cents,
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return {
        "ok": True,
        "order_id": str(order.id),
        "checkout_url": order.checkout_url,
        "seat_ids": [str(s) for s in seat_ids],
        "amount_cents": amount_cents,
        "currency": order.currency,
    }
