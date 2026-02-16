from __future__ import annotations

from django.db import models
from django.core.validators import MinValueValidator


class CurriculumCourse(models.Model):
    """
    School-scoped curriculum container (what the school teaches).
    """
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="curriculum_courses")
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=64, blank=True, default="")
    grade_level = models.CharField(max_length=32, blank=True, default="")  # e.g., "5", "9", "K", "6-8"
    description = models.TextField(blank=True, default="")

    # Christian-school differentiators (optional, but first-class)
    worldview_theme = models.CharField(max_length=255, blank=True, default="")
    anchor_scripture_ref = models.CharField(max_length=128, blank=True, default="")  # e.g., "Col 3:23"
    anchor_scripture_text = models.TextField(blank=True, default="")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["school", "code"], name="uq_curriculum_course_school_code"),
        ]
        ordering = ["code", "name"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class CurriculumUnit(models.Model):
    """
    A unit within a course: scope/sequence chunk.
    """
    course = models.ForeignKey(CurriculumCourse, on_delete=models.CASCADE, related_name="units")
    order = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    title = models.CharField(max_length=255)

    # pacing (optional)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    essential_question = models.CharField(max_length=255, blank=True, default="")
    big_idea = models.TextField(blank=True, default="")

    worldview_focus = models.CharField(max_length=255, blank=True, default="")
    scripture_ref = models.CharField(max_length=128, blank=True, default="")
    scripture_text = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["course", "order"], name="uq_curriculum_unit_course_order"),
        ]
        ordering = ["course_id", "order"]

    def __str__(self) -> str:
        return f"Unit {self.order}: {self.title}"


class CurriculumLesson(models.Model):
    """
    A lesson inside a unit.
    """
    unit = models.ForeignKey(CurriculumUnit, on_delete=models.CASCADE, related_name="lessons")
    order = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    title = models.CharField(max_length=255)

    planned_date = models.DateField(null=True, blank=True)

    objective = models.TextField(blank=True, default="")
    activities = models.TextField(blank=True, default="")
    assessment = models.TextField(blank=True, default="")

    worldview_focus = models.CharField(max_length=255, blank=True, default="")
    scripture_ref = models.CharField(max_length=128, blank=True, default="")
    scripture_text = models.TextField(blank=True, default="")

    # simple resource links (keep schema stable)
    resources = models.JSONField(default=list, blank=True)  # list of {label,url} dicts

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["unit", "order"], name="uq_curriculum_lesson_unit_order"),
        ]
        ordering = ["unit_id", "order"]

    def __str__(self) -> str:
        return f"Lesson {self.order}: {self.title}"
