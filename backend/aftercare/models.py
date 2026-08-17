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
    """Per-school extended-care configuration."""

    # Compatibility-only predecessor identifier. New writes use school_fk.
    school_id = models.IntegerField(db_index=True, unique=True, null=True, blank=True)
    school_fk = models.OneToOneField(
        "core.School",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="aftercare_program_config",
        db_column="school_uuid_id",
    )

    start_time = models.TimeField(default="15:00")
    end_time = models.TimeField(default="18:00")
    late_fee_per_10_min = models.DecimalField(max_digits=8, decimal_places=2, default=10.00)
    late_fee_grace_minutes = models.IntegerField(default=0)
    late_fee_cap = models.DecimalField(max_digits=8, decimal_places=2, default=100.00)
    ratio_k_2 = models.IntegerField(default=12)
    ratio_3_5 = models.IntegerField(default=15)
    ratio_6_8 = models.IntegerField(default=18)
    ratio_9_12 = models.IntegerField(default=20)
    default_billing_model = models.CharField(max_length=20, choices=BILLING_MODELS, default="FLAT_MONTHLY")
    dropin_daily_rate = models.DecimalField(max_digits=8, decimal_places=2, default=15.00)
    prepaid_session_unit_price = models.DecimalField(max_digits=8, decimal_places=2, default=12.00)
    monthly_rate_1_day = models.DecimalField(max_digits=8, decimal_places=2, default=60.00)
    monthly_rate_2_days = models.DecimalField(max_digits=8, decimal_places=2, default=105.00)
    monthly_rate_3_days = models.DecimalField(max_digits=8, decimal_places=2, default=145.00)
    monthly_rate_4_days = models.DecimalField(max_digits=8, decimal_places=2, default=180.00)
    monthly_rate_5_days = models.DecimalField(max_digits=8, decimal_places=2, default=210.00)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AftercareProgramConfig(school={self.school_fk_id or self.school_id})"


class AftercareEnrollment(models.Model):
    """A student enrolled in extended care for a date range and day pattern."""

    school_id = models.IntegerField(db_index=True, null=True, blank=True)
    student_id = models.IntegerField(db_index=True, null=True, blank=True)
    school_fk = models.ForeignKey(
        "core.School", on_delete=models.PROTECT, null=True, blank=True,
        related_name="aftercare_enrollments", db_column="school_uuid_id",
    )
    student_fk = models.ForeignKey(
        "households.Student", on_delete=models.PROTECT, null=True, blank=True,
        related_name="aftercare_enrollments", db_column="student_uuid_id",
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
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
            models.Index(fields=["school_fk", "is_active"]),
            models.Index(fields=["school_fk", "student_fk"]),
        ]


class AftercarePickupContact(models.Model):
    """Authorized pickup list per canonical student."""

    school_id = models.IntegerField(db_index=True, null=True, blank=True)
    student_id = models.IntegerField(db_index=True, null=True, blank=True)
    school_fk = models.ForeignKey(
        "core.School", on_delete=models.PROTECT, null=True, blank=True,
        related_name="aftercare_pickup_contacts", db_column="school_uuid_id",
    )
    student_fk = models.ForeignKey(
        "households.Student", on_delete=models.PROTECT, null=True, blank=True,
        related_name="aftercare_pickup_contacts", db_column="student_uuid_id",
    )
    name = models.CharField(max_length=120)
    relationship = models.CharField(max_length=80, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["school_id", "student_id", "is_active"]),
            models.Index(fields=["school_fk", "student_fk", "is_active"]),
        ]


class AftercareAttendance(models.Model):
    """One extended-care attendance record per canonical student per day."""

    school_id = models.IntegerField(db_index=True, null=True, blank=True)
    student_id = models.IntegerField(db_index=True, null=True, blank=True)
    school_fk = models.ForeignKey(
        "core.School", on_delete=models.PROTECT, null=True, blank=True,
        related_name="aftercare_attendance", db_column="school_uuid_id",
    )
    student_fk = models.ForeignKey(
        "households.Student", on_delete=models.PROTECT, null=True, blank=True,
        related_name="aftercare_attendance", db_column="student_uuid_id",
    )
    date = models.DateField(db_index=True)
    checkin_time = models.DateTimeField()
    checkout_time = models.DateTimeField(null=True, blank=True)
    pickup_contact_id = models.IntegerField(null=True, blank=True)
    pickup_contact_fk = models.ForeignKey(
        AftercarePickupContact, on_delete=models.PROTECT, null=True, blank=True,
        related_name="attendance_pickups", db_column="pickup_contact_uuid_id",
    )
    pickup_name_freeform = models.CharField(max_length=120, blank=True)
    pickup_verified = models.BooleanField(default=False)
    late_minutes = models.IntegerField(default=0)
    late_fee_cents = models.IntegerField(default=0)
    late_fee_charge_id = models.CharField(max_length=64, null=True, blank=True)
    notes = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("school_id", "student_id", "date")]
        constraints = [
            models.UniqueConstraint(
                fields=["school_fk", "student_fk", "date"],
                condition=models.Q(school_fk__isnull=False, student_fk__isnull=False),
                name="aftercare_attendance_canonical_unique",
            )
        ]
        indexes = [
            models.Index(fields=["school_id", "date"]),
            models.Index(fields=["school_fk", "date"]),
        ]


class AftercareIncident(models.Model):
    """Behavioral/safety incident during extended care."""

    school_id = models.IntegerField(db_index=True, null=True, blank=True)
    student_id = models.IntegerField(db_index=True, null=True, blank=True)
    school_fk = models.ForeignKey(
        "core.School", on_delete=models.PROTECT, null=True, blank=True,
        related_name="aftercare_incidents", db_column="school_uuid_id",
    )
    student_fk = models.ForeignKey(
        "households.Student", on_delete=models.PROTECT, null=True, blank=True,
        related_name="aftercare_incidents", db_column="student_uuid_id",
    )
    attendance_id = models.IntegerField(null=True, blank=True)
    attendance_fk = models.ForeignKey(
        AftercareAttendance, on_delete=models.PROTECT, null=True, blank=True,
        related_name="incidents", db_column="attendance_uuid_id",
    )
    occurred_at = models.DateTimeField(default=timezone.now)
    severity = models.CharField(max_length=20, choices=INCIDENT_SEVERITY, default="MINOR")
    description = models.TextField()
    parent_notified = models.BooleanField(default=False)
    discipline_record_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["school_id", "student_id", "occurred_at"]),
            models.Index(fields=["school_id", "severity", "occurred_at"]),
            models.Index(fields=["school_fk", "student_fk", "occurred_at"]),
            models.Index(fields=["school_fk", "severity", "occurred_at"]),
        ]


class AftercareMonthlyChargeRun(models.Model):
    """Idempotency guard for monthly flat billing runs."""

    school_id = models.IntegerField(db_index=True, null=True, blank=True)
    school_fk = models.ForeignKey(
        "core.School", on_delete=models.PROTECT, null=True, blank=True,
        related_name="aftercare_monthly_charge_runs", db_column="school_uuid_id",
    )
    year = models.IntegerField()
    month = models.IntegerField()
    ran_at = models.DateTimeField(default=timezone.now)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = [("school_id", "year", "month")]
        constraints = [
            models.UniqueConstraint(
                fields=["school_fk", "year", "month"],
                condition=models.Q(school_fk__isnull=False),
                name="aftercare_charge_run_canonical_unique",
            )
        ]
        indexes = [
            models.Index(fields=["school_id", "year", "month"]),
            models.Index(fields=["school_fk", "year", "month"]),
        ]
