"""Curriculum-map governance services and model integrity guards."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import CurriculumMap, CurriculumMapVersion, CurriculumMapVersionEvent, Lesson, Unit


_VERSION_TRANSITION_WRITE = ContextVar("curriculum_version_transition_write", default=False)

TRANSITIONS = {
    CurriculumMapVersion.Status.DRAFT: {CurriculumMapVersion.Status.REVIEW},
    CurriculumMapVersion.Status.REVIEW: {
        CurriculumMapVersion.Status.DRAFT,
        CurriculumMapVersion.Status.APPROVED,
    },
    CurriculumMapVersion.Status.APPROVED: {CurriculumMapVersion.Status.PUBLISHED},
    CurriculumMapVersion.Status.PUBLISHED: {CurriculumMapVersion.Status.RETIRED},
    CurriculumMapVersion.Status.RETIRED: set(),
}


@contextmanager
def _allow_version_transition_write():
    token = _VERSION_TRANSITION_WRITE.set(True)
    try:
        yield
    finally:
        _VERSION_TRANSITION_WRITE.reset(token)


def _norm(value):
    return str(value) if value is not None else None


def _draft_version(version_id, using=None):
    manager = CurriculumMapVersion._base_manager.using(using) if using else CurriculumMapVersion._base_manager
    try:
        version = manager.get(pk=version_id)
    except CurriculumMapVersion.DoesNotExist as exc:
        raise ValidationError({"curriculum_version": "Curriculum version does not exist."}) from exc
    if version.status != CurriculumMapVersion.Status.DRAFT:
        raise ValidationError(
            {"curriculum_version": "Only draft curriculum versions may be authored. Clone to create a new draft."}
        )
    return version


@receiver(pre_save, sender=CurriculumMap, dispatch_uid="curricula.map.integrity")
def validate_curriculum_map(sender, instance, raw=False, using=None, **kwargs):
    if raw:
        return
    if instance.course_id:
        course_school = getattr(instance.course, "school_id", None)
        if _norm(course_school) != _norm(instance.school_id):
            raise ValidationError({"course": "Curriculum map course must belong to the same school."})

    if instance.pk:
        manager = CurriculumMap._base_manager.using(using) if using else CurriculumMap._base_manager
        persisted = manager.filter(pk=instance.pk).first()
        if persisted and persisted.versions.exists():
            if _norm(persisted.school_id) != _norm(instance.school_id):
                raise ValidationError({"school_id": "Versioned curriculum-map school cannot be changed."})
            if _norm(persisted.course_id) != _norm(instance.course_id):
                raise ValidationError({"course": "Versioned curriculum-map course cannot be changed."})
            if persisted.active and not instance.active and persisted.versions.filter(status=CurriculumMapVersion.Status.PUBLISHED).exists():
                raise ValidationError({"active": "Retire the published curriculum version before deactivating the map."})


@receiver(pre_save, sender=CurriculumMapVersion, dispatch_uid="curricula.version.integrity")
def validate_curriculum_version(sender, instance, raw=False, using=None, **kwargs):
    if raw:
        return
    if not instance.curriculum_map_id:
        raise ValidationError({"curriculum_map": "Curriculum version requires a curriculum map."})
    if _norm(instance.curriculum_map.school_id) != _norm(instance.school_id):
        raise ValidationError({"school_id": "Curriculum version and map must belong to the same school."})
    if instance.effective_from and instance.effective_to and instance.effective_to < instance.effective_from:
        raise ValidationError({"effective_to": "Effective-to date cannot precede effective-from date."})

    if instance.pk:
        manager = CurriculumMapVersion._base_manager.using(using) if using else CurriculumMapVersion._base_manager
        persisted = manager.filter(pk=instance.pk).first()
        if persisted:
            if _norm(persisted.school_id) != _norm(instance.school_id):
                raise ValidationError({"school_id": "Curriculum version school is immutable."})
            if _norm(persisted.curriculum_map_id) != _norm(instance.curriculum_map_id):
                raise ValidationError({"curriculum_map": "Curriculum version map is immutable."})
            if persisted.version_number != instance.version_number:
                raise ValidationError({"version_number": "Curriculum version number is immutable."})
            if persisted.status != instance.status and not _VERSION_TRANSITION_WRITE.get():
                raise ValidationError({"status": "Curriculum version status must change through the governance transition service."})


@receiver(pre_delete, sender=CurriculumMapVersion, dispatch_uid="curricula.version.no_delete")
def prevent_version_delete(sender, instance, **kwargs):
    raise ValidationError("Curriculum-map versions are governance records and cannot be deleted; retire them instead.")


@receiver(pre_save, sender=CurriculumMapVersionEvent, dispatch_uid="curricula.event.append_only")
def validate_version_event(sender, instance, raw=False, using=None, **kwargs):
    if raw:
        return
    if instance.pk:
        manager = CurriculumMapVersionEvent._base_manager.using(using) if using else CurriculumMapVersionEvent._base_manager
        if manager.filter(pk=instance.pk).exists():
            raise ValidationError("Curriculum governance events are append-only and cannot be edited.")
    if not instance.version_id:
        raise ValidationError({"version": "Governance event requires a curriculum version."})
    if _norm(instance.version.school_id) != _norm(instance.school_id):
        raise ValidationError({"school_id": "Governance event and version must belong to the same school."})
    if instance.to_status not in CurriculumMapVersion.Status.values:
        raise ValidationError({"to_status": "Invalid curriculum version status."})
    if instance.from_status and instance.from_status not in CurriculumMapVersion.Status.values:
        raise ValidationError({"from_status": "Invalid curriculum version status."})


@receiver(pre_delete, sender=CurriculumMapVersionEvent, dispatch_uid="curricula.event.no_delete")
def prevent_event_delete(sender, instance, **kwargs):
    raise ValidationError("Curriculum governance events are append-only and cannot be deleted.")


@receiver(pre_save, sender=Unit, dispatch_uid="curricula.unit.integrity")
def validate_curriculum_unit(sender, instance, raw=False, using=None, **kwargs):
    if raw:
        return
    if not instance.curriculum_map_id or not instance.curriculum_version_id:
        raise ValidationError("Curriculum unit requires a map and version.")
    version = _draft_version(instance.curriculum_version_id, using=using)
    if _norm(instance.school_id) != _norm(instance.curriculum_map.school_id):
        raise ValidationError({"school_id": "Curriculum unit and map must belong to the same school."})
    if _norm(instance.school_id) != _norm(version.school_id):
        raise ValidationError({"school_id": "Curriculum unit and version must belong to the same school."})
    if _norm(instance.curriculum_map_id) != _norm(version.curriculum_map_id):
        raise ValidationError({"curriculum_version": "Curriculum version must belong to the unit curriculum map."})

    if instance.pk:
        manager = Unit._base_manager.using(using) if using else Unit._base_manager
        persisted = manager.filter(pk=instance.pk).first()
        if persisted:
            for field in ("school_id", "curriculum_map_id", "curriculum_version_id"):
                if _norm(getattr(persisted, field)) != _norm(getattr(instance, field)):
                    raise ValidationError({field: "Curriculum unit ownership/version fields are immutable."})


@receiver(pre_delete, sender=Unit, dispatch_uid="curricula.unit.delete_draft_only")
def validate_curriculum_unit_delete(sender, instance, using=None, **kwargs):
    _draft_version(instance.curriculum_version_id, using=using)


@receiver(pre_save, sender=Lesson, dispatch_uid="curricula.lesson.integrity")
def validate_curriculum_lesson(sender, instance, raw=False, using=None, **kwargs):
    if raw:
        return
    if not instance.unit_id:
        raise ValidationError({"unit": "Curriculum lesson requires a unit."})
    unit = instance.unit
    _draft_version(unit.curriculum_version_id, using=using)
    if _norm(instance.school_id) != _norm(unit.school_id):
        raise ValidationError({"school_id": "Curriculum lesson and unit must belong to the same school."})

    if instance.pk:
        manager = Lesson._base_manager.using(using) if using else Lesson._base_manager
        persisted = manager.filter(pk=instance.pk).first()
        if persisted:
            if _norm(persisted.school_id) != _norm(instance.school_id):
                raise ValidationError({"school_id": "Curriculum lesson school is immutable."})
            if _norm(persisted.unit_id) != _norm(instance.unit_id):
                raise ValidationError({"unit": "Curriculum lesson unit is immutable."})


@receiver(pre_delete, sender=Lesson, dispatch_uid="curricula.lesson.delete_draft_only")
def validate_curriculum_lesson_delete(sender, instance, using=None, **kwargs):
    _draft_version(instance.unit.curriculum_version_id, using=using)


@receiver(pre_delete, sender=CurriculumMap, dispatch_uid="curricula.map.no_versioned_delete")
def prevent_versioned_map_delete(sender, instance, **kwargs):
    if instance.versions.exists():
        raise ValidationError("Versioned curriculum maps cannot be deleted; deactivate the map and retire versions.")


def create_new_draft(*, curriculum_map: CurriculumMap, actor=None, change_summary=""):
    with transaction.atomic():
        locked_map = CurriculumMap._base_manager.select_for_update().get(pk=curriculum_map.pk)
        latest = (
            CurriculumMapVersion._base_manager.filter(curriculum_map=locked_map)
            .aggregate(max_version=Max("version_number"))["max_version"]
            or 0
        )
        version = CurriculumMapVersion.objects.create(
            school_id=locked_map.school_id,
            curriculum_map=locked_map,
            version_number=latest + 1,
            status=CurriculumMapVersion.Status.DRAFT,
            change_summary=change_summary or ("Initial curriculum-map draft" if latest == 0 else f"Draft version {latest + 1}"),
        )
        CurriculumMapVersionEvent.objects.create(
            school_id=locked_map.school_id,
            version=version,
            to_status=CurriculumMapVersion.Status.DRAFT,
            actor=actor,
            notes="Draft created.",
        )
        return version


def transition_version(*, version: CurriculumMapVersion, target_status: str, actor, notes=""):
    if target_status not in CurriculumMapVersion.Status.values:
        raise ValidationError({"status": "Invalid curriculum version status."})

    with transaction.atomic():
        locked = CurriculumMapVersion._base_manager.select_for_update().select_related("curriculum_map").get(pk=version.pk)
        source = locked.status
        if target_status not in TRANSITIONS[source]:
            raise ValidationError({"status": f"Transition {source} -> {target_status} is not permitted."})

        now = timezone.now()
        if target_status == CurriculumMapVersion.Status.DRAFT:
            locked.submitted_by = None
            locked.submitted_at = None
            locked.approved_by = None
            locked.approved_at = None
            locked.published_at = None
        elif target_status == CurriculumMapVersion.Status.REVIEW:
            locked.submitted_by = actor
            locked.submitted_at = now
            locked.approved_by = None
            locked.approved_at = None
        elif target_status == CurriculumMapVersion.Status.APPROVED:
            if locked.submitted_by_id == getattr(actor, "id", None):
                raise ValidationError({"status": "The submitter cannot approve the same curriculum version."})
            if locked.submitted_by_id is None:
                raise ValidationError({"status": "Curriculum version must be submitted for review before approval."})
            locked.approved_by = actor
            locked.approved_at = now
        elif target_status == CurriculumMapVersion.Status.PUBLISHED:
            if locked.approved_by_id is None:
                raise ValidationError({"status": "Only an approved curriculum version can be published."})
            current = (
                CurriculumMapVersion._base_manager.select_for_update()
                .filter(curriculum_map_id=locked.curriculum_map_id, status=CurriculumMapVersion.Status.PUBLISHED)
                .exclude(pk=locked.pk)
                .first()
            )
            if current:
                old_status = current.status
                current.status = CurriculumMapVersion.Status.RETIRED
                current.retired_at = now
                with _allow_version_transition_write():
                    current.save(update_fields=["status", "retired_at", "updated_at"])
                CurriculumMapVersionEvent.objects.create(
                    school_id=current.school_id,
                    version=current,
                    from_status=old_status,
                    to_status=CurriculumMapVersion.Status.RETIRED,
                    actor=actor,
                    notes=f"Retired automatically when version {locked.version_number} was published.",
                )
            locked.published_at = now
            locked.retired_at = None
        elif target_status == CurriculumMapVersion.Status.RETIRED:
            locked.retired_at = now

        locked.status = target_status
        with _allow_version_transition_write():
            locked.save()
        CurriculumMapVersionEvent.objects.create(
            school_id=locked.school_id,
            version=locked,
            from_status=source,
            to_status=target_status,
            actor=actor,
            notes=notes,
        )
        return locked


def clone_version(*, source: CurriculumMapVersion, actor=None, change_summary=""):
    with transaction.atomic():
        locked_source = (
            CurriculumMapVersion._base_manager.select_for_update()
            .select_related("curriculum_map")
            .get(pk=source.pk)
        )
        curriculum_map = CurriculumMap._base_manager.select_for_update().get(pk=locked_source.curriculum_map_id)
        latest = (
            CurriculumMapVersion._base_manager.filter(curriculum_map=curriculum_map)
            .aggregate(max_version=Max("version_number"))["max_version"]
            or 0
        )
        clone = CurriculumMapVersion.objects.create(
            school_id=locked_source.school_id,
            curriculum_map=curriculum_map,
            version_number=latest + 1,
            status=CurriculumMapVersion.Status.DRAFT,
            change_summary=change_summary or f"Cloned from version {locked_source.version_number}",
        )

        source_units = (
            Unit._base_manager.filter(curriculum_version=locked_source)
            .prefetch_related("lessons")
            .order_by("sequence", "id")
        )
        for source_unit in source_units:
            cloned_unit = Unit.objects.create(
                school_id=clone.school_id,
                curriculum_map=curriculum_map,
                curriculum_version=clone,
                sequence=source_unit.sequence,
                title=source_unit.title,
                description=source_unit.description,
                overview=source_unit.overview,
            )
            for source_lesson in source_unit.lessons.all():
                Lesson.objects.create(
                    school_id=clone.school_id,
                    unit=cloned_unit,
                    sequence=source_lesson.sequence,
                    title=source_lesson.title,
                    description=source_lesson.description,
                    objectives=source_lesson.objectives,
                    resources=source_lesson.resources,
                )

        CurriculumMapVersionEvent.objects.create(
            school_id=clone.school_id,
            version=clone,
            to_status=CurriculumMapVersion.Status.DRAFT,
            actor=actor,
            notes=f"Cloned from version {locked_source.version_number} ({locked_source.id}).",
        )
        return clone
