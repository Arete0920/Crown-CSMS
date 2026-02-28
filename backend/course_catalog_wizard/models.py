from __future__ import annotations
import uuid
from django.db import models
from core.models import School


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="courses")
    code = models.CharField(max_length=24)
    name = models.CharField(max_length=160)
    credits = models.DecimalField(max_digits=4, decimal_places=1, default=1.0)
    department = models.CharField(max_length=80, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["school", "code"], name="uniq_course_code_per_school"),
        ]


class CourseCatalogWizardSession(models.Model):
    STATUS = [
        ("draft", "Draft"),
        ("configured", "Configured"),
        ("committed", "Committed"),
        ("verified", "Verified"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=STATUS, default="draft")
    catalog = models.JSONField(default=list, blank=True)
    commit_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["school", "status"])]
