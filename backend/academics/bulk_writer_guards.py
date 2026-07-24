from __future__ import annotations

from contextvars import ContextVar
from functools import wraps

from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import models, router, transaction
from django.db.models.signals import pre_save

from .models import (
    Assignment,
    AssignmentCategory,
    Enrollment,
    Section,
    Submission,
    TeacherAssignment,
    Term,
)


AUTHORITY_FIELDS = {
    Term: frozenset({"school_id", "academic_year", "academic_year_id"}),
    Section: frozenset(
        {
            "school_id",
            "course",
            "course_id",
            "term_ref",
            "term_ref_id",
            "teacher",
            "teacher_id",
        }
    ),
    Enrollment: frozenset({"school_id", "section", "section_id", "student", "student_id"}),
    TeacherAssignment: frozenset(
        {"school_id", "section", "section_id", "staff", "staff_id"}
    ),
    AssignmentCategory: frozenset({"school_id", "section", "section_id"}),
    Assignment: frozenset(
        {"school_id", "section", "section_id", "category", "category_id"}
    ),
    Submission: frozenset(
        {"school_id", "assignment", "assignment_id", "enrollment", "enrollment_id"}
    ),
}

_BULK_UPDATE_INTERNAL_WRITE = ContextVar(
    "academics_bulk_update_internal_write", default=False
)


def _authority_fields(model):
    return AUTHORITY_FIELDS.get(model, frozenset())


def _normalize_fields(fields):
    return {getattr(field, "name", str(field)) for field in fields}


def _write_alias(queryset):
    return queryset._db or router.db_for_write(queryset.model)


def _unsafe_queryset_update_fields(model, kwargs):
    """Return authority fields that are not safe lifecycle null-clears.

    Django's deletion collector clears nullable foreign keys with an internal
    QuerySet.update(field=None). That operation removes authority rather than
    assigning new authority, so it is permitted. Any non-null reassignment,
    non-relation authority change, or unknown field remains rejected.
    """

    unsafe = set()
    for name in _authority_fields(model).intersection(kwargs):
        field_name = name[:-3] if name.endswith("_id") else name
        try:
            field = model._meta.get_field(field_name)
        except FieldDoesNotExist:
            unsafe.add(name)
            continue

        if kwargs[name] is None and field.is_relation and field.null:
            continue
        unsafe.add(name)
    return unsafe


def _validate_objects(model, objects, *, using, update_fields=None):
    for obj in objects:
        if not isinstance(obj, model):
            raise TypeError(f"Expected {model.__name__} instance, got {type(obj).__name__}.")
        pre_save.send(
            sender=model,
            instance=obj,
            raw=False,
            using=using,
            update_fields=update_fields,
        )


def install_academics_bulk_writer_guards() -> None:
    if getattr(models.QuerySet.update, "_crown_academics_relational_guard", False):
        return

    original_update = models.QuerySet.update
    original_bulk_create = models.QuerySet.bulk_create
    original_bulk_update = models.QuerySet.bulk_update

    @wraps(original_update)
    def guarded_update(self, **kwargs):
        if _BULK_UPDATE_INTERNAL_WRITE.get():
            return original_update(self, **kwargs)

        touched = _unsafe_queryset_update_fields(self.model, kwargs)
        if touched:
            names = ", ".join(sorted(touched))
            raise ValidationError(
                f"{self.model.__name__} authority fields cannot be changed with "
                f"QuerySet.update(): {names}. Use instance save() or validated bulk_update()."
            )
        return original_update(self, **kwargs)

    @wraps(original_bulk_create)
    def guarded_bulk_create(self, objs, *args, **kwargs):
        object_list = list(objs)
        if self.model not in AUTHORITY_FIELDS or not object_list:
            return original_bulk_create(self, object_list, *args, **kwargs)

        using = _write_alias(self)
        write_queryset = self.using(using)
        with transaction.atomic(using=using):
            _validate_objects(self.model, object_list, using=using)
            return original_bulk_create(write_queryset, object_list, *args, **kwargs)

    @wraps(original_bulk_update)
    def guarded_bulk_update(self, objs, fields, *args, **kwargs):
        object_list = list(objs)
        normalized_fields = _normalize_fields(fields)
        authority = _authority_fields(self.model)
        touched = authority.intersection(normalized_fields)
        if self.model not in AUTHORITY_FIELDS or not touched or not object_list:
            return original_bulk_update(self, object_list, fields, *args, **kwargs)

        primary_keys = [obj.pk for obj in object_list]
        if any(pk is None for pk in primary_keys):
            raise ValueError("All bulk_update() objects must have a primary key set.")

        using = _write_alias(self)
        write_queryset = self.using(using)
        with transaction.atomic(using=using):
            locked_primary_keys = list(
                self.model._base_manager.using(using)
                .select_for_update()
                .filter(pk__in=primary_keys)
                .values_list("pk", flat=True)
            )
            if len(locked_primary_keys) != len(set(primary_keys)):
                raise ValidationError(
                    f"One or more {self.model.__name__} rows do not exist in database {using}."
                )
            _validate_objects(
                self.model,
                object_list,
                using=using,
                update_fields=normalized_fields,
            )
            token = _BULK_UPDATE_INTERNAL_WRITE.set(True)
            try:
                return original_bulk_update(
                    write_queryset, object_list, fields, *args, **kwargs
                )
            finally:
                _BULK_UPDATE_INTERNAL_WRITE.reset(token)

    guarded_update._crown_academics_relational_guard = True
    guarded_bulk_create._crown_academics_relational_guard = True
    guarded_bulk_update._crown_academics_relational_guard = True

    models.QuerySet.update = guarded_update
    models.QuerySet.bulk_create = guarded_bulk_create
    models.QuerySet.bulk_update = guarded_bulk_update
