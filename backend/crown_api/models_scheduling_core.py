from django.db import models

from core.models import BaseModel
from crown_api.models_academics_core import Course
from crown_api.models_households import Person, Student


class Term(BaseModel):
    code = models.CharField(max_length=16, unique=True, db_index=True)
    name = models.CharField(max_length=64)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date", "code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}".strip()


class Section(BaseModel):
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    section_code = models.CharField(max_length=16)
    name_override = models.CharField(max_length=128, blank=True, default="")
    teacher = models.ForeignKey(
        Person,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="teaching_sections",
    )
    room = models.CharField(max_length=32, blank=True, default="")
    meeting_days = models.CharField(max_length=16, blank=True, default="")
    meeting_time = models.CharField(max_length=32, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["term", "course", "section_code"],
                name="uniq_term_course_section_code",
            )
        ]
        ordering = ["term__code", "course__course_code", "section_code"]

    def __str__(self) -> str:
        label = self.name_override or f"{self.course.course_code} {self.section_code}"
        return f"{self.term.code} - {label}".strip()


class SectionEnrollment(BaseModel):
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="roster",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="section_enrollments",
    )
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["section", "student"],
                name="uniq_section_enrollment_section_student",
            )
        ]
        ordering = ["section", "student__person__last_name"]

    def __str__(self) -> str:
        return f"{self.student} -> {self.section}".strip()
