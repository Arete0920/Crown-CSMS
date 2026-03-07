"""
Advancement Stage 2 service layer.

All public functions are @transaction.atomic.
Uses AdvancementTransaction as the internal ledger — LedgerEntry does not exist in
this codebase (spec references a different project).
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    AdvancementTransaction,
    Campaign,
    Donor,
    Gift,
    Pledge,
    SponsorshipAgreement,
    SponsorshipPackage,
    Ticket,
    TicketScan,
)
from .payments.service import get_provider


# ---------------------------------------------------------------------------
# Gift checkout & payment confirmation
# ---------------------------------------------------------------------------

@transaction.atomic
def create_gift_checkout(
    *,
    school_id: uuid.UUID,
    amount: Decimal,
    donor_id: uuid.UUID | None = None,
    campaign_id: uuid.UUID | None = None,
    restricted: bool = False,
    restriction_label: str = "",
    memo: str = "",
) -> Gift:
    """
    Create a pending Gift and open a provider checkout session.
    Returns the saved Gift with provider_payment_id populated.
    """
    provider = get_provider()
    currency = getattr(settings, "ADVANCEMENT_CURRENCY", "usd")

    metadata: dict = {
        "school_id": str(school_id),
        "donor_id": str(donor_id) if donor_id else None,
        "campaign_id": str(campaign_id) if campaign_id else None,
        "restricted": restricted,
    }

    session = provider.create_checkout_session(
        amount=float(amount),
        currency=currency,
        metadata=metadata,
    )

    gift = Gift.objects.create(
        school_id=school_id,
        donor_id=donor_id,
        campaign_id=campaign_id,
        amount=amount,
        restricted=restricted,
        restriction_label=restriction_label,
        memo=memo,
        status="pending",
        provider=provider.PROVIDER_NAME,
        provider_payment_id=session["provider_payment_id"],
    )
    return gift


@transaction.atomic
def mark_gift_paid(*, gift_id: uuid.UUID, school_id: uuid.UUID) -> Gift:
    """
    Confirm payment for a Gift. Creates the AdvancementTransaction revenue entry
    and updates Donor.lifetime_giving + Campaign.raised side effects.

    Raises Gift.DoesNotExist if not found for this school.
    Raises ValueError if already paid/refunded.
    """
    gift = Gift.objects.select_for_update().get(id=gift_id, school_id=school_id)

    if gift.status in ("paid", "refunded"):
        raise ValueError(f"Gift {gift_id} is already {gift.status}.")

    gift.status = "paid"
    gift.save(update_fields=["status"])

    # Campaign raised total
    campaign = None
    if gift.campaign_id:
        try:
            campaign = Campaign.objects.select_for_update().get(
                id=gift.campaign_id, school_id=school_id
            )
            campaign.raised += gift.amount
            campaign.donors_count += 1
            campaign.save(update_fields=["raised", "donors_count"])
        except Campaign.DoesNotExist:
            campaign = None

    # Donor lifetime giving
    if gift.donor_id:
        try:
            donor = Donor.objects.select_for_update().get(
                id=gift.donor_id, school_id=school_id
            )
            donor.lifetime_giving += gift.amount
            donor.save(update_fields=["lifetime_giving"])
        except Donor.DoesNotExist:
            pass

    AdvancementTransaction.objects.create(
        school_id=school_id,
        category="donation",
        amount=gift.amount,
        description=f"Gift {gift.id} confirmed",
        reference_id=gift.id,
        campaign=campaign,
    )

    return gift


# ---------------------------------------------------------------------------
# Pledge management
# ---------------------------------------------------------------------------

@transaction.atomic
def create_pledge(
    *,
    school_id: uuid.UUID,
    total_amount: Decimal,
    start_date,
    frequency: str = "monthly",
    donor_id: uuid.UUID | None = None,
    campaign_id: uuid.UUID | None = None,
    end_date=None,
    external_subscription_id: str = "",
) -> Pledge:
    """
    Create a recurring giving commitment (Pledge).
    External subscription ID is stored if provided by the payment provider.
    """
    pledge = Pledge.objects.create(
        school_id=school_id,
        donor_id=donor_id,
        campaign_id=campaign_id,
        total_amount=total_amount,
        start_date=start_date,
        end_date=end_date,
        frequency=frequency,
        status="active",
        external_subscription_id=external_subscription_id,
    )
    return pledge


@transaction.atomic
def cancel_pledge(*, pledge_id: uuid.UUID, school_id: uuid.UUID) -> Pledge:
    """Cancel an active pledge."""
    pledge = Pledge.objects.select_for_update().get(id=pledge_id, school_id=school_id)
    if pledge.status == "cancelled":
        raise ValueError(f"Pledge {pledge_id} is already cancelled.")
    pledge.status = "cancelled"
    pledge.save(update_fields=["status"])
    return pledge


# ---------------------------------------------------------------------------
# Sponsorship agreement checkout & payment confirmation
# ---------------------------------------------------------------------------

@transaction.atomic
def create_sponsorship_checkout(
    *,
    school_id: uuid.UUID,
    package_id: uuid.UUID,
    start_date,
    sponsor_id: uuid.UUID | None = None,
    campaign_id: uuid.UUID | None = None,
    end_date=None,
) -> SponsorshipAgreement:
    """
    Create a pending SponsorshipAgreement and open a provider checkout session.
    """
    package = SponsorshipPackage.objects.get(id=package_id, school_id=school_id)

    provider = get_provider()
    currency = getattr(settings, "ADVANCEMENT_CURRENCY", "usd")

    metadata: dict = {
        "school_id": str(school_id),
        "sponsor_id": str(sponsor_id) if sponsor_id else None,
        "package_id": str(package_id),
    }

    session = provider.create_checkout_session(
        amount=float(package.price),
        currency=currency,
        metadata=metadata,
    )

    agreement = SponsorshipAgreement.objects.create(
        school_id=school_id,
        sponsor_id=sponsor_id,
        package=package,
        campaign_id=campaign_id,
        amount=package.price,
        status="pending",
        start_date=start_date,
        end_date=end_date,
        provider=provider.PROVIDER_NAME,
        provider_payment_id=session["provider_payment_id"],
    )
    return agreement


@transaction.atomic
def mark_sponsorship_paid(
    *, agreement_id: uuid.UUID, school_id: uuid.UUID
) -> SponsorshipAgreement:
    """
    Confirm payment on a SponsorshipAgreement — transitions pending → active.
    Creates the AdvancementTransaction revenue entry.

    Raises SponsorshipAgreement.DoesNotExist if not found for this school.
    Raises ValueError if already active/expired/cancelled.
    """
    agreement = SponsorshipAgreement.objects.select_for_update().get(
        id=agreement_id, school_id=school_id
    )

    if agreement.status != "pending":
        raise ValueError(
            f"SponsorshipAgreement {agreement_id} cannot be activated from status '{agreement.status}'."
        )

    agreement.status = "active"
    agreement.save(update_fields=["status"])

    AdvancementTransaction.objects.create(
        school_id=school_id,
        category="sponsorship",
        amount=agreement.amount,
        description=f"SponsorshipAgreement {agreement.id} activated",
        reference_id=agreement.id,
    )

    return agreement


# ---------------------------------------------------------------------------
# QR ticket check-in
# ---------------------------------------------------------------------------

@transaction.atomic
def check_in_ticket_by_qr(
    *,
    school_id: uuid.UUID,
    qr_code: str,
    scanned_by_id: uuid.UUID | None = None,
) -> TicketScan:
    """
    Attempt to check in a ticket by QR code.

    - Valid first scan  → checked_in=True, result="accepted"
    - Already checked in → result="duplicate"
    - QR not found       → result="invalid" (ticket FK left null)

    Returns the TicketScan audit record.
    """
    try:
        ticket = Ticket.objects.select_for_update().get(
            school_id=school_id,
            qr_code=qr_code,
        )
    except Ticket.DoesNotExist:
        scan = TicketScan.objects.create(
            school_id=school_id,
            ticket=None,
            qr_attempted=qr_code,
            scanned_by_id=scanned_by_id,
            result="invalid",
        )
        return scan

    if ticket.checked_in:
        scan = TicketScan.objects.create(
            school_id=school_id,
            ticket=ticket,
            qr_attempted=qr_code,
            scanned_by_id=scanned_by_id,
            result="duplicate",
        )
        return scan

    ticket.checked_in = True
    ticket.checked_in_at = timezone.now()
    ticket.save(update_fields=["checked_in", "checked_in_at"])

    scan = TicketScan.objects.create(
        school_id=school_id,
        ticket=ticket,
        qr_attempted=qr_code,
        scanned_by_id=scanned_by_id,
        result="accepted",
    )
    return scan
