"""Relational instructional execution authority for lesson plans."""

import uuid

from django.core.exceptions import ValidationError
from django.db import models

from .models import Lesson, LessonPlan, TimeStampedModel


class LessonExecutionQuerySet(models.QuerySet):
    """Prevent bulk writers from bypassing execution-evidence validation."""

    _guarded_fields = frozenset(
        {
            "school_id",
            "lesson_plan",
            "lesson_plan_id",
            "lesson",
            "lesson_id",
            "sequence_order",
            "delivery_status",
            "planned_minutes",
            "actual_minutes",
            "actual_started_at",
            "actual_completed_at",
            "completion_notes",
        }
    )

    def update(self, **kwargs):
        touched = self._guarded_fields.intersection(kwargs)
        if touched:
            names = ", ".join(sorted(touched))
            raise ValidationError(
                f"LessonPlanLesson guarded fields cannot be changed with QuerySet.update(): {names}. "
                "Use validated instance writes."
            )
        return super().update(**kwargs)

    def bulk_create(self, objs, *args, **kwargs):
        raise ValidationError("LessonPlanLesson cannot be created with bulk_create(); use validated instance writes.")

    def bulk_update(self, objs, fields, *args, **kwargs):
        raise ValidationError("LessonPlanLesson cannot be changed with bulk_update(); use validated instance writes.")


class LessonPlanLesson(TimeStampedModel):
    """A scheduled lesson plus durable evidence of actual instructional delivery."""

    class DeliveryStatus(models.TextChoices):
        PLANNED = "planned", "Planned"
        IN_PROGRESS = "in_progress", "In progress"
        TAUGHT = "taught", "Taught"
        PARTIAL = "partial", "Partially taught"
        SKIPPED = "skipped", "Skipped"
        RESCHEDULED = "rescheduled", "Rescheduled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    lesson_plan = models.ForeignKey(
        LessonPlan,
        on_delete=models.CASCADE,
        related_name="lesson_links",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.PROTECT,
        related_name="lesson_plan_links",
    )
    sequence_order = models.PositiveSmallIntegerField(default=1)
    delivery_status = models.CharField(
        max_length=16,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PLANNED,
        db_index=True,
    )
    planned_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    actual_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    actual_started_at = models.DateTimeField(null=True, blank=True)
    actual_completed_at = models.DateTimeField(null=True, blank=True)
    completion_notes = models.TextField(blank=True, default="")

    objects = LessonExecutionQuerySet.as_manager()

    class Meta:
        app_label = "academics"
        db_table = "lesson_plan_lesson"
        ordering = ["sequence_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["lesson_plan", "lesson"],
                name="uniq_lesson_plan_lesson",
            ),
        ]
        indexes = [
            models.Index(
                fields=["school_id", "lesson_plan", "delivery_status"],
                name="lesson_plan_school__220497_idx",
            ),
            models.Index(
                fields=["school_id", "lesson"],
                name="lesson_plan_school__0f2b0d_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"LessonPlanLesson({self.lesson_plan_id} -> {self.lesson_id}: {self.delivery_status})"
