"""
term_structure_wizard/models.py

Three canonical models + one wizard session model.

State machine (session):
    draft → configured → periods_set → committed → verified

Invariants:
    - UniqueConstraint(school, academic_year) on TermStructure — one per year per school
    - MarkingPeriod: UniqueConstraint(term_structure, code)
    - MarkingPeriod: CheckConstraint(start_date <= end_date)
    - Period ordering, adjacency, and full-year coverage enforced in views (not DB)
    - Term code lock: at commit time, TermWeight.term_code ⊆ MarkingPeriod.code
    - is_active flip: select_for_update + update at commit (no-op sibling flip due to unique constraint,
      but pattern is kept for consistency with #14–#17)
"""
import uuid

from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint

from core.models import AcademicYear, School


VALID_STRUCTURE_TYPES = {"SEMESTER", "QUARTER", "TRIMESTER", "CUSTOM"}


class TermStructure(models.Model):
    """
    One per (school, academic_year) — enforced by UniqueConstraint.
    Holds the structure type; MarkingPeriod rows are the child records.
    """
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school         = models.ForeignKey(School, on_delete=models.CASCADE, related_name="term_structures")
    academic_year  = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="term_structures")
    structure_type = models.CharField(max_length=20)   # SEMESTER | QUARTER | TRIMESTER | CUSTOM
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["school", "academic_year"],
                name="uniq_term_structure_school_year",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "is_active"]),
        ]

    def __str__(self):
        return f"TermStructure({self.structure_type}, ay={self.academic_year_id})"


class MarkingPeriod(models.Model):
    """
    Child of TermStructure.  Rows are ordered, non-overlapping, and must
    cover the full academic year (enforced in views at commit time).
    """
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    term_structure = models.ForeignKey(TermStructure, on_delete=models.CASCADE, related_name="marking_periods")
    code           = models.CharField(max_length=20)    # Q1, Q2, S1, S2, T1 …
    name           = models.CharField(max_length=100)
    start_date     = models.DateField()
    end_date       = models.DateField()
    ordering       = models.IntegerField()
    is_grade_term  = models.BooleanField(default=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["term_structure", "code"],
                name="uniq_marking_period_code",
            ),
            CheckConstraint(
                condition=Q(start_date__lte=F("end_date")),
                name="chk_marking_period_start_lte_end",
            ),
        ]
        ordering = ["ordering"]

    def __str__(self):
        return f"MarkingPeriod({self.code}, {self.start_date}–{self.end_date})"


class TermStructureWizardSession(models.Model):
    STATUS_DRAFT       = "draft"
    STATUS_CONFIGURED  = "configured"
    STATUS_PERIODS_SET = "periods_set"
    STATUS_COMMITTED   = "committed"
    STATUS_VERIFIED    = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT,       "Draft"),
        (STATUS_CONFIGURED,  "Configured"),
        (STATUS_PERIODS_SET, "Periods Set"),
        (STATUS_COMMITTED,   "Committed"),
        (STATUS_VERIFIED,    "Verified"),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school         = models.ForeignKey(School, on_delete=models.CASCADE, related_name="term_structure_wizard_sessions")
    created_by     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="term_structure_wizard_sessions",
    )
    academic_year  = models.ForeignKey(
        AcademicYear,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="term_structure_wizard_sessions",
    )
    structure_config = models.JSONField(null=True, blank=True)   # {structure_type}
    periods_config   = models.JSONField(default=list)            # [{code, name, start_date, end_date, ordering, is_grade_term}]
    commit_result    = models.JSONField(null=True, blank=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "status"]),
        ]

    def __str__(self):
        return f"TermStructureWizardSession({self.status}, school={self.school_id})"
