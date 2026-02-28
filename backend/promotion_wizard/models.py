from __future__ import annotations
import uuid
from django.db import models
from core.models import School

VALID_GRADE_CODES = frozenset([
    "PK3","PK4","K","1","2","3","4","5","6","7","8","9","10","11","12","GRAD",
])


class PromotionRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="promotion_rules")
    from_grade_code = models.CharField(max_length=8)
    to_grade_code = models.CharField(max_length=8)
    ordering = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "from_grade_code"],
                name="uniq_promo_from_grade_per_school",
            ),
        ]
        ordering = ["ordering", "from_grade_code"]


class PromotionWizardSession(models.Model):
    STATUS = [
        ("draft", "Draft"),
        ("configured", "Configured"),
        ("committed", "Committed"),
        ("verified", "Verified"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=STATUS, default="draft")
    rules = models.JSONField(default=list, blank=True)
    commit_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["school", "status"])]
