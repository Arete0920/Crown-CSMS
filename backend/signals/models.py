from django.db import models
from django.utils import timezone


class SignalDefinition(models.Model):
    """
    A deterministic, explainable signal rule.
    Examples: attendance_drop_30d, gpa_drop, tuition_delinquent, discipline_spike.
    """
    school_id = models.IntegerField(db_index=True)
    key = models.SlugField(max_length=64)  # unique per school
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    severity_weight = models.IntegerField(default=10)  # 1..100
    is_active = models.BooleanField(default=True)

    # JSON rule config so we can evolve without migrations for every tweak.
    # {"type":"attendance_drop","window_days":30,"threshold_pct":90}
    # {"type":"tuition_delinquent","days_past_due":30,"amount_min":100}
    rule = models.JSONField(default=dict)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("school_id", "key")]
        indexes = [
            models.Index(fields=["school_id", "is_active"]),
        ]

    def __str__(self):
        return f"{self.school_id}:{self.key}"


class StudentRiskSnapshot(models.Model):
    """
    Roll-up view (per student) so dashboards can load fast.
    One row per student per day (latest-wins via update_or_create).
    """
    school_id = models.IntegerField(db_index=True)
    student_id = models.IntegerField(db_index=True)
    as_of_date = models.DateField(db_index=True)

    risk_score = models.IntegerField(default=0)   # 0..100
    risk_level = models.CharField(max_length=12, default="LOW")  # LOW/MED/HIGH
    drivers = models.JSONField(default=list)  # [{"key":..,"weight":..,"summary":..}]

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("school_id", "student_id", "as_of_date")]
        indexes = [
            models.Index(fields=["school_id", "as_of_date", "risk_level"]),
            models.Index(fields=["school_id", "student_id"]),
        ]


class SignalEvent(models.Model):
    """
    Atomic evidence: a signal fired for a student with explainable details.
    """
    school_id = models.IntegerField(db_index=True)
    student_id = models.IntegerField(db_index=True)
    signal_key = models.SlugField(max_length=64, db_index=True)

    weight = models.IntegerField(default=10)
    summary = models.CharField(max_length=200)
    details = models.JSONField(default=dict)  # {"attendance_pct": 88.2, "window_days":30}

    fired_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["school_id", "student_id", "fired_at"]),
            models.Index(fields=["school_id", "signal_key", "fired_at"]),
        ]


class InterventionCase(models.Model):
    """
    Signal -> Human -> Action loop.
    Board sees counts; staff works the queue.
    """
    school_id = models.IntegerField(db_index=True)
    student_id = models.IntegerField(db_index=True)

    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=16, default="OPEN")    # OPEN/IN_PROGRESS/CLOSED
    priority = models.CharField(max_length=12, default="MED")   # LOW/MED/HIGH

    reason = models.CharField(max_length=200)
    linked_signals = models.JSONField(default=list)  # [{"key":..., "weight":...}]
    owner_user_id = models.IntegerField(null=True, blank=True)

    last_action_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["school_id", "status", "priority"]),
            models.Index(fields=["school_id", "student_id", "status"]),
        ]


class InterventionAction(models.Model):
    """
    Timeline of actions: note, call, meeting, plan, follow-up.
    """
    school_id = models.IntegerField(db_index=True)
    case_id = models.IntegerField(db_index=True)

    action_type = models.CharField(max_length=24, default="NOTE")  # NOTE/CALL/MEETING/PLAN/FOLLOWUP
    note = models.TextField()
    created_by_user_id = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["school_id", "case_id", "created_at"]),
        ]


class BoardExecutiveMetric(models.Model):
    """
    Aggregated metrics for Board dashboard (read-only).
    Stores Crown Compass 2.0 indexes as-of date.
    """
    school_id = models.IntegerField(db_index=True)
    as_of_date = models.DateField(db_index=True)

    # Compass indexes 0..100
    enrollment_health = models.IntegerField(default=0)
    financial_health = models.IntegerField(default=0)
    culture_health = models.IntegerField(default=0)
    mission_health = models.IntegerField(default=0)
    retention_risk = models.IntegerField(default=0)  # higher = worse

    # Narrative snippets (explainable + auditable)
    highlights = models.JSONField(default=list)   # ["Re-enrollment +2.1% YoY", ...]
    watchlist = models.JSONField(default=list)    # ["2 accounts >30 days past due", ...]

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("school_id", "as_of_date")]
        indexes = [
            models.Index(fields=["school_id", "as_of_date"]),
        ]
