"""
enrollment_period_wizard/models.py

Domain models for Wizard #16 — Enrollment Period Setup.

  EnrollmentPeriod   – one per (school, academic_year); gated by DB unique constraint.
  GradeCapacity      – one per (school, academic_year, grade_code); gated by DB unique + check constraint.
  EnrollmentPeriodWizardSession – wizard session state machine.

State machine: draft → configured → capacities_set → committed → verified
"""
import uuid

from django.conf import settings
from django.db import models

from core.models import AcademicYear, School

# ---------------------------------------------------------------------------
# Valid grade codes (matches core.GradeLevel.GRADE_CHOICES)
# ---------------------------------------------------------------------------

VALID_GRADE_CODES = frozenset({"PK", "K", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"})


# ---------------------------------------------------------------------------
# Domain model 1: EnrollmentPeriod
# ---------------------------------------------------------------------------

class EnrollmentPeriod(models.Model):
    """
    Defines the enrollment window for a given academic year at a school.
    Exactly one per (school, academic_year) — enforced by DB constraint.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name="enrollment_periods",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="enrollment_periods",
    )
    open_date = models.DateField()
    close_date = models.DateField()
    reenroll_close_date = models.DateField(null=True, blank=True)
    reenroll_first = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "academic_year"],
                name="uniq_enrollment_period_school_year",
            ),
        ]

    def __str__(self):
        return f"EnrollmentPeriod(school={self.school_id}, year={self.academic_year_id})"


# ---------------------------------------------------------------------------
# Domain model 2: GradeCapacity
# ---------------------------------------------------------------------------

class GradeCapacity(models.Model):
    """
    Target seat count per grade for a given academic year at a school.
    Key: (school, academic_year, grade_code) — enforced by DB unique constraint.
    target_seats >= 0 enforced by DB check constraint.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name="grade_capacities",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="grade_capacities",
    )
    grade_code = models.CharField(max_length=3)
    target_seats = models.IntegerField(default=0)
    new_students_allowed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "academic_year", "grade_code"],
                name="uniq_grade_capacity_year_grade",
            ),
            models.CheckConstraint(
                condition=models.Q(target_seats__gte=0),
                name="chk_grade_capacity_seats_gte_0",
            ),
        ]

    def __str__(self):
        return f"GradeCapacity({self.grade_code}, year={self.academic_year_id}, seats={self.target_seats})"


# ---------------------------------------------------------------------------
# Wizard session model
# ---------------------------------------------------------------------------

class EnrollmentPeriodWizardSession(models.Model):
    STATUS_DRAFT          = "draft"
    STATUS_CONFIGURED     = "configured"
    STATUS_CAPACITIES_SET = "capacities_set"
    STATUS_COMMITTED      = "committed"
    STATUS_VERIFIED       = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT,          "Draft"),
        (STATUS_CONFIGURED,     "Configured"),
        (STATUS_CAPACITIES_SET, "Capacities Set"),
        (STATUS_COMMITTED,      "Committed"),
        (STATUS_VERIFIED,       "Verified"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name="enrollment_period_wizard_sessions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="enrollment_period_wizard_sessions",
    )
    # AcademicYear FK — set during configure step; validated to belong to request school
    academic_year = models.ForeignKey(
        AcademicYear,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="enrollment_period_wizard_sessions",
    )
    # Date fields stored as ISO strings; parsed + validated in view
    open_date          = models.CharField(max_length=10, blank=True, default="")
    close_date         = models.CharField(max_length=10, blank=True, default="")
    reenroll_close_date = models.CharField(max_length=10, blank=True, default="")
    reenroll_first     = models.BooleanField(default=False)
    # [{grade_code, target_seats, new_students_allowed}]
    capacities_config  = models.JSONField(default=list)
    commit_result      = models.JSONField(null=True, blank=True)
    status             = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "status"]),
        ]

    def __str__(self):
        return f"EnrollmentPeriodWizardSession(school={self.school_id}, {self.status})"
