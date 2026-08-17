import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from academics.models import Course


class GovernedQuerySet(models.QuerySet):
    """Prevent bulk writers from bypassing curriculum governance signals."""

    def update(self, **kwargs):
        raise ValidationError(
            f"{self.model.__name__} cannot be changed with QuerySet.update(); use validated instance writes."
        )

    def bulk_create(self, objs, *args, **kwargs):
        raise ValidationError(
            f"{self.model.__name__} cannot be created with bulk_create(); use validated instance writes."
        )

    def bulk_update(self, objs, fields, *args, **kwargs):
        raise ValidationError(
            f"{self.model.__name__} cannot be changed with bulk_update(); use validated instance writes."
        )


GovernedManager = models.Manager.from_queryset(GovernedQuerySet)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CurriculumMap(TimeStampedModel):
    """Stable curriculum-map identity for a school course."""

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

    objects = GovernedManager()

    class Meta:
        db_table = "curriculum_map"
        indexes = [models.Index(fields=["school_id", "course"])]

    def __str__(self):
        course_code = self.course.code if self.course else "unassigned"
        return f"{self.title} ({course_code})"


class CurriculumMapVersion(TimeStampedModel):
    """Governed edition of a curriculum map."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEW = "review", "In review"
        APPROVED = "approved", "Approved"
        PUBLISHED = "published", "Published"
        RETIRED = "retired", "Retired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    curriculum_map = models.ForeignKey(
        CurriculumMap,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version_number = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    change_summary = models.TextField(blank=True, default="")
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="curriculum_versions_submitted",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="curriculum_versions_approved",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    retired_at = models.DateTimeField(null=True, blank=True)

    objects = GovernedManager()

    class Meta:
        db_table = "curriculum_map_version"
        ordering = ["curriculum_map_id", "-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["curriculum_map", "version_number"],
                name="uniq_curriculum_map_version_number",
            ),
            models.UniqueConstraint(
                fields=["curriculum_map"],
                condition=models.Q(status="published"),
                name="uniq_published_curriculum_map_version",
            ),
        ]
        indexes = [
            models.Index(
                fields=["school_id", "curriculum_map", "status"],
                name="curr_ver_school_map_status_idx",
            ),
            models.Index(
                fields=["school_id", "status"],
                name="curr_ver_school_status_idx",
            ),
        ]

    def __str__(self):
        return f"{self.curriculum_map.title} v{self.version_number} [{self.status}]"


class CurriculumMapVersionEvent(models.Model):
    """Append-only governance event for curriculum-map version transitions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    version = models.ForeignKey(
        CurriculumMapVersion,
        on_delete=models.CASCADE,
        related_name="events",
    )
    from_status = models.CharField(max_length=16, blank=True, default="")
    to_status = models.CharField(max_length=16)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="curriculum_version_events",
    )
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = GovernedManager()

    class Meta:
        db_table = "curriculum_map_version_event"
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(
                fields=["school_id", "version", "created_at"],
                name="curr_evt_sch_ver_created",
            )
        ]


class Unit(TimeStampedModel):
    """Major learning module within one governed curriculum-map version."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    curriculum_map = models.ForeignKey(
        CurriculumMap,
        on_delete=models.CASCADE,
        related_name="units",
    )
    curriculum_version = models.ForeignKey(
        CurriculumMapVersion,
        on_delete=models.PROTECT,
        related_name="units",
    )
    sequence = models.IntegerField(default=0, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    overview = models.TextField(blank=True, default="")

    objects = GovernedManager()

    class Meta:
        db_table = "curriculum_unit"
        indexes = [
            models.Index(fields=["school_id", "curriculum_map", "sequence"]),
            models.Index(
                fields=["school_id", "curriculum_version", "sequence"],
                name="curr_unit_school_ver_seq_idx",
            ),
        ]
        ordering = ["curriculum_map", "sequence"]

    def __str__(self):
        return f"Unit {self.sequence}: {self.title}"


class Lesson(TimeStampedModel):
    """Specific teaching module within a governed curriculum unit."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="lessons")
    sequence = models.IntegerField(default=0, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    objectives = models.TextField(blank=True, default="")
    resources = models.TextField(blank=True, default="")

    objects = GovernedManager()

    class Meta:
        db_table = "curriculum_lesson"
        indexes = [models.Index(fields=["school_id", "unit", "sequence"])]
        ordering = ["unit", "sequence"]

    def __str__(self):
        return f"Lesson {self.sequence}: {self.title}"
