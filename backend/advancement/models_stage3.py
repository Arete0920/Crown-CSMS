"""
Advancement Platform — Stage 3 Models

All models follow Crown conventions:
  - UUID PK (explicit, no BaseModel)
  - school_id = UUIDField(db_index=True)  (no FK to School — tenant filter pattern)
  - FKs to Stage 1/2 advancement models use direct ForeignKey within the same app

Entities:
  Moves Management:    Relationship, Prospect, Move
  Alumni:              AlumniCohort, AlumniCohortMember
  Memberships:         MembershipTier, Membership
  Seating:             Venue, SeatingMap, EventSeating, Seat, SeatHold, TicketSeat
  Sponsorships:        SponsorshipDeliverable, SponsorImpression
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Moves Management (Major Gifts)
# ---------------------------------------------------------------------------

class Relationship(models.Model):
    """
    A relationship record — alumni, parent, business partner, board member, etc.
    """
    RELATIONSHIP_CHOICES = [
        ("alumni", "Alumni"),
        ("parent", "Parent"),
        ("grandparent", "Grandparent"),
        ("church_partner", "Church Partner"),
        ("business_partner", "Business Partner"),
        ("board", "Board Member"),
        ("friend", "Friend of School"),
        ("staff", "Staff"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    donor = models.ForeignKey(
        "advancement.Donor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="relationships",
    )
    relationship_type = models.CharField(
        max_length=50, choices=RELATIONSHIP_CHOICES, default="friend"
    )
    class_year = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school_id", "relationship_type"], name="rel_school_type_idx"),
        ]

    def __str__(self):
        return f"Relationship [{self.relationship_type}]"


class Prospect(models.Model):
    """
    Major gift prospect profile — links to a Donor, holds capacity tier + assignment.
    """
    CAPACITY_CHOICES = [
        ("unknown", "Unknown"),
        ("tier1", "Tier 1 ($10k+)"),
        ("tier2", "Tier 2 ($5k–$9.9k)"),
        ("tier3", "Tier 3 ($1k–$4.9k)"),
        ("tier4", "Tier 4 (<$1k)"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    donor = models.ForeignKey(
        "advancement.Donor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prospect_profiles",
    )
    capacity_tier = models.CharField(
        max_length=20, choices=CAPACITY_CHOICES, default="unknown"
    )
    interest_tags = models.CharField(max_length=255, blank=True, default="")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_prospects",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school_id", "is_active"], name="prospect_school_active_idx"),
        ]

    def __str__(self):
        return f"Prospect [{self.capacity_tier}]"


class Move(models.Model):
    """
    A single cultivation action/stage transition for a prospect.
    A new Move row is inserted on every transition — provides full history.
    """
    STAGE_CHOICES = [
        ("identified", "Identified"),
        ("qualified", "Qualified"),
        ("cultivating", "Cultivating"),
        ("soliciting", "Soliciting"),
        ("stewarding", "Stewarding"),
        ("closed_won", "Closed Won"),
        ("closed_lost", "Closed Lost"),
    ]
    ACTION_CHOICES = [
        ("call", "Call"),
        ("email", "Email"),
        ("meeting", "Meeting"),
        ("tour", "Tour"),
        ("event", "Event Invite"),
        ("proposal", "Proposal"),
        ("thank_you", "Thank You"),
        ("other", "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    prospect = models.ForeignKey(
        Prospect,
        on_delete=models.CASCADE,
        related_name="moves",
    )
    stage = models.CharField(max_length=30, choices=STAGE_CHOICES, default="identified")
    action_type = models.CharField(max_length=30, choices=ACTION_CHOICES, default="other")
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    summary = models.CharField(max_length=255, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moves_created",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school_id", "stage"], name="move_school_stage_idx"),
            models.Index(fields=["school_id", "prospect_id"], name="move_school_prospect_idx"),
        ]

    def __str__(self):
        return f"Move [{self.stage}] for Prospect {self.prospect_id}"


# ---------------------------------------------------------------------------
# Alumni Cohorts
# ---------------------------------------------------------------------------

class AlumniCohort(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    class_year = models.IntegerField(null=True, blank=True)
    tags = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class AlumniCohortMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    cohort = models.ForeignKey(
        AlumniCohort,
        on_delete=models.CASCADE,
        related_name="members",
    )
    donor = models.ForeignKey(
        "advancement.Donor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cohort_memberships",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("school_id", "cohort", "donor")]

    def __str__(self):
        return f"AlumniCohortMember cohort={self.cohort_id}"


# ---------------------------------------------------------------------------
# Memberships (Booster Club, Annual Giving, etc.)
# ---------------------------------------------------------------------------

class MembershipTier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    annual_price = models.DecimalField(max_digits=12, decimal_places=2)
    benefits = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["annual_price"]

    def __str__(self):
        return self.name


class Membership(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    donor = models.ForeignKey(
        "advancement.Donor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="memberships",
    )
    tier = models.ForeignKey(
        MembershipTier,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    provider = models.CharField(max_length=50, blank=True, default="")
    provider_payment_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school_id", "status"], name="membership_school_status_idx"),
        ]

    def __str__(self):
        return f"Membership [{self.tier_id}] {self.status}"


# ---------------------------------------------------------------------------
# Seating Maps
# ---------------------------------------------------------------------------

class Venue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SeatingMap(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    venue = models.ForeignKey(
        Venue,
        on_delete=models.CASCADE,
        related_name="seating_maps",
    )
    name = models.CharField(max_length=255)
    layout_json = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class EventSeating(models.Model):
    """Links an Event to a SeatingMap + sets seat hold policy."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    event = models.OneToOneField(
        "advancement.Event",
        on_delete=models.CASCADE,
        related_name="seating_config",
    )
    seating_map = models.ForeignKey(
        SeatingMap,
        on_delete=models.PROTECT,
        related_name="event_configs",
    )
    hold_minutes = models.IntegerField(default=10)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"EventSeating for Event {self.event_id}"


