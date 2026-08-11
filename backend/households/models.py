import uuid

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models


class TimeStampedModel(models.Model):
    """Local lightweight base with fail-closed model validation on writes."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not kwargs.get("raw", False):
            self.clean()
        return super().save(*args, **kwargs)


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
    if instance.school_id != related.school_id:
        raise ValidationError(
            {relation_name: "Related record must belong to the same school."}
        )


class Household(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=160)
    address1 = models.CharField(max_length=160, blank=True, default="")
    address2 = models.CharField(max_length=160, blank=True, default="")
    city = models.CharField(max_length=80, blank=True, default="")
    state = models.CharField(max_length=40, blank=True, default="")
    postal_code = models.CharField(max_length=20, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "household"
        indexes = [
            models.Index(fields=["school_id", "is_active"]),
            models.Index(fields=["school_id", "name"]),
        ]

    def __str__(self) -> str:
        return self.name


class Guardian(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="guardians",
    )
    account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="households_guardian",
        null=True,
        blank=True,
        help_text="Canonical authenticated account for Parent360 access. Email is not authorization.",
    )
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "guardian"
        indexes = [
            models.Index(fields=["school_id", "household"]),
            models.Index(fields=["school_id", "last_name", "first_name"]),
        ]

    def clean(self):
        super().clean()
        _require_same_school(self, "household")
        _require_same_school(self, "account")

    def __str__(self) -> str:
        return f"{self.last_name}, {self.first_name}"


class Student(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    household = models.ForeignKey(
        Household,
        on_delete=models.PROTECT,
        related_name="students",
    )
    account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="households_student",
        null=True,
        blank=True,
        help_text="Canonical authenticated account for Student self-service. Email is not authorization.",
    )
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    grade_level = models.CharField(max_length=16, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "student"
        indexes = [
            models.Index(fields=["school_id", "is_active"]),
            models.Index(fields=["school_id", "last_name", "first_name"]),
            models.Index(fields=["school_id", "grade_level"]),
        ]

    def clean(self):
        super().clean()
        _require_same_school(self, "household")
        _require_same_school(self, "account")

    def __str__(self) -> str:
        return f"{self.last_name}, {self.first_name}"
