"""
Stage 3.2 – Stripe Checkout seat ordering services.

Flow:
1. Buyer picks seats → Stage 3.1 hold_seats_strict() puts a SeatHold
2. Buyer clicks "Pay" → create_seat_checkout_session() creates PendingSeatOrder + Stripe session
3. Stripe webhooks fire → stripe_webhook view calls:
     already_processed_event() / mark_event_processed() (idempotency)
     fulfill_paid_order() → tickets + TicketSeat + EmailOutbox entry
4. Buyer polls /orders/<id>/status/ until status == "fulfilled"
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from advancement.models import Event, Ticket  # Event + Ticket live in models.py
from advancement.models_stage3 import Seat, SeatHold, TicketSeat
from advancement.models_stage3_2 import PendingSeatOrder, ProcessedWebhookEvent
from advancement.payments.service import get_checkout_provider
from advancement.services import create_ticket_purchase

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Donation preset helper (Stage 3.4)
# ---------------------------------------------------------------------------

def _donation_presets_cents() -> list[int]:
    """
    Returns donation preset values in cents from DONATION_PRESETS_USD setting.
    e.g. "10,25,50" → [1000, 2500, 5000]
    """
    try:
        raw = str(getattr(settings, "DONATION_PRESETS_USD", "10,25,50"))
        return [int(x.strip()) * 100 for x in raw.split(",") if x.strip().isdigit()]
    except Exception:
        return [1000, 2500, 5000]


# ---------------------------------------------------------------------------
# Checkout session creation
# ---------------------------------------------------------------------------

def create_seat_checkout_session(
    *,
    school_id: uuid.UUID,
    event_id: uuid.UUID,
    purchaser_name: str,
    purchaser_email: str,
    seat_ids: list[uuid.UUID],
    amount_cents: int,
    currency: str | None = None,
    success_url: str | None = None,
    cancel_url: str | None = None,
) -> PendingSeatOrder:
    """
    Create a PendingSeatOrder and initiate a Stripe Checkout session.

    Returns the PendingSeatOrder instance (caller redirects buyer to .checkout_url).
    """
    currency = currency or getattr(settings, "ADVANCEMENT_CURRENCY", "usd")
    app_base = getattr(settings, "PUBLIC_APP_BASE_URL", "http://localhost:5173")
    api_base = getattr(settings, "PUBLIC_API_BASE_URL", "http://localhost:8000")

    order = PendingSeatOrder.objects.create(
        school_id=school_id,
        event_id=event_id,
        purchaser_name=purchaser_name,
        purchaser_email=purchaser_email,
        seat_ids=[str(s) for s in seat_ids],
        amount_cents=amount_cents,
        currency=currency,
        status="pending",
    )

    s_url = success_url or f"{app_base}/advancement/tickets/success?order_id={order.id}"
    c_url = cancel_url or f"{app_base}/advancement/tickets/select"

    provider = get_checkout_provider()

    try:
        event = Event.objects.get(pk=event_id, school_id=school_id)
        description = f"Seats – {event.name}"
    except Event.DoesNotExist:
        description = "Seat tickets"

    result = provider.create_checkout_session(
        amount_cents=amount_cents,
        currency=currency,
        description=description,
        success_url=s_url,
        cancel_url=c_url,
        metadata={
            "order_id": str(order.id),
            "school_id": str(school_id),
            "event_id": str(event_id),
            "customer_email": purchaser_email,
            # Stage 3.4: optional donation presets (stripped by StripeProvider before sending to Stripe)
            "donation_presets_cents": _donation_presets_cents(),
        },
    )

    order.provider = result.provider
    order.provider_session_id = result.provider_payment_id
    order.checkout_url = result.checkout_url or ""
    order.save(update_fields=["provider", "provider_session_id", "checkout_url"])

    return order


# ---------------------------------------------------------------------------
# Webhook idempotency helpers
# ---------------------------------------------------------------------------

def already_processed_event(*, provider: str, event_id: str) -> bool:
    """Return True if this provider event was already handled."""
    return ProcessedWebhookEvent.objects.filter(
        provider=provider, event_id=event_id
    ).exists()


def mark_event_processed(
    *, provider: str, event_id: str, school_id: uuid.UUID | None = None
) -> None:
    """Record that a webhook event has been processed (idempotent guard)."""
    ProcessedWebhookEvent.objects.get_or_create(
        provider=provider,
        event_id=event_id,
        defaults={"school_id": school_id},
    )


# ---------------------------------------------------------------------------
# Order fulfillment (called from webhook handler)
# ---------------------------------------------------------------------------

def fulfill_paid_order(*, order_id: uuid.UUID) -> PendingSeatOrder:
    """
    Convert a PendingSeatOrder into real Ticket + TicketSeat rows.

    Idempotent: if status is already "fulfilled", returns the order unchanged.
    Queues an EmailOutbox row for ticket delivery after committing.
    """
    with transaction.atomic():
        try:
            order = PendingSeatOrder.objects.select_for_update().get(id=order_id)
        except PendingSeatOrder.DoesNotExist:
            raise ValueError(f"PendingSeatOrder {order_id} not found")

        if order.status == "fulfilled":
            return order  # idempotent

        school_id = order.school_id
        event_id = order.event_id
        seat_ids = [uuid.UUID(s) for s in order.seat_ids]

        try:
            event = Event.objects.get(pk=event_id, school_id=school_id)
        except Event.DoesNotExist:
            order.status = "failed"
            order.touch()
            return order

        seat_map = {s.id: s for s in Seat.objects.filter(school_id=school_id, id__in=seat_ids)}

        ticket_ids = []
        for seat_id in seat_ids:
            seat = seat_map.get(seat_id)
            if seat is None:
                continue
            ticket = create_ticket_purchase(
                school_id=school_id,
                event=event,
                purchaser_name=order.purchaser_name,
                purchaser_email=order.purchaser_email,
            )
            TicketSeat.objects.create(
                school_id=school_id,
                event_id=event_id,
                ticket=ticket,
                seat=seat,
            )
            ticket_ids.append(ticket.id)

        # Release any remaining holds
        SeatHold.objects.filter(
            school_id=school_id,
            event=event,
            seat_id__in=seat_ids,
        ).delete()

        order.status = "fulfilled"
        order.updated_at = timezone.now()
        order.save(update_fields=["status", "updated_at"])

    # Queue ticket delivery email (outside atomic block to avoid rollback)
    _queue_ticket_email(order=order, ticket_ids=ticket_ids)

    return order


# ---------------------------------------------------------------------------
# Email queueing (deferred to Stage 3.3 emailer)
# ---------------------------------------------------------------------------

def _queue_ticket_email(*, order: PendingSeatOrder, ticket_ids: list) -> None:
    """
    Queue an EmailOutbox row for ticket delivery.
    Import is deferred to avoid circular imports at module load time.
    """
    try:
        from advancement.models_stage3_3 import EmailOutbox
        from advancement.tickets_render import make_ticket_pdf_bytes, to_b64
        from advancement.models import Ticket
        from advancement.models_stage3 import TicketSeat as _TS

        attachments = []
        for ticket_id in ticket_ids:
            try:
                ticket = Ticket.objects.select_related().get(id=ticket_id)
                ts = _TS.objects.select_related("seat").get(ticket=ticket)
                pdf_bytes = make_ticket_pdf_bytes(ticket=ticket, seat=ts.seat)
                attachments.append({
                    "filename": f"ticket_{ticket.id}.pdf",
                    "content_b64": to_b64(pdf_bytes),
                    "mime_type": "application/pdf",
                })
            except Exception:
                logger.warning("ticket attachment generation skipped for ticket %s", ticket_id, exc_info=True)

        EmailOutbox.objects.create(
            school_id=order.school_id,
            kind="ticket_delivery",
            to_email=order.purchaser_email,
            subject=f"Your tickets – {order.purchaser_name}",
            body_text=(
                f"Hi {order.purchaser_name},\n\n"
                f"Thank you for your purchase! Your tickets are attached.\n\n"
                f"Order ID: {order.id}"
            ),
            body_html=(
                f"<p>Hi {order.purchaser_name},</p>"
                f"<p>Thank you for your purchase! Your tickets are attached.</p>"
                f"<p>Order ID: <strong>{order.id}</strong></p>"
            ),
            attachments_json=attachments,
        )
    except Exception:
        logger.warning("ticket delivery outbox enqueue failed for order %s", order.id, exc_info=True)
