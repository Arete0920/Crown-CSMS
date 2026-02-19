from django.db import models
from django.utils import timezone

from core.models import School
from core.tenant_models import TenantScopedModel

class GraduationRule(TenantScopedModel):
    """
    Demo-ready v1: only total credits required (+ optional notes).
    Later: per-subject requirements, course codes, credit buckets, GPA rules, service hours, etc.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="graduation_rules")
    name = models.CharField(max_length=120, default="Default Graduation Policy")
    required_total_credits = models.DecimalField(max_digits=6, decimal_places=2, default=24.00)

    # Future-facing knobs (kept simple for v1)
    min_gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["school", "is_active"]),
        ]

    def __str__(self):
        return f"{self.school_id} :: {self.name}"
