from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


READINESS_STATUS_CHOICES = [
    ("READY", "Ready"),
    ("MISSING_PAYMENT", "Missing Payment"),
    ("MISSING_FORMS", "Missing Forms"),
    ("HEALTH_REVIEW_REQUIRED", "Health Review Required"),
    ("PICKUP_CONTACT_MISSING", "Pickup Contact Missing"),
    ("WAITLISTED", "Waitlisted"),
    ("CAPACITY_BLOCKED", "Capacity Blocked"),
    ("STAFF_REVIEW_REQUIRED", "Staff Review Required"),
    ("BLOCKED", "Blocked"),
]

ENROLLMENT_STATUS_CHOICES = [
    ("REGISTERED", "Registered"),
    ("WAITLISTED", "Waitlisted"),
    ("CANCELLED", "Cancelled"),
]

PAYMENT_STATUS_CHOICES = [
    ("NOT_BILLED", "Not Billed"),
    ("DEPOSIT_DUE", "Deposit Due"),
    ("DEPOSIT_PAID", "Deposit Paid"),
    ("BALANCE_DUE", "Balance Due"),
    ("PAID_IN_FULL", "Paid In Full"),
    ("PAST_DUE", "Past Due"),
    ("REFUNDED", "Refunded"),
    ("CANCELLED", "Cancelled"),
]

HEALTH_REVIEW_STATUS_CHOICES = [
    ("NOT_REQUIRED", "Not Required"),
    ("NEEDS_REVIEW", "Needs Review"),
    ("APPROVED", "Approved"),
]

FORM_STATUS_CHOICES = [
    ("NOT_STARTED", "Not Started"),
    ("MISSING", "Missing"),
    ("IN_PROGRESS", "In Progress"),
    ("COMPLETE", "Complete"),
]

BILLING_POLICY_CHOICES = [
    ("PER_SESSION", "Per Session"),
    ("PER_WEEK", "Per Week"),
    ("FULL_CAMP", "Full Camp"),
]

INCIDENT_SEVERITY_CHOICES = [
    ("LOW", "Low"),
    ("MODERATE", "Moderate"),
    ("HIGH", "High"),
    ("CRITICAL", "Critical"),
]

CLUB_CATEGORY_CHOICES = [
    ("STEM", "STEM"),
    ("ARTS", "Arts"),
    ("SPORTS", "Sports"),
    ("COOKING", "Cooking"),
    ("LEADERSHIP", "Leadership"),
    ("SERVICE", "Service"),
    ("FAITH", "Faith"),
    ("READING", "Reading"),
    ("OTHER", "Other"),
]

CLUB_OFFERING_STATUS_CHOICES = [
    ("DRAFT", "Draft"),
    ("PUBLISHED", "Published"),
]

CLUB_SELECTION_STATUS_CHOICES = [
    ("ENROLLED", "Enrolled"),
    ("WAITLISTED", "Waitlisted"),
    ("CANCELLED", "Cancelled"),
]


class SummerCampProgramConfig(models.Model):
    school = models.OneToOneField(
        "core.School",
        on_delete=models.CASCADE,
        related_name="summer_camp_program_config",
    )
    camp_name = models.CharField(max_length=160, default="Summer Camp")
    default_start_time = models.TimeField(default="08:00")
    default_end_time = models.TimeField(default="15:00")
    default_capacity = models.IntegerField(default=30)
    default_staff_ratio = models.IntegerField(default=10)
    required_form_policy = models.JSONField(default=dict, blank=True)
    billing_policy = models.CharField(max_length=24, choices=BILLING_POLICY_CHOICES, default="PER_SESSION")
    pickup_policy = models.JSONField(default=dict, blank=True)
    health_review_policy = models.JSONField(default=dict, blank=True)
    public_registration_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


class SummerCampProgram(models.Model):
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_programs")
    name = models.CharField(max_length=160)
    program_type = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    grade_band = models.CharField(max_length=64, blank=True)
    location = models.CharField(max_length=120, blank=True)
    public_registration_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("school", "name")]


class SummerCampSession(models.Model):
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_sessions")
    program = models.ForeignKey(SummerCampProgram, on_delete=models.CASCADE, related_name="sessions")
    name = models.CharField(max_length=180)
    theme_title = models.CharField(max_length=180, blank=True)
    theme_story = models.TextField(blank=True)
    scripture_reference = models.CharField(max_length=120, blank=True)
    virtue_focus = models.CharField(max_length=120, blank=True)
    special_event = models.CharField(max_length=180, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.IntegerField(default=0)
    waitlist_capacity = models.IntegerField(default=0)
    price_cents = models.IntegerField(default=0)
    deposit_cents = models.IntegerField(default=0)
    status = models.CharField(max_length=32, default="DRAFT")
    required_forms = models.JSONField(default=list, blank=True)
    required_permissions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("program", "name", "start_date")]
        indexes = [models.Index(fields=["school", "start_date", "status"])]


