import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import router, transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver

from core.models import AcademicYear
from households.models import Student

from .models import Course, Enrollment, Section, Term


def _normalized_uuid(value):
    if value in (None, ""):
        return value
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return value


def _field_selected(fields, *names):
    return bool(fields.intersection(names))


def _manager_for_alias(manager, using, *, lock=False):
    queryset = manager.using(using) if using else manager
    return queryset.select_for_update() if lock else queryset


@receiver(pre_save, sender=Term, dispatch_uid="academics.term.tenant_consistency")
def enforce_term_academic_year_tenant(
    sender, instance, raw=False, update_fields=None, using=None, **kwargs
):
    if raw:
        return

    if not instance.academic_year_id:
        raise ValidationError({"academic_year": "Term requires an academic year."})

    try:
        academic_year = _manager_for_alias(
            AcademicYear._base_manager, using
        ).only("school_id").get(pk=instance.academic_year_id)
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


def _projected_section_authority(instance, update_fields, using=None):
    current = {
        "school_id": instance.school_id,
        "course_id": instance.course_id,
        "term_ref_id": instance.term_ref_id,
        "teacher_id": instance.teacher_id,
    }
    if not instance.pk or update_fields is None:
        return current

    try:
        persisted = _manager_for_alias(
            Section._base_manager, using
        ).only("school_id", "course_id", "term_ref_id", "teacher_id").get(
            pk=instance.pk
        )
    except Section.DoesNotExist:
        return current

    fields = {str(field) for field in update_fields}
    return {
        "school_id": (
            instance.school_id if "school_id" in fields else persisted.school_id
        ),
        "course_id": (
            instance.course_id
            if _field_selected(fields, "course", "course_id")
            else persisted.course_id
        ),
        "term_ref_id": (
            instance.term_ref_id
            if _field_selected(fields, "term_ref", "term_ref_id")
            else persisted.term_ref_id
        ),
        "teacher_id": (
            instance.teacher_id
            if _field_selected(fields, "teacher", "teacher_id")
            else persisted.teacher_id
        ),
    }


@receiver(pre_save, sender=Section, dispatch_uid="academics.section.tenant_consistency")
def enforce_section_tenant_consistency(
    sender, instance, raw=False, update_fields=None, using=None, **kwargs
):
    if raw:
        return

    authority = _projected_section_authority(instance, update_fields, using=using)
    school_id = _normalized_uuid(authority["school_id"])
    course_id = authority["course_id"]
    term_ref_id = authority["term_ref_id"]
    teacher_id = authority["teacher_id"]

    if not course_id:
        raise ValidationError({"course": "Section requires a course."})

    try:
        course = _manager_for_alias(
            Course._base_manager, using, lock=True
        ).only("school_id").get(pk=course_id)
    except Course.DoesNotExist as exc:
        raise ValidationError({"course": "Course does not exist."}) from exc

    if school_id != _normalized_uuid(course.school_id):
        raise ValidationError(
            {"course": "Section and course must belong to the same school."}
        )

    if term_ref_id:
        try:
            term = _manager_for_alias(
                Term._base_manager, using, lock=True
            ).only("school_id").get(pk=term_ref_id)
        except Term.DoesNotExist as exc:
            raise ValidationError({"term_ref": "Term does not exist."}) from exc
        if school_id != _normalized_uuid(term.school_id):
            raise ValidationError(
                {"term_ref": "Section and term must belong to the same school."}
            )

    if teacher_id:
        User = get_user_model()
        try:
            teacher = _manager_for_alias(
                User._base_manager, using, lock=True
            ).only("school_id").get(pk=teacher_id)
        except User.DoesNotExist as exc:
            raise ValidationError({"teacher": "Teacher does not exist."}) from exc
        if not teacher.school_id:
            raise ValidationError(
                {"teacher": "Section teacher must belong to a school."}
            )
        if school_id != _normalized_uuid(teacher.school_id):
            raise ValidationError(
                {"teacher": "Section and teacher must belong to the same school."}
            )


