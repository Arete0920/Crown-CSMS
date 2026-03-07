"""
Stage 3.4 Models — Receipts + Sponsor placements.

Crown UUID pattern: school_id / event_id / order_id are UUIDFields (no FK to
School or cross-app models). This keeps advancement fully self-contained and
avoids migration coupling.

Models:
    Receipt              – full financial record per fulfilled order
    SponsorAsset         – reusable logo/brand entry per school
    EventSponsorPlacement – which sponsors appear on a given event purchase page
                            and are injected into PDFs / Wallet passes
"""
from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class Receipt(models.Model):
    """
    Created once per fulfilled PendingSeatOrder after Stripe webhook confirms
    payment.  Stores ticket subtotal, optional donation amount, and provider
    payment reference for accounting.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    # References PendingSeatOrder.id (UUIDField — no FK to avoid cross-model coupling)
    order_id = models.UUIDField(db_index=True, unique=True)

    # Denormalised for easy querying without joining orders
    event_id = models.UUIDField(db_index=True)
    purchaser_email = models.EmailField()

    receipt_number = models.CharField(max_length=80, unique=True)

    # Financial breakdown (Decimal for accounting accuracy)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    donation = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Provider provenance
    provider = models.CharField(max_length=50, default="stripe")
    provider_payment_intent_id = models.CharField(max_length=255, blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school_id", "event_id"], name="receipt_school_event_idx"),
        ]

    def __str__(self) -> str:
        return f"Receipt {self.receipt_number} — {self.purchaser_email}"


class SponsorAsset(models.Model):
    """
    Reusable sponsor brand entry per school.  The logo_url is an absolute URL
    (CDN / media endpoint).  Embedded into PDFs and Wallet passes server-side;
    rendered as tiles in the pre-checkout UI.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    sponsor_name = models.CharField(max_length=255)
    logo_url = models.URLField(max_length=512)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["sponsor_name"]
        indexes = [
            models.Index(fields=["school_id"], name="sponsorasset_school_idx"),
        ]

    def __str__(self) -> str:
        return self.sponsor_name


class EventSponsorPlacement(models.Model):
    """
    Associates a SponsorAsset with a specific event, controlling where the
    logo appears (pre-checkout tiles, receipt PDF, Wallet pass).

    tier examples: "title", "gold", "silver", "standard"
    sort_order: lower = higher prominence (title sponsor first)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    event_id = models.UUIDField(db_index=True)

    sponsor = models.ForeignKey(
        SponsorAsset,
        on_delete=models.PROTECT,
        related_name="placements",
    )

    tier = models.CharField(max_length=30, default="standard")
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "tier"]
        unique_together = [("school_id", "event_id", "sponsor")]
        indexes = [
            models.Index(fields=["school_id", "event_id"], name="evtsponsor_school_event_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.sponsor.sponsor_name} @ event {self.event_id} ({self.tier})"