class SummerCampEnrollment(models.Model):
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_enrollments")
    session = models.ForeignKey(SummerCampSession, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey("households.Student", on_delete=models.SET_NULL, null=True, blank=True, related_name="summer_camp_enrollments")
    household = models.ForeignKey("households.Household", on_delete=models.SET_NULL, null=True, blank=True, related_name="summer_camp_enrollments")
    status = models.CharField(max_length=24, choices=ENROLLMENT_STATUS_CHOICES, default="REGISTERED")
    registration_source = models.CharField(max_length=24, default="EXISTING")
    form_status = models.CharField(max_length=24, choices=FORM_STATUS_CHOICES, default="MISSING")
    payment_status = models.CharField(max_length=24, choices=PAYMENT_STATUS_CHOICES, default="DEPOSIT_DUE")
    health_status = models.CharField(max_length=24, choices=HEALTH_REVIEW_STATUS_CHOICES, default="NEEDS_REVIEW")
    pickup_status = models.CharField(max_length=24, default="MISSING")
    readiness_status = models.CharField(max_length=32, choices=READINESS_STATUS_CHOICES, default="BLOCKED")
    readiness_blockers = models.JSONField(default=list, blank=True)
    waitlist_position = models.IntegerField(null=True, blank=True)
    payment_required_before_attendance = models.BooleanField(default=True)
    balance_due_cents = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=["school", "session", "status"]), models.Index(fields=["school", "student"])]


class SummerCampFormRequirement(models.Model):
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_form_requirements")
    session = models.ForeignKey(SummerCampSession, on_delete=models.CASCADE, related_name="form_requirements")
    form_type = models.CharField(max_length=80)
    required = models.BooleanField(default=True)
    conditional_rule = models.CharField(max_length=240, blank=True)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = [("session", "form_type")]


class SummerCampHealthReview(models.Model):
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_health_reviews")
    enrollment = models.OneToOneField(SummerCampEnrollment, on_delete=models.CASCADE, related_name="health_review")
    allergies = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    restrictions = models.TextField(blank=True)
    emergency_contacts = models.JSONField(default=list, blank=True)
    review_status = models.CharField(max_length=24, choices=HEALTH_REVIEW_STATUS_CHOICES, default="NEEDS_REVIEW")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)


class SummerCampPickupContact(models.Model):
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_pickup_contacts")
    enrollment = models.ForeignKey(SummerCampEnrollment, on_delete=models.CASCADE, related_name="pickup_contacts")
    name = models.CharField(max_length=120)
    relationship = models.CharField(max_length=80, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True)


class SummerCampAttendance(models.Model):
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_attendance")
    session = models.ForeignKey(SummerCampSession, on_delete=models.CASCADE, related_name="attendance")
    student = models.ForeignKey("households.Student", on_delete=models.SET_NULL, null=True, blank=True, related_name="summer_camp_attendance")
    date = models.DateField(db_index=True)
    checkin_time = models.DateTimeField()
    checkout_time = models.DateTimeField(null=True, blank=True)
    pickup_verified = models.BooleanField(default=False)
    # Preserve the identity of the authorized person in historical release records.
    pickup_contact = models.ForeignKey(SummerCampPickupContact, on_delete=models.PROTECT, null=True, blank=True)
    pickup_verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="verified_summer_camp_pickups",
    )
    notes = models.CharField(max_length=240, blank=True)

    class Meta:
        unique_together = [("session", "student", "date")]
        indexes = [models.Index(fields=["school", "date"])]


class SummerCampGroup(models.Model):
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_groups")
    session = models.ForeignKey(SummerCampSession, on_delete=models.CASCADE, related_name="groups")
    name = models.CharField(max_length=120)
    age_band = models.CharField(max_length=64, blank=True)
    counselor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="summer_camp_counselor_groups")
    capacity = models.IntegerField(default=0)

    class Meta:
        unique_together = [("session", "name")]


class SummerCampGroupAssignment(models.Model):
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_group_assignments")
    group = models.ForeignKey(SummerCampGroup, on_delete=models.CASCADE, related_name="assignments")
    enrollment = models.ForeignKey(SummerCampEnrollment, on_delete=models.CASCADE, related_name="group_assignments")
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="summer_camp_group_assignments")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("group", "enrollment")]


class SummerCampClub(models.Model):
    """Reusable elective/activity catalog for Camp sessions within one tenant."""

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_clubs")
    code = models.SlugField(max_length=72)
    name = models.CharField(max_length=160)
    category = models.CharField(max_length=24, choices=CLUB_CATEGORY_CHOICES, default="OTHER")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["school", "code"], name="camp_club_school_code_uq"),
        ]
        indexes = [models.Index(fields=["school", "is_active"], name="camp_club_school_active_idx")]


