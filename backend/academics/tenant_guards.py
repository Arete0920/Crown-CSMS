import uuid

from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver

from core.models import AcademicYear

from .models import Term


def _normalized_uuid(value):
    if value in (None, ""):
        return value
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return value


@receiver(pre_save, sender=Term, dispatch_uid="academics.term.tenant_consistency")
def enforce_term_academic_year_tenant(sender, instance, raw=False, update_fields=None, **kwargs):
    if raw:
        return

    if not instance.academic_year_id:
        raise ValidationError({"academic_year": "Term requires an academic year."})

    try:
        academic_year = AcademicYear._base_manager.only("school_id").get(
            pk=instance.academic_year_id
        )
    except AcademicYear.DoesNotExist as exc:
        raise ValidationError({"academic_year": "Academic year does not exist."}) from exc

    if _normalized_uuid(instance.school_id) != _normalized_uuid(academic_year.school_id):
        raise ValidationError(
            {"academic_year": "Term and academic year must belong to the same school."}
        )

    if instance.pk and update_fields is not None:
        normalized_fields = {str(field) for field in update_fields}
        relationship_fields = {"school_id", "academic_year", "academic_year_id"}
        relationship_update = normalized_fields & relationship_fields
        has_school = "school_id" in normalized_fields
        has_academic_year = bool(
            {"academic_year", "academic_year_id"} & normalized_fields
        )
        if relationship_update and not (has_school and has_academic_year):
            raise ValidationError(
                "Term school and academic year must be updated together."
            )
