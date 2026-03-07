from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone

from core.models import School
from households.models import Student


class SignalDefinition(models.Model):
    """
    A deterministic, explainable signal rule scoped to a School.

    Uses UUID FKs so it can join directly to real School/Student rows.
    Examples: aftercare_late_30d, gpa_drop, tuition_delinquent, discipline_spike.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="signal_definitions")
    key = models.SlugField(max_length=64)          # e.g. "aftercare_late_30d"
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    severity_weight = models.IntegerField(default=10)   # 1..100
    is_active = models.BooleanField(default=True)

    # JSON rule config - evolves without new migrations for every parameter tweak.
    # {"type":"aftercare_late","window_days":30,"threshold_count":3}
    rule = models.JSONField(default=dict)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("school", "key")]
        indexes = [
            models.Index(fields=["school", "is_active"]),
        ]

    def __str__(self):
        return f"{self.school_id}:{self.key}"


class StudentRiskSnapshot(models.Model):
    """
    Roll-up per student so dashboards load fast.
    One row per (school, student, as_of_date); latest wins via update_or_create.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="risk_snapshots")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="risk_snapshots")
    as_of_date = models.DateField(db_index=True)

    risk_score = models.IntegerField(default=0)                         # 0..100
    risk_level = models.CharField(max_length=12, default="LOW")         # LOW/MED/HIGH
    drivers = models.JSONField(default=list)   # [{"key":..,"weight":..,"summary":..}]

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("school", "student", "as_of_date")]
        indexes = [
            models.Index(fields=["school", "as_of_date", "risk_level"]),
            models.Index(fields=["school", "student"]),
        ]


class SignalEvent(models.Model):
    """
    Atomic evidence: a signal fired for a student with explainable details.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="signal_events")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="signal_events")
    signal_key = models.SlugField(max_length=64, db_index=True)

    weight = models.IntegerField(default=10)
    summary = models.CharField(max_length=200)
    details = models.JSONField(default=dict)    # {"attendance_pct": 88.2, "window_days": 30}
    fired_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["school", "student", "fired_at"]),
            models.Index(fields=["school", "signal_key", "fired_at"]),
        ]


class InterventionCase(models.Model):
    """
    Signal to Human to Action loop.
    Board sees counts; staff works the queue.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="intervention_cases")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="intervention_cases")

    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=16, default="OPEN")        # OPEN/IN_PROGRESS/CLOSED
    priority = models.CharField(max_length=12, default="MED")       # LOW/MED/HIGH

    reason = models.CharField(max_length=200)
    linked_signals = models.JSONField(default=list)     # [{"key":..., "weight":...}]
    owner_user_id = models.IntegerField(null=True, blank=True)

    last_action_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "status", "priority"]),
            models.Index(fields=["school", "student", "status"]),
        ]


class InterventionAction(models.Model):
    """
    Timeline of actions: note, call, meeting, plan, follow-up.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="intervention_actions")
    case = models.ForeignKey(InterventionCase, on_delete=models.CASCADE, related_name="actions")

    action_type = models.CharField(max_length=24, default="NOTE")   # NOTE/CALL/MEETING/PLAN/FOLLOWUP
    note = models.TextField()
    created_by_user_id = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["school", "case", "created_at"]),
        ]


class BoardExecutiveMetric(models.Model):
    """
    Aggregated metrics for Board dashboard (read-only).
    Stores Crown Compass 2.0 indexes as-of date.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="board_metrics")
    as_of_date = models.DateField(db_index=True)

    # Compass indexes 0..100
    enrollment_health = models.IntegerField(default=0)
    financial_health = models.IntegerField(default=0)
    culture_health = models.IntegerField(default=0)
    mission_health = models.IntegerField(default=0)
    retention_risk = models.IntegerField(default=0)     # higher = worse

    # Explainable narrative snippets
    highlights = models.JSONField(default=list)     # ["Re-enrollment +2.1% YoY", ...]
    watchlist = models.JSONField(default=list)      # ["2 accounts >30 days past due", ...]

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("school", "as_of_date")]
        indexes = [
            models.Index(fields=["school", "as_of_date"]),
        ]
