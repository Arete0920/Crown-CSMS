from django.db import models
from django.utils import timezone
import uuid


# ---------------------------------------------------------------------------
# Existing models (0001_initial) — DO NOT alter field names (migration lock)
# ---------------------------------------------------------------------------

class Donor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, default="")
    source = models.CharField(max_length=120, blank=True, default="")
    lifetime_giving = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Extended fields (Stage 1)
    first_name = models.CharField(max_length=120, blank=True, default="")
    last_name = models.CharField(max_length=120, blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    organization = models.CharField(max_length=255, blank=True, default="")
    donor_type = models.CharField(
        max_length=50,
        choices=[
            ("individual", "Individual"),
            ("business", "Business"),
            ("church", "Church"),
            ("alumni", "Alumni"),
        ],
        default="individual",
    )

    class Meta:
        ordering = ["-lifetime_giving"]

    def __str__(self):
        return self.name


class Campaign(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("upcoming", "Upcoming"),
        ("closing", "Closing"),
        ("completed", "Completed"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=200)
    goal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    raised = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    donors_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="upcoming")
    created_at = models.DateTimeField(auto_now_add=True)

    # Extended fields (Stage 1)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def progress_percent(self):
        if not self.goal or self.goal == 0:
            return 0
        return round(float(self.raised) / float(self.goal) * 100, 1)


# ---------------------------------------------------------------------------
# Stage 1 new models (0002_stage1_advancement)
# ---------------------------------------------------------------------------

class SponsorshipPackage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, default="")
    placement_type = models.CharField(max_length=100, blank=True, default="")
    duration = models.CharField(max_length=100, blank=True, default="")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["price"]

    def __str__(self):
        return self.name


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    capacity = models.PositiveIntegerField(default=0)
    tickets_sold = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return self.name

    def attendance_percent(self):
        if not self.capacity:
            return 0
        return round(self.tickets_sold / self.capacity * 100, 1)

    def seats_remaining(self):
        return max(0, self.capacity - self.tickets_sold)


class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    purchaser_name = models.CharField(max_length=255)
    purchaser_email = models.EmailField()
    qr_code = models.CharField(max_length=255, unique=True)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    purchased_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-purchased_at"]

    def __str__(self):
        return f"{self.purchaser_name} — {self.event.name}"


class StoreItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    inventory = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, default="")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AdvancementTransaction(models.Model):
    """
    Internal revenue ledger for advancement events.
    Separate from core ledger spine (which is household-billing only).
    Categories: donation | event_ticket | sponsorship | store_purchase
    """
    CATEGORY_CHOICES = [
        ("donation", "Donation"),
        ("event_ticket", "Event Ticket"),
        ("sponsorship", "Sponsorship"),
        ("store_purchase", "Store Purchase"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=500, blank=True, default="")
    # nullable UUIDs pointing to Donor / Ticket / StoreItem / SponsorshipPackage
    reference_id = models.UUIDField(null=True, blank=True, db_index=True)
    campaign = models.ForeignKey(
        Campaign,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school_id", "category"], name="adv_txn_school__fb5116_idx"),
            models.Index(fields=["school_id", "created_at"], name="adv_txn_school__606626_idx"),
        ]

    def __str__(self):
        return f"{self.category} ${self.amount}"


# ---------------------------------------------------------------------------
# Stage 2 new models (0003_stage2_advancement)
# ---------------------------------------------------------------------------

class Gift(models.Model):
    """Linked donation record — created at checkout, updated on payment confirmation."""
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    # nullable UUID pointers — donor/campaign may not exist in every flow
    donor_id = models.UUIDField(null=True, blank=True, db_index=True)
    campaign_id = models.UUIDField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    restricted = models.BooleanField(default=False)
    restriction_label = models.CharField(max_length=255, blank=True, default="")
    memo = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="pending")
    provider = models.CharField(max_length=50, blank=True, default="")
    provider_payment_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school_id", "status"], name="gift_school_status_idx"),
        ]

    def __str__(self):
        return f"Gift ${self.amount} [{self.status}]"


class Pledge(models.Model):
    """Commitment to give over a schedule — may map to a recurring subscription."""
    FREQUENCY_CHOICES = [
        ("one_time", "One-time"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("annual", "Annual"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    donor_id = models.UUIDField(null=True, blank=True, db_index=True)
    campaign_id = models.UUIDField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default="monthly")
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="active")
    external_subscription_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school_id", "status"], name="pledge_school_status_idx"),
        ]

    def __str__(self):
        return f"Pledge ${self.total_amount} [{self.frequency}]"


class SponsorshipAgreement(models.Model):
    """A sponsor's binding agreement to a SponsorshipPackage."""
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("active", "Active"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    sponsor_id = models.UUIDField(null=True, blank=True, db_index=True)
    package = models.ForeignKey(
        SponsorshipPackage,
        on_delete=models.PROTECT,
        related_name="agreements",
    )
    campaign_id = models.UUIDField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="pending")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    provider = models.CharField(max_length=50, blank=True, default="")
    provider_payment_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school_id", "status"], name="spons_agr_school_status_idx"),
        ]

    def __str__(self):
        return f"SponsorshipAgreement [{self.status}] ${self.amount}"


class TicketScan(models.Model):
    """Audit trail for every QR check-in attempt (valid or invalid)."""
    RESULT_CHOICES = [
        ("accepted", "Accepted"),
        ("duplicate", "Duplicate"),
        ("invalid", "Invalid"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    # nullable — None when qr_code doesn't match any ticket
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="scans",
    )
    qr_attempted = models.CharField(max_length=255, blank=True, default="")
    scanned_by_id = models.UUIDField(null=True, blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=40, choices=RESULT_CHOICES, default="accepted")

    class Meta:
        ordering = ["-scanned_at"]
        indexes = [
            models.Index(fields=["school_id", "result"], name="ticketscan_school_result_idx"),
        ]

    def __str__(self):
        return f"TicketScan [{self.result}] @ {self.scanned_at}"


# ---------------------------------------------------------------------------
# Additional stage model files – imported here so Django migration detection
# discovers all models in this app from a single entry point.
# ---------------------------------------------------------------------------
from .models_stage3 import (  # noqa: F401
    Relationship, Prospect, Move,
    AlumniCohort, AlumniCohortMember,
    MembershipTier, Membership,
    Venue, SeatingMap, EventSeating, Seat, SeatHold, TicketSeat,
    SponsorshipDeliverable, SponsorImpression,
)
from .models_stage3_2 import PendingSeatOrder, ProcessedWebhookEvent  # noqa: F401
from .models_stage3_3 import EventSectionPrice, EmailOutbox  # noqa: F401
from .models_stage3_4 import Receipt, SponsorAsset, EventSponsorPlacement  # noqa: F401
