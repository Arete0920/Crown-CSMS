from django.db import models
from django.utils import timezone

DAYS = [
    ("MON", "Monday"),
    ("TUE", "Tuesday"),
    ("WED", "Wednesday"),
    ("THU", "Thursday"),
    ("FRI", "Friday"),
]

BILLING_MODELS = [
    ("FLAT_MONTHLY", "Flat Monthly"),
    ("PREPAID", "Prepaid Sessions"),
    ("DROPIN", "Drop-in Daily"),
]

INCIDENT_SEVERITY = [
    ("MINOR", "Minor"),
    ("MODERATE", "Moderate"),
    ("MAJOR", "Major"),
]


class AftercareProgramConfig(models.Model):
    """
    Per-tenant configuration — set via CrownMagus Aftercare Setup Wizard.
    Exactly one row per school (unique=True on school_id).
    """
    school_id = models.IntegerField(db_index=True, unique=True)

    # Operational times (stored as local time strings; display/parse in views)
    start_time = models.TimeField(default="15:00")
    end_time = models.TimeField(default="18:00")

    # Late fee policy
    late_fee_per_10_min = models.DecimalField(max_digits=8, decimal_places=2, default=10.00)
    late_fee_grace_minutes = models.IntegerField(default=0)
    late_fee_cap = models.DecimalField(max_digits=8, decimal_places=2, default=100.00)

    # Staffing ratio policy (students per staff; soft guidance for now)
    ratio_k_2 = models.IntegerField(default=12)
    ratio_3_5 = models.IntegerField(default=15)
    ratio_6_8 = models.IntegerField(default=18)
    ratio_9_12 = models.IntegerField(default=20)

    # Billing defaults
    default_billing_model = models.CharField(max_length=20, choices=BILLING_MODELS, default="FLAT_MONTHLY")
    dropin_daily_rate = models.DecimalField(max_digits=8, decimal_places=2, default=15.00)

    # Prepaid default
    prepaid_session_unit_price = models.DecimalField(max_digits=8, decimal_places=2, default=12.00)

    # Flat monthly defaults
    monthly_rate_1_day = models.DecimalField(max_digits=8, decimal_places=2, default=60.00)
    monthly_rate_2_days = models.DecimalField(max_digits=8, decimal_places=2, default=105.00)
    monthly_rate_3_days = models.DecimalField(max_digits=8, decimal_places=2, default=145.00)
    monthly_rate_4_days = models.DecimalField(max_digits=8, decimal_places=2, default=180.00)
    monthly_rate_5_days = models.DecimalField(max_digits=8, decimal_places=2, default=210.00)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AftercareProgramConfig(school_id={self.school_id})"


class AftercareEnrollment(models.Model):
    """
    A student enrolled in aftercare for a date range + day pattern.
    """
    school_id = models.IntegerField(db_index=True)
    student_id = models.IntegerField(db_index=True)

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    # e.g. ["MON","WED","FRI"]
    days_of_week = models.JSONField(default=list)

    billing_model = models.CharField(max_length=20, choices=BILLING_MODELS)
    monthly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    prepaid_sessions_balance = models.IntegerField(default=0)

    dropin_daily_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["school_id", "is_active"]),
            models.Index(fields=["school_id", "student_id"]),
        ]


class AftercarePickupContact(models.Model):
    """
    Authorized pickup list per student.
    """
    school_id = models.IntegerField(db_index=True)
    student_id = models.IntegerField(db_index=True)

    name = models.CharField(max_length=120)
    relationship = models.CharField(max_length=80, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["school_id", "student_id", "is_active"]),
        ]


class AftercareAttendance(models.Model):
    """
    One record per student per day. Tracks checkin/checkout + late fee computed at checkout.
    """
    school_id = models.IntegerField(db_index=True)
    student_id = models.IntegerField(db_index=True)
    date = models.DateField(db_index=True)

    checkin_time = models.DateTimeField()
    checkout_time = models.DateTimeField(null=True, blank=True)

    pickup_contact_id = models.IntegerField(null=True, blank=True)
    pickup_name_freeform = models.CharField(max_length=120, blank=True)
    pickup_verified = models.BooleanField(default=False)

    late_minutes = models.IntegerField(default=0)
    late_fee_cents = models.IntegerField(default=0)
    late_fee_charge_id = models.IntegerField(null=True, blank=True)

    notes = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("school_id", "student_id", "date")]
        indexes = [
            models.Index(fields=["school_id", "date"]),
        ]


class AftercareIncident(models.Model):
    """
    Behavioral/safety incident during aftercare.
    MODERATE/MAJOR incidents auto-link to a discipline record.
    """
    school_id = models.IntegerField(db_index=True)
    student_id = models.IntegerField(db_index=True)

    attendance_id = models.IntegerField(null=True, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)

    severity = models.CharField(max_length=20, choices=INCIDENT_SEVERITY, default="MINOR")
    description = models.TextField()

    parent_notified = models.BooleanField(default=False)
    discipline_record_id = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["school_id", "student_id", "occurred_at"]),
            models.Index(fields=["school_id", "severity", "occurred_at"]),
        ]


class AftercareMonthlyChargeRun(models.Model):
    """
    Idempotency guard for monthly flat billing runs.
    One row per (school_id, year, month) — prevents double-charging.
    """
    school_id = models.IntegerField(db_index=True)
    year = models.IntegerField()
    month = models.IntegerField()
    ran_at = models.DateTimeField(default=timezone.now)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = [("school_id", "year", "month")]
        indexes = [
            models.Index(fields=["school_id", "year", "month"]),
        ]
