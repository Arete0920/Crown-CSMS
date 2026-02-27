# backend/transportation/models.py
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True


class Vehicle(TimeStampedModel):
    VEHICLE_TYPES = [
        ("BUS", "Bus"),
        ("VAN", "Van"),
        ("CARPOOL", "Carpool"),
    ]
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="transport_vehicles",
    )
    vehicle_type = models.CharField(max_length=16, choices=VEHICLE_TYPES)
    name = models.CharField(max_length=64)
    plate = models.CharField(max_length=24, blank=True, default="")
    vin = models.CharField(max_length=32, blank=True, default="")
    capacity = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True, default="")
    insurance_expiry = models.DateField(null=True, blank=True)
    inspection_expiry = models.DateField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "vehicle_type", "is_deleted"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.vehicle_type})"


class Driver(TimeStampedModel):
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="transport_drivers",
    )
    full_name = models.CharField(max_length=96)
    phone = models.CharField(max_length=32, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    is_contractor = models.BooleanField(default=False)
    cdl_number = models.CharField(max_length=32, blank=True, default="")
    cdl_expiry = models.DateField(null=True, blank=True)
    background_check_expiry = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["school", "is_deleted"]),
        ]

    def __str__(self):
        return self.full_name


class Route(TimeStampedModel):
    DIRECTION_CHOICES = [
        ("AM", "AM"),
        ("PM", "PM"),
        ("MID", "Midday"),
    ]
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="transport_routes",
    )
    name = models.CharField(max_length=96)
    direction = models.CharField(max_length=8, choices=DIRECTION_CHOICES, default="AM")
    days_of_week = models.CharField(max_length=32, default="MTWTF")
    active_start = models.DateField(null=True, blank=True)
    active_end = models.DateField(null=True, blank=True)
    default_vehicle = models.ForeignKey(
        Vehicle,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="default_routes",
    )
    default_driver = models.ForeignKey(
        Driver,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="default_routes",
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["school", "direction", "is_deleted"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.direction})"


class Stop(TimeStampedModel):
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="transport_stops",
    )
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="stops")
    order = models.PositiveIntegerField(default=0)
    label = models.CharField(max_length=96)
    address = models.CharField(max_length=200, blank=True, default="")
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    pickup_time = models.TimeField(null=True, blank=True)
    dropoff_time = models.TimeField(null=True, blank=True)
    safety_notes = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["school", "route", "order", "is_deleted"]),
        ]
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.label} (Route {self.route_id})"


class StudentRider(TimeStampedModel):
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="transport_riders",
    )
    student_id = models.UUIDField(db_index=True)  # SIS cross-reference; not a FK to avoid circular deps
    school_year = models.CharField(max_length=9)   # e.g. "2025-2026"
    is_eligible = models.BooleanField(default=True)
    pickup_stop = models.ForeignKey(
        Stop, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="pickup_riders",
    )
    dropoff_stop = models.ForeignKey(
        Stop, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="dropoff_riders",
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["school", "student_id", "school_year", "is_deleted"]),
        ]


class Assignment(TimeStampedModel):
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="transport_assignments",
    )
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="assignments")
    driver = models.ForeignKey(
        Driver, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="assignments",
    )
    vehicle = models.ForeignKey(
        Vehicle, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="assignments",
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_override = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["school", "route", "start_date", "is_deleted"]),
        ]


class RideEvent(TimeStampedModel):
    EVENT_TYPES = [
        ("BOARDED", "Boarded"),
        ("NO_SHOW", "No Show"),
        ("LATE", "Late"),
        ("INCIDENT", "Incident"),
    ]
    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="transport_ride_events",
    )
    service_date = models.DateField(db_index=True)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="events")
    student_id = models.UUIDField(db_index=True)  # SIS cross-reference
    event_type = models.CharField(max_length=16, choices=EVENT_TYPES)
    note = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["school", "service_date", "event_type", "is_deleted"]),
        ]

    def __str__(self):
        return f"{self.event_type} – {self.service_date}"
