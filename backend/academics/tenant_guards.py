import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import router, transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver

from core.models import AcademicYear, Staff
from households.models import Student

from .models import (
    Assignment,
    AssignmentCategory,
    Course,
    Enrollment,
    Section,
    Submission,
    TeacherAssignment,
    Term,
)


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


def _projected_authority(instance, update_fields, field_names, using=None):
    """Return the authority values that a partial save would persist."""
    current = {field_name: getattr(instance, field_name) for field_name in field_names}
    if not instance.pk or update_fields is None:
        return current

    model = type(instance)
    try:
        persisted = _manager_for_alias(model._base_manager, using).only(
            *field_names
        ).get(pk=instance.pk)
    except model.DoesNotExist:
        return current

    fields = {str(field) for field in update_fields}
    projected = {}
    for field_name in field_names:
        selected_names = {field_name}
        if field_name.endswith("_id"):
            selected_names.add(field_name[:-3])
        projected[field_name] = (
            current[field_name]
            if _field_selected(fields, *selected_names)
            else getattr(persisted, field_name)
        )
    return projected


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
    return _projected_authority(
        instance,
        update_fields,
        ("school_id", "course_id", "term_ref_id", "teacher_id"),
        using=using,
    )


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
    return _projected_authority(
        instance,
        update_fields,
        ("school_id", "section_id", "student_id"),
        using=using,
    )


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


@receiver(
    pre_save,
    sender=TeacherAssignment,
    dispatch_uid="academics.teacher_assignment.tenant_consistency",
)
def enforce_teacher_assignment_tenant_consistency(
    sender, instance, raw=False, update_fields=None, using=None, **kwargs
):
    if raw:
        return

    authority = _projected_authority(
        instance,
        update_fields,
        ("school_id", "section_id", "staff_id"),
        using=using,
    )
    school_id = _normalized_uuid(authority["school_id"])
    section_id = authority["section_id"]
    staff_id = authority["staff_id"]

    if not section_id:
        raise ValidationError({"section": "Teacher assignment requires a section."})
    if not staff_id:
        raise ValidationError({"staff": "Teacher assignment requires a staff member."})

    try:
        section = _manager_for_alias(
            Section._base_manager, using, lock=True
        ).only("school_id").get(pk=section_id)
    except Section.DoesNotExist as exc:
        raise ValidationError({"section": "Section does not exist."}) from exc

    try:
        staff = _manager_for_alias(
            Staff._base_manager, using, lock=True
        ).only("school_id").get(pk=staff_id)
    except Staff.DoesNotExist as exc:
        raise ValidationError({"staff": "Staff member does not exist."}) from exc

    if school_id != _normalized_uuid(section.school_id):
        raise ValidationError(
            {"section": "Teacher assignment and section must belong to the same school."}
        )
    if school_id != _normalized_uuid(staff.school_id):
        raise ValidationError(
            {"staff": "Teacher assignment and staff must belong to the same school."}
        )


@receiver(
    pre_save,
    sender=AssignmentCategory,
    dispatch_uid="academics.assignment_category.tenant_consistency",
)
def enforce_assignment_category_tenant_consistency(
    sender, instance, raw=False, update_fields=None, using=None, **kwargs
):
    if raw:
        return

    authority = _projected_authority(
        instance,
        update_fields,
        ("school_id", "section_id"),
        using=using,
    )
    school_id = _normalized_uuid(authority["school_id"])
    section_id = authority["section_id"]

    if not section_id:
        raise ValidationError({"section": "Assignment category requires a section."})

    try:
        section = _manager_for_alias(
            Section._base_manager, using, lock=True
        ).only("school_id").get(pk=section_id)
    except Section.DoesNotExist as exc:
        raise ValidationError({"section": "Section does not exist."}) from exc

    if school_id != _normalized_uuid(section.school_id):
        raise ValidationError(
            {"section": "Assignment category and section must belong to the same school."}
        )


