"""Integrity guards and synchronization for instructional execution evidence."""

from uuid import UUID

from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from rest_framework.exceptions import ValidationError

from .lesson_execution_models import LessonPlanLesson
from .models import Lesson, LessonPlan, Section


def _normalized(value):
    return str(value) if value is not None else None


def _ordered_plan_lessons(instance: LessonPlan, using=None):
    raw_ids = instance.lesson_ids or []
    if not isinstance(raw_ids, list):
        raise ValidationError({"lesson_ids": "lesson_ids must be a list of lesson UUID strings."})

    normalized_ids = []
    for raw_id in raw_ids:
        try:
            normalized_ids.append(UUID(str(raw_id)))
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValidationError({"lesson_ids": "Each lesson_id must be a valid UUID."}) from exc

    if not normalized_ids:
        return []

    section_manager = Section._base_manager.using(using) if using else Section._base_manager
    lesson_manager = Lesson._base_manager.using(using) if using else Lesson._base_manager
    try:
        section = section_manager.get(pk=instance.section_id)
    except Section.DoesNotExist as exc:
        raise ValidationError({"section": "Lesson plan section does not exist."}) from exc

    lessons = lesson_manager.filter(
        id__in=normalized_ids,
        school_id=instance.school_id,
        unit__course_id=section.course_id,
    )
    by_id = {lesson.id: lesson for lesson in lessons}
    missing = [str(lesson_id) for lesson_id in normalized_ids if lesson_id not in by_id]
    if missing:
        raise ValidationError(
            {
                "lesson_ids": "All lesson_ids must belong to lessons in this section course and school.",
                "invalid_lesson_ids": missing,
            }
        )

    ordered = []
    seen = set()
    for lesson_id in normalized_ids:
        if lesson_id not in seen:
            ordered.append(by_id[lesson_id])
            seen.add(lesson_id)
    return ordered


@receiver(pre_save, sender=LessonPlan, dispatch_uid="academics.lesson_plan.execution_links.validate")
def validate_lesson_plan_execution_links(sender, instance: LessonPlan, raw=False, using=None, **kwargs) -> None:
    if raw:
        return
    if not instance.section_id:
        raise ValidationError({"section": "Lesson plan requires a section."})
    _ordered_plan_lessons(instance, using=using)


@receiver(post_save, sender=LessonPlan, dispatch_uid="academics.lesson_plan.execution_links.sync")
def synchronize_lesson_plan_execution_links(sender, instance: LessonPlan, raw=False, using=None, **kwargs) -> None:
    if raw:
        return
    lessons = _ordered_plan_lessons(instance, using=using)
    manager = LessonPlanLesson.objects.using(using) if using else LessonPlanLesson.objects
    requested_ids = [lesson.id for lesson in lessons]

    manager.filter(
        lesson_plan_id=instance.id,
        school_id=instance.school_id,
    ).exclude(lesson_id__in=requested_ids).delete()

    for sequence, lesson in enumerate(lessons, start=1):
        link, _ = manager.get_or_create(
            school_id=instance.school_id,
            lesson_plan_id=instance.id,
            lesson_id=lesson.id,
            defaults={"sequence_order": sequence},
        )
        if link.sequence_order != sequence:
            link.sequence_order = sequence
            link.save(update_fields=["sequence_order", "updated_at"])


def _validate_evidence_history(instance: LessonPlanLesson, manager) -> None:
    """Prevent already-recorded instruction from being silently erased."""
    if not instance.pk:
        return

    persisted = manager.filter(pk=instance.pk).first()
    if persisted is None:
        return

    if (
        persisted.delivery_status != LessonPlanLesson.DeliveryStatus.PLANNED
        and instance.delivery_status == LessonPlanLesson.DeliveryStatus.PLANNED
    ):
        raise ValidationError(
            {"delivery_status": "Recorded instructional delivery cannot be reverted to planned."}
        )

    for field in ("actual_minutes", "actual_started_at", "actual_completed_at"):
        if getattr(persisted, field) is not None and getattr(instance, field) is None:
            raise ValidationError({field: "Recorded instructional evidence cannot be cleared."})

    if (persisted.completion_notes or "").strip() and not (instance.completion_notes or "").strip():
        raise ValidationError({"completion_notes": "Recorded instructional evidence cannot be cleared."})


def _validate_execution_timestamps(instance: LessonPlanLesson) -> None:
    if instance.actual_started_at is None or instance.actual_completed_at is None:
        return
    try:
        invalid_order = instance.actual_completed_at < instance.actual_started_at
    except TypeError as exc:
        raise ValidationError(
            {"actual_completed_at": "Start and completion timestamps must use compatible timezone formats."}
        ) from exc
    if invalid_order:
        raise ValidationError(
            {"actual_completed_at": "Completion timestamp cannot precede the start timestamp."}
        )


@receiver(pre_save, sender=LessonPlanLesson, dispatch_uid="academics.lesson_execution.tenant_consistency")
def enforce_lesson_execution_integrity(
    sender,
    instance: LessonPlanLesson,
    raw=False,
    using=None,
    **kwargs,
) -> None:
    """Require tenant/course consistency and preserve recorded execution history."""
    if raw:
        return
    if not instance.lesson_plan_id:
        raise ValidationError({"lesson_plan": "Lesson execution requires a lesson plan."})
    if not instance.lesson_id:
        raise ValidationError({"lesson": "Lesson execution requires a lesson."})

    plan_manager = LessonPlan._base_manager.using(using) if using else LessonPlan._base_manager
    lesson_manager = Lesson._base_manager.using(using) if using else Lesson._base_manager
    link_manager = LessonPlanLesson._base_manager.using(using) if using else LessonPlanLesson._base_manager

    try:
        plan = plan_manager.select_related("section").get(pk=instance.lesson_plan_id)
    except LessonPlan.DoesNotExist as exc:
        raise ValidationError({"lesson_plan": "Lesson plan does not exist."}) from exc

    try:
        lesson = lesson_manager.select_related("unit").get(pk=instance.lesson_id)
    except Lesson.DoesNotExist as exc:
        raise ValidationError({"lesson": "Lesson does not exist."}) from exc

    if _normalized(instance.school_id) != _normalized(plan.school_id):
        raise ValidationError({"school_id": "Execution record and lesson plan must belong to the same school."})
    if _normalized(instance.school_id) != _normalized(lesson.school_id):
        raise ValidationError({"lesson": "Execution record and lesson must belong to the same school."})
    if _normalized(plan.section.course_id) != _normalized(lesson.unit.course_id):
        raise ValidationError({"lesson": "Execution lesson must belong to the lesson plan section course."})

    _validate_execution_timestamps(instance)
    _validate_evidence_history(instance, link_manager)


@receiver(pre_delete, sender=LessonPlanLesson, dispatch_uid="academics.protect_lesson_execution_evidence")
def protect_lesson_execution_evidence(sender, instance: LessonPlanLesson, **kwargs) -> None:
    """Block ordinary deletion once a scheduled lesson contains execution evidence."""
    has_evidence = (
        instance.delivery_status != LessonPlanLesson.DeliveryStatus.PLANNED
        or instance.actual_minutes is not None
        or instance.actual_started_at is not None
        or instance.actual_completed_at is not None
        or bool((instance.completion_notes or "").strip())
    )
    if has_evidence:
        raise ValidationError(
            {
                "lesson_ids": (
                    "This lesson has recorded instructional execution evidence and cannot be removed "
                    "from the plan. Preserve the execution record and use delivery_status to document "
                    "the instructional outcome."
                )
            }
        )
