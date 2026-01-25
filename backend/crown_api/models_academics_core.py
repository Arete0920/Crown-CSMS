from django.db import models

from core.models import BaseModel
from crown_api.models_households import Student


class Course(BaseModel):
    course_code = models.CharField(max_length=32, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    term = models.CharField(max_length=32, blank=True, default="")
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["course_code"]

    def __str__(self) -> str:
        return f"{self.course_code} - {self.name}".strip()


class CourseEnrollment(BaseModel):
    STATUS_ENROLLED = "ENROLLED"
    STATUS_DROPPED = "DROPPED"

    STATUS_CHOICES = [
        (STATUS_ENROLLED, "Enrolled"),
        (STATUS_DROPPED, "Dropped"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="course_enrollments",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ENROLLED)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="uniq_course_enrollment_student_course",
            )
        ]
        ordering = ["course__course_code", "student__person__last_name"]

    def __str__(self) -> str:
        return f"{self.student} -> {self.course} ({self.status})"


class AttendanceRecord(BaseModel):
    STATUS_PRESENT = "PRESENT"
    STATUS_ABSENT = "ABSENT"
    STATUS_TARDY = "TARDY"
    STATUS_EXCUSED = "EXCUSED"

    STATUS_CHOICES = [
        (STATUS_PRESENT, "Present"),
        (STATUS_ABSENT, "Absent"),
        (STATUS_TARDY, "Tardy"),
        (STATUS_EXCUSED, "Excused"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_records",
    )
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PRESENT)
    minutes_late = models.PositiveSmallIntegerField(null=True, blank=True)
    notes_public = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course", "date"],
                name="uniq_attendance_student_course_date",
            )
        ]
        ordering = ["-date", "course__course_code"]

    def __str__(self) -> str:
        course_part = self.course.course_code if self.course_id else "(no course)"
        return f"{self.student} {self.date} {course_part} {self.status}".strip()


class GradeRecord(BaseModel):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="grade_records",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grade_records",
    )

    period = models.CharField(max_length=32, blank=True, default="")
    assignment_name = models.CharField(max_length=255, blank=True, default="")
    category = models.CharField(max_length=64, blank=True, default="")

    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    score_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    letter_grade = models.CharField(max_length=8, blank=True, default="")

    posted_at = models.DateTimeField(null=True, blank=True)
    notes_public = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-posted_at", "course__course_code", "assignment_name"]

    def __str__(self) -> str:
        course_part = self.course.course_code if self.course_id else "(no course)"
        label = self.assignment_name or self.period or "grade"
        return f"{self.student} {course_part} {label}".strip()