@receiver(
    pre_save,
    sender=Assignment,
    dispatch_uid="academics.assignment.tenant_consistency",
)
def enforce_assignment_tenant_consistency(
    sender, instance, raw=False, update_fields=None, using=None, **kwargs
):
    if raw:
        return

    authority = _projected_authority(
        instance,
        update_fields,
        ("school_id", "section_id", "category_id"),
        using=using,
    )
    school_id = _normalized_uuid(authority["school_id"])
    section_id = authority["section_id"]
    category_id = authority["category_id"]

    if not section_id:
        raise ValidationError({"section": "Assignment requires a section."})
    if not category_id:
        raise ValidationError({"category": "Assignment requires a category."})

    # AssignmentCategory saves already hold the category row before locking Section.
    # Acquire the same shared authority rows in that order to avoid deadlocks.
    try:
        category = _manager_for_alias(
            AssignmentCategory._base_manager, using, lock=True
        ).only("school_id", "section_id").get(pk=category_id)
    except AssignmentCategory.DoesNotExist as exc:
        raise ValidationError({"category": "Assignment category does not exist."}) from exc

    try:
        section = _manager_for_alias(
            Section._base_manager, using, lock=True
        ).only("school_id").get(pk=section_id)
    except Section.DoesNotExist as exc:
        raise ValidationError({"section": "Section does not exist."}) from exc

    if school_id != _normalized_uuid(section.school_id):
        raise ValidationError(
            {"section": "Assignment and section must belong to the same school."}
        )
    if school_id != _normalized_uuid(category.school_id):
        raise ValidationError(
            {"category": "Assignment and category must belong to the same school."}
        )
    if _normalized_uuid(category.section_id) != _normalized_uuid(section_id):
        raise ValidationError(
            {"category": "Assignment category must belong to the selected section."}
        )


@receiver(
    pre_save,
    sender=Submission,
    dispatch_uid="academics.submission.tenant_consistency",
)
def enforce_submission_tenant_consistency(
    sender, instance, raw=False, update_fields=None, using=None, **kwargs
):
    if raw:
        return

    authority = _projected_authority(
        instance,
        update_fields,
        ("school_id", "assignment_id", "enrollment_id"),
        using=using,
    )
    school_id = _normalized_uuid(authority["school_id"])
    assignment_id = authority["assignment_id"]
    enrollment_id = authority["enrollment_id"]

    if not assignment_id:
        raise ValidationError({"assignment": "Submission requires an assignment."})
    if not enrollment_id:
        raise ValidationError({"enrollment": "Submission requires an enrollment."})

    try:
        assignment = _manager_for_alias(
            Assignment._base_manager, using, lock=True
        ).only("school_id", "section_id").get(pk=assignment_id)
    except Assignment.DoesNotExist as exc:
        raise ValidationError({"assignment": "Assignment does not exist."}) from exc

    try:
        enrollment = _manager_for_alias(
            Enrollment._base_manager, using, lock=True
        ).only("school_id", "section_id").get(pk=enrollment_id)
    except Enrollment.DoesNotExist as exc:
        raise ValidationError({"enrollment": "Enrollment does not exist."}) from exc

    if school_id != _normalized_uuid(assignment.school_id):
        raise ValidationError(
            {"assignment": "Submission and assignment must belong to the same school."}
        )
    if school_id != _normalized_uuid(enrollment.school_id):
        raise ValidationError(
            {"enrollment": "Submission and enrollment must belong to the same school."}
        )
    if _normalized_uuid(assignment.section_id) != _normalized_uuid(
        enrollment.section_id
    ):
        raise ValidationError(
            {"enrollment": "Submission enrollment must belong to the assignment section."}
        )


def _serialized_save(model, original_save, instance, *args, **kwargs):
    positional_names = ("force_insert", "force_update", "using", "update_fields")
    if len(args) > len(positional_names):
        raise TypeError(
            f"Model.save() takes from 1 to {len(positional_names) + 1} positional arguments "
            f"but {len(args) + 1} were given"
        )
    for name, value in zip(positional_names, args):
        if name in kwargs:
            raise TypeError(f"Model.save() got multiple values for argument '{name}'")
        kwargs[name] = value

    using = kwargs.get("using") or instance._state.db or router.db_for_write(
        model, instance=instance
    )
    kwargs["using"] = using

    with transaction.atomic(using=using):
        if not instance._state.adding:
            try:
                model._base_manager.using(using).select_for_update().only("pk").get(
                    pk=instance.pk
                )
            except model.DoesNotExist:
                pass
        return original_save(instance, **kwargs)


def _install_serialized_save(model):
    if getattr(model.save, "_tenant_serialized", False):
        return

    original_save = model.save

    def serialized_save(instance, *args, **kwargs):
        return _serialized_save(model, original_save, instance, *args, **kwargs)

    serialized_save._tenant_serialized = True
    model.save = serialized_save


for _model in (
    Section,
    Enrollment,
    TeacherAssignment,
    AssignmentCategory,
    Assignment,
    Submission,
):
    _install_serialized_save(_model)
