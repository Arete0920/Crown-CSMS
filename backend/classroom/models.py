import uuid
from django.db import models
from django.utils import timezone


class Classroom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="classrooms")

    # Simple "homeroom/class" concept (not the full master schedule section model)
    name = models.CharField(max_length=120)  # e.g., "9th Grade Homeroom", "English 9 - Section A"
    room = models.CharField(max_length=40, blank=True, default="")  # e.g., "B201"
    grade_level = models.CharField(max_length=20, blank=True, default="")  # e.g., "9"

    homeroom_teacher = models.ForeignKey(
        "core.Staff",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="homerooms",
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "is_active", "created_at"]),
        ]
        unique_together = [("school", "name")]

    def __str__(self) -> str:
        return f"{self.school_id} | {self.name}"


class ClassroomEnrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey("core.Student", on_delete=models.CASCADE, related_name="classroom_enrollments")

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("classroom", "student")]
        indexes = [
            models.Index(fields=["classroom", "student"]),
        ]


class ClassroomAnnouncement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="announcements")

    title = models.CharField(max_length=160)
    body = models.TextField(blank=True, default="")
    pinned = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["classroom", "-created_at"]),
        ]


class ClassroomAssignment(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="assignments")

    title = models.CharField(max_length=160)
    description = models.TextField(blank=True, default="")

    due_date = models.DateField(null=True, blank=True)
    points = models.PositiveIntegerField(default=100)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PUBLISHED)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["classroom", "status", "-created_at"]),
        ]


class ClassroomSeatingChart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    classroom = models.OneToOneField(Classroom, on_delete=models.CASCADE, related_name="seating_chart")

    # JSON layout schema:
    # { "rows": 5, "cols": 6, "seats": [{"r":0,"c":0,"student_id":"..."} ...] }
    layout = models.JSONField(default=dict)

    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["classroom"]),
        ]
