import uuid
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import models, router

from academics.models import Assignment, Section
from households.models import Student


def _normalized_uuid(value):
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return value


def _require_same_school(instance, relation_name: str, *, using=None):
    """Validate relation ownership against persisted database values."""
    relation_id = getattr(instance, f"{relation_name}_id", None)
    if relation_id is None:
        return None
    model = instance._meta.get_field(relation_name).remote_field.model
    db_alias = using or instance._state.db or router.db_for_write(
        type(instance), instance=instance
    )
    fields = ("school_id", "section_id") if relation_name == "assignment" else ("school_id",)
    related = (
        model._base_manager.db_manager(using=db_alias)
        .filter(pk=relation_id)
        .values(*fields)
        .first()
    )
    if related is None:
        raise ValidationError({relation_name: "Related record does not exist."})
    if _normalized_uuid(instance.school_id) != _normalized_uuid(related["school_id"]):
        raise ValidationError(
            {relation_name: "Related record must belong to the same school."}
        )
    return related


# GradeEntry carries both student records and tenant authority. Instance.save()
# already runs clean(), but Django QuerySet.update()/bulk_create()/bulk_update()
# skip that check unless the manager explicitly guards these paths.
_GRADE_PROTECTED_FIELDS = frozenset({
    "id", "pk", "school_id", "section", "section_id", "student", "student_id",
    "assignment", "assignment_id", "assignment_name",
    "points_earned", "points_possible",
})


class GradeEntryQuerySet(models.QuerySet):
    """Reject unvalidated bulk changes to grade identity and scoring fields."""

    def update(self, **kwargs):
        protected = _GRADE_PROTECTED_FIELDS.intersection(kwargs)
        if protected:
            raise ValidationError(
                "GradeEntry protected fields require validated instance save(): "
                + ", ".join(sorted(protected))
            )
        return super().update(**kwargs)

    def bulk_create(self, objs, *args, **kwargs):
        if kwargs.get("update_conflicts"):
            raise ValidationError(
                "GradeEntry bulk upsert is unsupported; use validated instance writes."
            )
        records = list(objs)
        for record in records:
            if not isinstance(record, self.model):
                raise TypeError("bulk_create expects GradeEntry model instances.")
            record.clean(using=self.db)
        return super().bulk_create(records, *args, **kwargs)

    def bulk_update(self, objs, fields, *args, **kwargs):
        # Django implements bulk_update via QuerySet.update(CASE ...).
        # Reject protected writes before entering that internal path.
        fields = tuple(fields)
        normalized_fields = {
            getattr(field, "name", field) for field in fields
        }
        protected = _GRADE_PROTECTED_FIELDS.intersection(normalized_fields)
        if protected:
            raise ValidationError(
                "GradeEntry protected fields require validated instance save(): "
                + ", ".join(sorted(protected))
            )
        return super().bulk_update(objs, fields, *args, **kwargs)


class GradeEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objects = GradeEntryQuerySet.as_manager()

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

    def clean(self, *, using=None):
        super().clean()
        _require_same_school(self, "section", using=using)
        _require_same_school(self, "student", using=using)
        assignment_row = _require_same_school(self, "assignment", using=using)
        if assignment_row and _normalized_uuid(
            assignment_row["section_id"]
        ) != _normalized_uuid(self.section_id):
            raise ValidationError(
                {"assignment": "Assignment must belong to the selected section."}
            )
        for name in ("points_earned", "points_possible"):
            raw_value = getattr(self, name)
            if raw_value is None:
                continue
            try:
                number = Decimal(str(raw_value))
            except (InvalidOperation, ValueError, TypeError) as exc:
                raise ValidationError(
                    {name: "Grade points must be finite nonnegative numbers."}
                ) from exc
            if not number.is_finite() or number < 0:
                raise ValidationError(
                    {name: "Grade points must be finite nonnegative numbers."}
                )

    def save(self, *args, **kwargs):
        self.clean(using=kwargs.get("using"))
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"GradeEntry({self.section_id} {self.student_id} {self.assignment_name})"
