from __future__ import annotations

from django.conf import settings
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
    pickup_contact = models.ForeignKey(SummerCampPickupContact, on_delete=models.SET_NULL, null=True, blank=True)
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


class SummerCampStaffAssignment(models.Model):
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="summer_camp_staff_assignments")
    session = models.ForeignKey(SummerCampSession, on_delete=models.CASCADE, related_name="staff_assignments")
    staff_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="summer_camp_staff_assignments")
    role = models.CharField(max_length=64)
    credential_status = models.CharField(max_length=64, default="PENDING")
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
