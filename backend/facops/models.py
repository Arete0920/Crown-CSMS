# backend/facops/models.py
from __future__ import annotations

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Facilities & Maintenance models
# ---------------------------------------------------------------------------

class Location(TimeStampedModel):
    """Building/campus areas; supports hierarchy (campus → building → floor → room)."""
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="facops_locations",
    )
    name = models.CharField(max_length=200)
    kind = models.CharField(
        max_length=50,
        default="room",  # campus / building / floor / room / other
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["school", "name"])]

    def __str__(self) -> str:
        return self.name


class Asset(TimeStampedModel):
    """Maintainable item: HVAC, doors, IT equipment, playground, kitchen appliances."""
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="facops_assets",
    )
    name = models.CharField(max_length=200)
    asset_tag = models.CharField(max_length=64, blank=True, default="")
    location = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assets",
    )
    category = models.CharField(max_length=100, default="general")
    manufacturer = models.CharField(max_length=120, blank=True, default="")
    model = models.CharField(max_length=120, blank=True, default="")
    serial_number = models.CharField(max_length=120, blank=True, default="")
    installed_on = models.DateField(null=True, blank=True)
    retired_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["school", "category"]),
            models.Index(fields=["school", "asset_tag"]),
        ]

    def __str__(self) -> str:
        return self.name


class WorkOrder(TimeStampedModel):
    STATUS_NEW = "NEW"
    STATUS_TRIAGED = "TRIAGED"
    STATUS_ASSIGNED = "ASSIGNED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_BLOCKED = "BLOCKED"
    STATUS_DONE = "DONE"
    STATUS_CANCELED = "CANCELED"
    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_TRIAGED, "Triaged"),
        (STATUS_ASSIGNED, "Assigned"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_BLOCKED, "Blocked"),
        (STATUS_DONE, "Done"),
        (STATUS_CANCELED, "Canceled"),
    ]

    PRIORITY_LOW = "LOW"
    PRIORITY_NORMAL = "NORMAL"
    PRIORITY_HIGH = "HIGH"
    PRIORITY_URGENT = "URGENT"
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_NORMAL, "Normal"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_URGENT, "Urgent"),
    ]

    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="facops_work_orders",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_NORMAL,
    )
    category = models.CharField(max_length=100, default="general")
    location = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="work_orders",
    )
    asset = models.ForeignKey(
        Asset,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="work_orders",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="facops_work_orders_requested",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="facops_work_orders_assigned",
    )
    due_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    labor_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["school", "status"]),
            models.Index(fields=["school", "priority"]),
            models.Index(fields=["school", "created_at"]),
        ]

    def __str__(self) -> str:
        return self.title


class WorkOrderComment(TimeStampedModel):
    """Threaded note on a work order."""
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="facops_comments",
    )
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="facops_comments",
    )
    body = models.TextField()


# ---------------------------------------------------------------------------
# Security & Safety models
# ---------------------------------------------------------------------------

class SafetyIncident(TimeStampedModel):
    SEV_INFO = "INFO"
    SEV_LOW = "LOW"
    SEV_MED = "MEDIUM"
    SEV_HIGH = "HIGH"
    SEV_CRIT = "CRITICAL"
    SEVERITY_CHOICES = [
        (SEV_INFO, "Info"),
        (SEV_LOW, "Low"),
        (SEV_MED, "Medium"),
        (SEV_HIGH, "High"),
        (SEV_CRIT, "Critical"),
    ]

    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="safety_incidents",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default=SEV_LOW,
    )
    location = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="safety_incidents",
    )
    related_asset = models.ForeignKey(
        Asset,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="safety_incidents",
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="incidents_reported",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="incidents_assigned",
    )
    occurred_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "severity"]),
            models.Index(fields=["school", "created_at"]),
        ]

    def __str__(self) -> str:
        return self.title


class Drill(TimeStampedModel):
    TYPE_FIRE = "FIRE"
    TYPE_LOCKDOWN = "LOCKDOWN"
    TYPE_SHELTER = "SHELTER"
    TYPE_EVAC = "EVACUATION"
    TYPE_OTHER = "OTHER"
    TYPE_CHOICES = [
        (TYPE_FIRE, "Fire"),
        (TYPE_LOCKDOWN, "Lockdown"),
        (TYPE_SHELTER, "Shelter"),
        (TYPE_EVAC, "Evacuation"),
        (TYPE_OTHER, "Other"),
    ]

    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="safety_drills",
    )
    drill_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_FIRE,
    )
    planned_for = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="drills_created",
    )

    class Meta:
        indexes = [models.Index(fields=["school", "planned_for"])]

    def __str__(self) -> str:
        return f"{self.drill_type} drill ({self.planned_for})"


class VisitorLog(TimeStampedModel):
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="visitor_logs",
    )
    name = models.CharField(max_length=200)
    purpose = models.CharField(max_length=200, blank=True, default="")
    checked_in_at = models.DateTimeField(auto_now_add=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    badge_id = models.CharField(max_length=64, blank=True, default="")
    external_ref = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["school", "checked_in_at"])]

    def __str__(self) -> str:
        return f"{self.name} ({self.checked_in_at})"


class Alert(TimeStampedModel):
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="facops_alerts",
    )
    kind = models.CharField(max_length=50, default="SECURITY")  # SECURITY / FACILITIES / OTHER
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True, default="")
    emitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="facops_alerts_emitted",
    )
    channel = models.CharField(max_length=50, default="TEAMS")  # TEAMS / EMAIL / SMS
    external_ref = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["school", "kind"])]

    def __str__(self) -> str:
        return self.title
