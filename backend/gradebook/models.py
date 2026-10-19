import uuid

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models

from academics.models import Assignment, Section
from households.models import Student


def _normalized_uuid(value):
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return value


def _require_same_school(instance, relation_name: str) -> None:
    relation_id = getattr(instance, f"{relation_name}_id", None)
    if relation_id is None:
        return
    try:
        related = getattr(instance, relation_name)
    except ObjectDoesNotExist as exc:
        raise ValidationError(
            {relation_name: "Related record does not exist."}
        ) from exc
    if _normalized_uuid(instance.school_id) != _normalized_uuid(related.school_id):
        raise ValidationError(
            {relation_name: "Related record must belong to the same school."}
        )


class GradeEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="grade_entries",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="grade_entries",
    )
    assignment = models.ForeignKey(
        Assignment,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="grade_entries",
    )

    assignment_name = models.CharField(max_length=255)
    points_earned = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    points_possible = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

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

    def clean(self):
        super().clean()
        _require_same_school(self, "section")
        _require_same_school(self, "student")
        _require_same_school(self, "assignment")
        if self.assignment_id and _normalized_uuid(
            self.assignment.section_id
        ) != _normalized_uuid(self.section_id):
            raise ValidationError(
                {"assignment": "Assignment must belong to the selected section."}
            )

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"GradeEntry({self.section_id} {self.student_id} {self.assignment_name})"
