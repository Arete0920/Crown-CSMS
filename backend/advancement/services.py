"""
Advancement services — all revenue recorded via AdvancementTransaction.
Does NOT touch the household ledger spine (Charge / Payment).
"""
from __future__ import annotations

import uuid
import logging

from django.db import transaction
from django.utils import timezone

from .models import (
    Donor,
    Campaign,
    Event,
    Ticket,
    StoreItem,
    AdvancementTransaction,
)

logger = logging.getLogger("crown.advancement")


# ---------------------------------------------------------------------------
# Ticket purchase
# ---------------------------------------------------------------------------

@transaction.atomic
def create_ticket_purchase(
    *,
    school_id,
    event: Event,
    purchaser_name: str,
    purchaser_email: str,
) -> Ticket:
    """
    Purchase one ticket for an event.
    - Creates unique QR code
    - Increments event.tickets_sold
    - Records AdvancementTransaction (category=event_ticket)
    Raises ValueError if event is at capacity or inactive.
    """
    if not event.active:
        raise ValueError(f"Event '{event.name}' is not active.")
    if event.capacity > 0 and event.tickets_sold >= event.capacity:
        raise ValueError(f"Event '{event.name}' is sold out.")

    qr = str(uuid.uuid4())
    ticket = Ticket.objects.create(
        school_id=school_id,
        event=event,
        purchaser_name=purchaser_name,
        purchaser_email=purchaser_email,
        qr_code=qr,
    )

    # Increment sold count
    Event.objects.filter(pk=event.pk).update(tickets_sold=event.tickets_sold + 1)

    AdvancementTransaction.objects.create(
        school_id=school_id,
        category="event_ticket",
        amount=event.ticket_price,
        description=f"Ticket: {event.name}",
        reference_id=ticket.id,
    )

    logger.info("advancement.ticket.purchased school=%s event=%s ticket=%s", school_id, event.id, ticket.id)
    return ticket


# ---------------------------------------------------------------------------
# Store purchase
# ---------------------------------------------------------------------------

@transaction.atomic
def create_store_purchase(
    *,
    school_id,
    item: StoreItem,
    quantity: int = 1,
) -> AdvancementTransaction:
    """
    Purchase store item(s).
    - Decrements inventory atomically (select_for_update)
    - Records AdvancementTransaction (category=store_purchase)
    Raises ValueError if item is inactive or insufficient inventory.
    """
    if not item.active:
        raise ValueError(f"Store item '{item.name}' is not available.")
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")

    # Lock the row to prevent race conditions
    locked = StoreItem.objects.select_for_update().get(pk=item.pk)
    if locked.inventory < quantity:
        raise ValueError(f"Insufficient inventory for '{item.name}' (available: {locked.inventory}).")

    StoreItem.objects.filter(pk=item.pk).update(inventory=locked.inventory - quantity)

    txn = AdvancementTransaction.objects.create(
        school_id=school_id,
        category="store_purchase",
        amount=item.price * quantity,
        description=f"Store purchase: {item.name} x{quantity}",
        reference_id=item.id,
    )

    logger.info("advancement.store.purchased school=%s item=%s qty=%s", school_id, item.id, quantity)
    return txn


# ---------------------------------------------------------------------------
# Donation recording
# ---------------------------------------------------------------------------

@transaction.atomic
def record_donation(
    *,
    school_id,
    donor: Donor,
    amount,
    campaign: Campaign | None = None,
    description: str = "",
) -> AdvancementTransaction:
    """
    Record a donation from a known Donor.
    - Creates AdvancementTransaction (category=donation)
    - Updates donor.lifetime_giving
    Raises ValueError for non-positive amounts.
    """
    from decimal import Decimal
    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValueError("Donation amount must be positive.")

    txn = AdvancementTransaction.objects.create(
        school_id=school_id,
        category="donation",
        amount=amount,
        description=description or f"Donation from {donor.name}",
        reference_id=donor.id,
        campaign=campaign,
    )

    # Update lifetime giving
    Donor.objects.filter(pk=donor.pk).update(lifetime_giving=donor.lifetime_giving + amount)

    # Update campaign raised total
    if campaign:
        from decimal import Decimal as D
        Campaign.objects.filter(pk=campaign.pk).update(raised=campaign.raised + amount)

    logger.info("advancement.donation.recorded school=%s donor=%s amount=%s", school_id, donor.id, amount)
    return txn


# ---------------------------------------------------------------------------
# Sponsorship sale
# ---------------------------------------------------------------------------

@transaction.atomic
def create_sponsorship_sale(
    *,
    school_id,
    package,
    campaign: Campaign | None = None,
    description: str = "",
) -> AdvancementTransaction:
    """
    Record a sponsorship package sale.
    - Creates AdvancementTransaction (category=sponsorship)
    """
    txn = AdvancementTransaction.objects.create(
        school_id=school_id,
        category="sponsorship",
        amount=package.price,
        description=description or f"Sponsorship: {package.name}",
        reference_id=package.id,
        campaign=campaign,
    )

    logger.info("advancement.sponsorship.sold school=%s package=%s", school_id, package.id)
    return txn
