import uuid
from django.db import models
from households.models import Student


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Course(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)

    code = models.CharField(max_length=32, db_index=True)
    name = models.CharField(max_length=160)

    class Meta:
        db_table = "course"
        indexes = [
            models.Index(fields=["school_id", "code"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class Section(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)

    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="sections")

    # spine: keep term as string (e.g., "2026-FALL")
    term = models.CharField(max_length=24, db_index=True)

    # optional teacher reference (string for now; real Staff model comes later)
    teacher_name = models.CharField(max_length=120, blank=True, default="")

    # optional grade band (string for now)
    grade_band = models.CharField(max_length=32, blank=True, default="")

    class Meta:
        db_table = "section"
        indexes = [
            models.Index(fields=["school_id", "term"]),
            models.Index(fields=["school_id", "course"]),
        ]

    def __str__(self) -> str:
        return f"Section({self.course.code} {self.term})"


class Enrollment(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)

    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="enrollments")

    class Meta:
        db_table = "enrollment"
        constraints = [
            models.UniqueConstraint(fields=["section", "student"], name="uniq_section_student"),
        ]
        indexes = [
            models.Index(fields=["school_id", "section"]),
            models.Index(fields=["school_id", "student"]),
        ]

    def __str__(self) -> str:
        return f"Enrollment({self.student_id} -> {self.section_id})"
