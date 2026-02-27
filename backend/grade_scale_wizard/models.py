"""
grade_scale_wizard/models.py

Domain models for the Grade Scale & Report Card Settings Wizard (#17).

Domain models:
  GradeScale      — one active scale per (school, academic_year)
  GradeScaleBand  — ordered, non-overlapping, full-coverage bands for a scale
  TermWeight      — optional per-term weighting (basis points, sum to 10 000)

Wizard session:
  GradeScaleWizardSession — transient scratchpad tracking wizard state
"""

import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint

User = get_user_model()

# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

SCALE_TYPE_LETTER  = "LETTER"
SCALE_TYPE_PERCENT = "PERCENT"
SCALE_TYPE_CHOICES = [
    (SCALE_TYPE_LETTER,  "Letter Grades (A–F)"),
    (SCALE_TYPE_PERCENT, "Percent (0–100)"),
]

ROUNDING_NEAREST = "NEAREST"
ROUNDING_FLOOR   = "FLOOR"
ROUNDING_CEIL    = "CEIL"
ROUNDING_CHOICES = [
    (ROUNDING_NEAREST, "Round to nearest"),
    (ROUNDING_FLOOR,   "Always round down (floor)"),
    (ROUNDING_CEIL,    "Always round up (ceiling)"),
]


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

class GradeScale(models.Model):
    """
    One grading scale per (school, academic_year, name).
    Only one scale may be is_active=True per (school, academic_year) at a time;
    enforced at commit via select_for_update + bulk-deactivate, not by DB constraint
    (to allow PostgreSQL <15 compatibility without partial-unique DDL).
    """

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school        = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="grade_scales"
    )
    academic_year = models.ForeignKey(
        "core.AcademicYear", on_delete=models.CASCADE, related_name="grade_scales"
    )
    name          = models.CharField(max_length=100)
    scale_type    = models.CharField(max_length=10, choices=SCALE_TYPE_CHOICES, default=SCALE_TYPE_LETTER)
    rounding      = models.CharField(max_length=8,  choices=ROUNDING_CHOICES,  default=ROUNDING_NEAREST)
    is_active     = models.BooleanField(default=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["school", "academic_year", "name"],
                name="uniq_grade_scale_school_year_name",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "academic_year", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.school_id} / {self.academic_year_id})"


class GradeScaleBand(models.Model):
    """
    One band in a grading scale (e.g., A = 90–100).

    Band ranges are integer percentages [min_pct, max_pct] inclusive.
    Adjacent bands must satisfy  max_pct[i] + 1 == min_pct[i+1] so that
    together they form full coverage from 0 to 100 with no gaps and no overlaps.

    Validation is enforced in the wizard view; DB constraints catch raw writes.
    """

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scale      = models.ForeignKey(GradeScale, on_delete=models.CASCADE, related_name="bands")
    label      = models.CharField(max_length=20)
    min_pct    = models.IntegerField()
    max_pct    = models.IntegerField()
    ordering   = models.IntegerField()
    gpa_points = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["scale", "label"],    name="uniq_grade_band_scale_label"),
            UniqueConstraint(fields=["scale", "ordering"], name="uniq_grade_band_scale_ordering"),
            CheckConstraint(condition=Q(min_pct__gte=0),   name="chk_band_min_pct_gte_0"),
            CheckConstraint(condition=Q(max_pct__lte=100), name="chk_band_max_pct_lte_100"),
            CheckConstraint(condition=Q(min_pct__lt=F("max_pct")), name="chk_band_min_lt_max"),
        ]
        ordering = ["ordering"]

    def __str__(self):
        return f"{self.label}: {self.min_pct}–{self.max_pct}"


class TermWeight(models.Model):
    """
    Optional per-term weighting for a grade scale.
    Stored as integer basis points (1 bp = 0.01 %).
    All weights for a scale must sum to exactly 10 000 bp (= 100.00 %).
    """

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scale      = models.ForeignKey(GradeScale, on_delete=models.CASCADE, related_name="term_weights")
    term_code  = models.CharField(max_length=20)
    weight_bp  = models.IntegerField(help_text="Basis points (10 000 bp = 100 %)")

    class Meta:
        constraints = [
            UniqueConstraint(fields=["scale", "term_code"], name="uniq_term_weight_scale_code"),
            CheckConstraint(
                condition=Q(weight_bp__gt=0) & Q(weight_bp__lte=10000),
                name="chk_term_weight_bp_range",
            ),
        ]

    def __str__(self):
        return f"{self.term_code}: {self.weight_bp} bp"


# ---------------------------------------------------------------------------
# Wizard session
# ---------------------------------------------------------------------------

class GradeScaleWizardSession(models.Model):
    STATUS_DRAFT        = "draft"
    STATUS_CONFIGURED   = "configured"
    STATUS_BANDS_SET    = "bands_set"
    STATUS_WEIGHTS_SET  = "weights_set"
    STATUS_COMMITTED    = "committed"
    STATUS_VERIFIED     = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT,       "Draft"),
        (STATUS_CONFIGURED,  "Configured"),
        (STATUS_BANDS_SET,   "Bands set"),
        (STATUS_WEIGHTS_SET, "Weights set"),
        (STATUS_COMMITTED,   "Committed"),
        (STATUS_VERIFIED,    "Verified"),
    ]

    # Commit is allowed from either bands_set or weights_set
    COMMITTABLE_STATUSES = {STATUS_BANDS_SET, STATUS_WEIGHTS_SET}

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school         = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="grade_scale_sessions"
    )
    created_by     = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name="grade_scale_sessions"
    )
    academic_year  = models.ForeignKey(
        "core.AcademicYear", null=True, on_delete=models.SET_NULL,
        related_name="grade_scale_sessions",
    )
    scale_config   = models.JSONField(null=True, default=None)
    bands_config   = models.JSONField(default=list)
    weights_config = models.JSONField(null=True, default=None)
    commit_result  = models.JSONField(null=True, default=None)
    status         = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT
    )
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["school", "status"])]
