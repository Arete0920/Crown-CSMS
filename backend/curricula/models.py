import uuid
from django.db import models
from academics.models import Course


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CurriculumMap(TimeStampedModel):
    """
    A curriculum map defines the structured learning path for a course.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="curriculum_maps",
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    grade_band = models.CharField(max_length=32, blank=True, default="")
    subject = models.CharField(max_length=80, blank=True, default="")
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "curriculum_map"
        indexes = [
            models.Index(fields=["school_id", "course"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.course.code})"


class Unit(TimeStampedModel):
    """
    A unit is a major learning module within a curriculum map.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    curriculum_map = models.ForeignKey(
        CurriculumMap,
        on_delete=models.CASCADE,
        related_name="units",
    )

    sequence = models.IntegerField(default=0, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    overview = models.TextField(blank=True, default="")

    class Meta:
        db_table = "curriculum_unit"
        indexes = [
            models.Index(fields=["school_id", "curriculum_map", "sequence"]),
        ]
        ordering = ["curriculum_map", "sequence"]

    def __str__(self):
        return f"Unit {self.sequence}: {self.title}"


class Lesson(TimeStampedModel):
    """
    A lesson is a specific teaching module within a unit.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="lessons",
    )

    sequence = models.IntegerField(default=0, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    objectives = models.TextField(blank=True, default="")  # Learning objectives
    resources = models.TextField(blank=True, default="")   # Teaching resources

    class Meta:
        db_table = "curriculum_lesson"
        indexes = [
            models.Index(fields=["school_id", "unit", "sequence"]),
        ]
        ordering = ["unit", "sequence"]

    def __str__(self):
        return f"Lesson {self.sequence}: {self.title}"