class SummerCampClubOffering(models.Model):
    """Session-specific scheduled offering of a reusable club."""

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_club_offerings")
    session = models.ForeignKey(SummerCampSession, on_delete=models.CASCADE, related_name="club_offerings")
    club = models.ForeignKey(SummerCampClub, on_delete=models.PROTECT, related_name="offerings")
    weekdays = models.JSONField(default=list)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=120, blank=True)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="summer_camp_club_offerings",
    )
    capacity = models.PositiveIntegerField(default=0)
    waitlist_capacity = models.PositiveIntegerField(default=0)
    optional_charge_cents = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, choices=CLUB_OFFERING_STATUS_CHOICES, default="DRAFT")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session", "club", "start_time"],
                name="camp_club_offering_session_time_uq",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "session", "status"], name="camp_offer_school_session_idx"),
        ]

    def clean(self):
        super().clean()
        if self.session_id and self.session.school_id != self.school_id:
            raise ValidationError("Club offering session belongs to another school.")
        if self.club_id and self.club.school_id != self.school_id:
            raise ValidationError("Club offering catalog item belongs to another school.")
        if self.instructor_id and getattr(self.instructor, "school_id", None) != self.school_id:
            raise ValidationError("Club instructor belongs to another school.")
        if (
            not isinstance(self.weekdays, list)
            or len(self.weekdays) > 7
            or len(set(self.weekdays)) != len(self.weekdays)
            or any(type(day) is not int or not 0 <= day <= 6 for day in self.weekdays)
        ):
            raise ValidationError("Club weekdays must be unique integers in 0..6.")
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Club offering end_time must be after start_time.")
        if self.status == "PUBLISHED":
            if not self.club_id or not self.club.is_active:
                raise ValidationError("Published club offering requires an active catalog item.")
            if not self.weekdays:
                raise ValidationError("Published club offering requires at least one weekday.")
            if self.capacity <= 0:
                raise ValidationError("Published club offering requires positive capacity.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class SummerCampClubSelection(models.Model):
    """Enrollment-scoped club choice with explicit seat/waitlist state."""

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_club_selections")
    offering = models.ForeignKey(SummerCampClubOffering, on_delete=models.PROTECT, related_name="selections")
    enrollment = models.ForeignKey(SummerCampEnrollment, on_delete=models.PROTECT, related_name="club_selections")
    status = models.CharField(max_length=16, choices=CLUB_SELECTION_STATUS_CHOICES, default="ENROLLED")
    waitlist_position = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["offering", "enrollment"], name="camp_club_selection_uq"),
        ]
        indexes = [
            models.Index(fields=["school", "offering", "status"], name="camp_select_school_offer_idx"),
        ]

    def clean(self):
        super().clean()
        if self.offering_id and self.offering.school_id != self.school_id:
            raise ValidationError("Club selection offering belongs to another school.")
        if self.enrollment_id and self.enrollment.school_id != self.school_id:
            raise ValidationError("Club selection enrollment belongs to another school.")
        if (
            self.offering_id
            and self.enrollment_id
            and self.offering.session_id != self.enrollment.session_id
        ):
            raise ValidationError("Club selection must use the enrollment's camp session.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class SummerCampStaffAssignment(models.Model):
    # An unreviewed status string alone never establishes safe supervision.
    CREDENTIAL_PENDING = "PENDING"
    CREDENTIAL_VERIFIED = "VERIFIED"
    CREDENTIAL_REVOKED = "REVOKED"
    CREDENTIAL_STATUS_CHOICES = [
        (CREDENTIAL_PENDING, "Pending review"),
        (CREDENTIAL_VERIFIED, "Verified"),
        (CREDENTIAL_REVOKED, "Revoked"),
    ]
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_staff_assignments")
    session = models.ForeignKey(SummerCampSession, on_delete=models.CASCADE, related_name="staff_assignments")
    staff_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="summer_camp_staff_assignments")
    role = models.CharField(max_length=64)
    credential_status = models.CharField(
        max_length=64, choices=CREDENTIAL_STATUS_CHOICES, default=CREDENTIAL_PENDING,
    )
    credential_verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="summer_camp_staff_credentials_verified",
    )
    credential_verified_at = models.DateTimeField(null=True, blank=True)
    credential_evidence_ref = models.CharField(max_length=160, blank=True, default="")
    assigned_date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = [("session", "staff_user", "role")]


class SummerCampIncident(models.Model):
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_incidents")
    session = models.ForeignKey(SummerCampSession, on_delete=models.CASCADE, related_name="incidents")
    student = models.ForeignKey("households.Student", on_delete=models.SET_NULL, null=True, blank=True, related_name="summer_camp_incidents")
    severity = models.CharField(max_length=16, choices=INCIDENT_SEVERITY_CHOICES, default="LOW")
    category = models.CharField(max_length=80, blank=True)
    description = models.TextField()
    parent_notified = models.BooleanField(default=False)
    health_followup_required = models.BooleanField(default=False)
    discipline_record_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)


class SummerCampBillingLedgerLink(models.Model):
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_billing_links")
    enrollment = models.ForeignKey(SummerCampEnrollment, on_delete=models.CASCADE, related_name="billing_links")
    charge_id = models.CharField(max_length=64, blank=True)
    charge_type = models.CharField(max_length=64, default="SESSION")
    amount_cents = models.IntegerField(default=0)
    status = models.CharField(max_length=24, default="OPEN")
    created_at = models.DateTimeField(default=timezone.now)


class SummerCampConfigWizardState(models.Model):
    school = models.OneToOneField("core.School", on_delete=models.CASCADE, related_name="summer_camp_config_wizard_state")
    completed_steps = models.JSONField(default=list, blank=True)
    is_completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