def _projected_enrollment_authority(instance, update_fields, using=None):
    current = {
        "school_id": instance.school_id,
        "section_id": instance.section_id,
        "student_id": instance.student_id,
    }
    if not instance.pk or update_fields is None:
        return current

    try:
        persisted = _manager_for_alias(
            Enrollment._base_manager, using
        ).only("school_id", "section_id", "student_id").get(pk=instance.pk)
    except Enrollment.DoesNotExist:
        return current

    fields = {str(field) for field in update_fields}
    return {
        "school_id": (
            instance.school_id if "school_id" in fields else persisted.school_id
        ),
        "section_id": (
            instance.section_id
            if _field_selected(fields, "section", "section_id")
            else persisted.section_id
        ),
        "student_id": (
            instance.student_id
            if _field_selected(fields, "student", "student_id")
            else persisted.student_id
        ),
    }


@receiver(
    pre_save,
    sender=Enrollment,
    dispatch_uid="academics.enrollment.tenant_consistency",
)
def enforce_enrollment_tenant_consistency(
    sender, instance, raw=False, update_fields=None, using=None, **kwargs
):
    if raw:
        return

    authority = _projected_enrollment_authority(instance, update_fields, using=using)
    school_id = _normalized_uuid(authority["school_id"])
    section_id = authority["section_id"]
    student_id = authority["student_id"]

    if not section_id:
        raise ValidationError({"section": "Enrollment requires a section."})
    if not student_id:
        raise ValidationError({"student": "Enrollment requires a student."})

    try:
        section = _manager_for_alias(
            Section._base_manager, using, lock=True
        ).only("school_id").get(pk=section_id)
    except Section.DoesNotExist as exc:
        raise ValidationError({"section": "Section does not exist."}) from exc

    try:
        student = _manager_for_alias(
            Student._base_manager, using, lock=True
        ).only("school_id").get(pk=student_id)
    except Student.DoesNotExist as exc:
        raise ValidationError({"student": "Student does not exist."}) from exc

    if school_id != _normalized_uuid(section.school_id):
        raise ValidationError(
            {"section": "Enrollment and section must belong to the same school."}
        )
    if school_id != _normalized_uuid(student.school_id):
        raise ValidationError(
            {"student": "Enrollment and student must belong to the same school."}
        )


def _serialized_save(model, original_save, instance, *args, **kwargs):
    positional_using = args[2] if len(args) >= 3 else None
    using = kwargs.get("using") or positional_using or instance._state.db or router.db_for_write(
        model, instance=instance
    )
    if len(args) >= 3 and positional_using is None:
        normalized_args = list(args)
        normalized_args[2] = using
        args = tuple(normalized_args)
    elif len(args) < 3:
        kwargs["using"] = using

    with transaction.atomic(using=using):
        if not instance._state.adding:
            try:
                model._base_manager.using(using).select_for_update().only("pk").get(
                    pk=instance.pk
                )
            except model.DoesNotExist:
                pass
        return original_save(instance, *args, **kwargs)


_original_section_save = Section.save


def _serialized_section_save(instance, *args, **kwargs):
    """Serialize Section validation, authority reads, and persistence atomically."""
    return _serialized_save(Section, _original_section_save, instance, *args, **kwargs)


if not getattr(Section.save, "_tenant_serialized", False):
    _serialized_section_save._tenant_serialized = True
    Section.save = _serialized_section_save


_original_enrollment_save = Enrollment.save


def _serialized_enrollment_save(instance, *args, **kwargs):
    """Serialize Enrollment validation, authority reads, and persistence atomically."""
    return _serialized_save(
        Enrollment, _original_enrollment_save, instance, *args, **kwargs
    )


if not getattr(Enrollment.save, "_tenant_serialized", False):
    _serialized_enrollment_save._tenant_serialized = True
    Enrollment.save = _serialized_enrollment_save
