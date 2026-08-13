from __future__ import annotations

import uuid

from django.db import models
from core.models import AcademicYear, School
from course_catalog_wizard.models import Course
from staff_setup_wizard.models import StaffMember
from room_setup_wizard.models import Room


class Section(models.Model):
    """Legacy advanced-scheduler section truth retained for reconciliation only.

    New scheduler writes must target academics.Section plus SectionPlacement.
    Retire this table only after COPY -> COMPARE parity is proven.
    """

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


class SectionPlacement(models.Model):
    """Scheduling-owned recurring meeting for a canonical academics.Section.

    A section may have multiple recurring meetings (for example MON/P1 and
    WED/P1, or A-day/P2 and B-day/P3). Each active template/block pair is a
    distinct placement; room and teacher collisions remain fail-closed.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="section_placements")
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="section_placements",
    )
    section = models.ForeignKey(
        "academics.Section",
        on_delete=models.CASCADE,
        related_name="schedule_placements",
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="section_placements",
    )
    day_template = models.ForeignKey(
        "bell_schedule_wizard.DayTemplate",
        on_delete=models.PROTECT,
        related_name="section_placements",
    )
    period_block = models.ForeignKey(
        "bell_schedule_wizard.PeriodBlock",
        on_delete=models.PROTECT,
        related_name="section_placements",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["section", "day_template", "period_block"],
                condition=models.Q(is_active=True),
                name="uniq_active_section_meeting",
            ),
            models.UniqueConstraint(
                fields=["school", "academic_year", "room", "day_template", "period_block"],
                condition=models.Q(room__isnull=False, is_active=True),
                name="uniq_active_room_schedule_slot",
            ),
        ]
        indexes = [
            models.Index(
                fields=["school", "academic_year", "is_active"],
                name="section_pla_school__b514dc_idx",
            ),
            models.Index(
                fields=["school", "day_template", "period_block"],
                name="section_pla_school__50cf2e_idx",
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