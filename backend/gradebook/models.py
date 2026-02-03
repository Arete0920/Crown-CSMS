import uuid
from django.db import models
from academics.models import Section
from households.models import Student


class GradeEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="grade_entries")
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="grade_entries")

    assignment_name = models.CharField(max_length=255)
    points_earned = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    points_possible = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "grade_entry"
        constraints = [
            models.UniqueConstraint(
                fields=["section", "student", "assignment_name"],
                name="uniq_grade_entry_section_student_assignment",
            )
        ]
        indexes = [
            models.Index(fields=["school_id", "section"]),
            models.Index(fields=["school_id", "student"]),
        ]

    def __str__(self) -> str:
        return f"GradeEntry({self.section_id} {self.student_id} {self.assignment_name})"
