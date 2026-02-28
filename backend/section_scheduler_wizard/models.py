from __future__ import annotations
import uuid
from django.db import models
from core.models import School, AcademicYear
from course_catalog_wizard.models import Course
from staff_setup_wizard.models import StaffMember
from room_setup_wizard.models import Room


class Section(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="sections")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="sections")
    section_code = models.CharField(max_length=32)
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    term_code = models.CharField(max_length=16)
    teacher = models.ForeignKey(StaffMember, on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    template_code = models.CharField(max_length=16)
    block_code = models.CharField(max_length=16)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "academic_year", "section_code"],
                name="uniq_section_code_per_year",
            ),
        ]


class SectionSchedulerWizardSession(models.Model):
    STATUS = [
        ("draft", "Draft"),
        ("configured", "Configured"),
        ("sections_set", "Sections Set"),
        ("committed", "Committed"),
        ("verified", "Verified"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=STATUS, default="draft")
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, null=True, blank=True
    )
    term_code = models.CharField(max_length=16, blank=True, default="")
    sections = models.JSONField(default=list, blank=True)
    commit_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["school", "status"])]
