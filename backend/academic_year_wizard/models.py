"""
academic_year_wizard/models.py

Session model only.  Commit operates on existing core.AcademicYear and
academics.Term — no new canonical data models live here.

State machine:
    draft → configured → terms_set → committed → verified
"""
import uuid

from django.conf import settings
from django.db import models
from django.db.models import JSONField

from core.models import School


class AcademicYearWizardSession(models.Model):
    STATUS_DRAFT      = "draft"
    STATUS_CONFIGURED = "configured"
    STATUS_TERMS_SET  = "terms_set"
    STATUS_COMMITTED  = "committed"
    STATUS_VERIFIED   = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT,      "Draft"),
        (STATUS_CONFIGURED, "Configured"),
        (STATUS_TERMS_SET,  "Terms Set"),
        (STATUS_COMMITTED,  "Committed"),
        (STATUS_VERIFIED,   "Verified"),
    ]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school     = models.ForeignKey(School, on_delete=models.CASCADE, related_name="academic_year_wizard_sessions")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="academic_year_wizard_sessions",
    )

    # Step 1 — configure
    year_name  = models.CharField(max_length=100, blank=True, default="")
    start_date = models.CharField(max_length=10, blank=True, default="")   # stored as ISO string
    end_date   = models.CharField(max_length=10, blank=True, default="")

    # Step 2 — terms
    terms_config = JSONField(default=list)    # [{code, name, school_year, start_date, end_date, ordering}]

    # Commit result
    commit_result = JSONField(null=True, blank=True)

    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "status"]),
        ]

    def __str__(self):
        return f"AcademicYearWizardSession({self.year_name or 'unnamed'}, {self.status})"