class Seat(models.Model):
    """A physical seat in a SeatingMap — section / row / number."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    seating_map = models.ForeignKey(
        SeatingMap,
        on_delete=models.CASCADE,
        related_name="seats",
    )
    section = models.CharField(max_length=50)
    row = models.CharField(max_length=20)
    number = models.CharField(max_length=20)

    class Meta:
        unique_together = [("school_id", "seating_map", "section", "row", "number")]
        indexes = [
            models.Index(fields=["school_id", "seating_map"], name="seat_school_map_idx"),
        ]

    def __str__(self):
        return f"{self.section}-{self.row}-{self.number}"


class SeatHold(models.Model):
    """Temporary hold to prevent double-sales during checkout."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    event = models.ForeignKey(
        "advancement.Event",
        on_delete=models.CASCADE,
        related_name="seat_holds",
    )
    seat = models.ForeignKey(
        Seat,
        on_delete=models.CASCADE,
        related_name="holds",
    )
    held_by_email = models.EmailField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("school_id", "event", "seat")]
        indexes = [
            models.Index(fields=["school_id", "event"], name="seathold_school_event_idx"),
        ]

    def __str__(self):
        return f"SeatHold seat={self.seat_id} expires={self.expires_at}"


class TicketSeat(models.Model):
    """Assigns a purchased Ticket to a confirmed Seat (post-checkout)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    event_id = models.UUIDField(null=True, blank=True, db_index=True)  # scoped per event
    ticket = models.OneToOneField(
        "advancement.Ticket",
        on_delete=models.CASCADE,
        related_name="seat_assignment",
    )
    seat = models.ForeignKey(
        Seat,
        on_delete=models.PROTECT,
        related_name="ticket_assignments",
    )

    class Meta:
        unique_together = [("school_id", "event_id", "seat")]
        indexes = [
            models.Index(fields=["school_id"], name="ticketseat_school_idx"),
        ]

    def __str__(self):
        return f"TicketSeat ticket={self.ticket_id} seat={self.seat_id}"


# ---------------------------------------------------------------------------
# Sponsorship Deliverables / Impressions
# ---------------------------------------------------------------------------

class SponsorshipDeliverable(models.Model):
    """Defines one placement/deliverable within a SponsorshipAgreement."""
    DELIVERABLE_CHOICES = [
        ("banner", "Banner"),
        ("livestream_overlay", "Livestream Overlay"),
        ("program_ad", "Program Ad"),
        ("website_block", "Website Block"),
        ("newsletter", "Newsletter"),
        ("social_post", "Social Post"),
        ("other", "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    agreement = models.ForeignKey(
        "advancement.SponsorshipAgreement",
        on_delete=models.CASCADE,
        related_name="deliverables",
    )
    deliverable_type = models.CharField(
        max_length=40, choices=DELIVERABLE_CHOICES, default="other"
    )
    label = models.CharField(max_length=255, blank=True, default="")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Deliverable [{self.deliverable_type}] {self.label}"


class SponsorImpression(models.Model):
    """Logs an exposure event against a SponsorshipDeliverable."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    deliverable = models.ForeignKey(
        SponsorshipDeliverable,
        on_delete=models.CASCADE,
        related_name="impressions",
    )
    happened_at = models.DateTimeField(default=timezone.now)
    channel = models.CharField(max_length=40, default="unknown")
    count = models.IntegerField(default=1)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ["-happened_at"]
        indexes = [
            models.Index(fields=["school_id", "deliverable"], name="impression_school_deliv_idx"),
        ]

    def __str__(self):
        return f"Impression channel={self.channel} count={self.count}"
