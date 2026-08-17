"""Tenant-scoped API for durable lesson execution evidence."""

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id

from .lesson_execution_models import LessonPlanLesson
from .models import LessonPlan, Section, TeacherAssignment


def _staff_for_user(user):
    try:
        return user.staff
    except (AttributeError, ObjectDoesNotExist):
        return None


def _can_write_section(user, school_id, section: Section) -> bool:
    """Require persistent academic-write authority plus section/admin scope."""
    if not getattr(user, "is_authenticated", False):
        return False
    school = School.objects.filter(pk=school_id).first()
    if school is None or not user_has_permission(user, "academics.edit", school=school):
        return False

    # Broad academic authorities remain permission-driven rather than role-name driven.
    if user_has_permission(user, "admin.view", school=school) or user_has_permission(
        user, "registrar.view", school=school
    ):
        return True

    # Ordinary instructional authority is object-scoped and revalidated on every request.
    if getattr(section, "teacher_id", None) and str(section.teacher_id) == str(user.id):
        return True

    staff = _staff_for_user(user)
    if staff is None:
        return False
    return TeacherAssignment.objects.filter(
        school_id=school_id,
        section_id=section.id,
        staff=staff,
    ).exists()


def _payload(link: LessonPlanLesson) -> dict:
    return {
        "link_id": str(link.id),
        "school_id": str(link.school_id),
        "plan_id": str(link.lesson_plan_id),
        "lesson_id": str(link.lesson_id),
        "sequence_order": link.sequence_order,
        "delivery_status": link.delivery_status,
        "planned_minutes": link.planned_minutes,
        "actual_minutes": link.actual_minutes,
        "actual_started_at": link.actual_started_at,
        "actual_completed_at": link.actual_completed_at,
        "completion_notes": link.completion_notes,
        "created_at": link.created_at,
        "updated_at": link.updated_at,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def lesson_plan_execution_list(request, plan_id):
    school_id = get_request_school_id(request)
    plan = get_object_or_404(
        LessonPlan.objects.select_related("section"),
        id=plan_id,
        school_id=school_id,
    )
    if not _can_write_section(request.user, school_id, plan.section):
        return Response(
            {"detail": "Lesson execution evidence requires persistent academic write authority for this section."},
            status=status.HTTP_403_FORBIDDEN,
        )
    links = LessonPlanLesson.objects.filter(
        school_id=school_id,
        lesson_plan=plan,
    ).select_related("lesson").order_by("sequence_order", "id")
    return Response([_payload(link) for link in links])


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def lesson_plan_execution_detail(request, link_id):
    school_id = get_request_school_id(request)
    link = get_object_or_404(
        LessonPlanLesson.objects.select_related("lesson_plan__section", "lesson"),
        id=link_id,
        school_id=school_id,
    )
    if not _can_write_section(request.user, school_id, link.lesson_plan.section):
        return Response(
            {"detail": "Lesson execution evidence requires persistent academic write authority for this section."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == "GET":
        return Response(_payload(link))

    allowed_statuses = {choice for choice, _ in LessonPlanLesson.DeliveryStatus.choices}
    delivery_status = request.data.get("delivery_status")
    if delivery_status is not None and delivery_status not in allowed_statuses:
        return Response(
            {"delivery_status": f"Must be one of: {', '.join(sorted(allowed_statuses))}."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    parsed_minutes = {}
    for field in ("planned_minutes", "actual_minutes"):
        if field not in request.data:
            continue
        value = request.data.get(field)
        if value is None or value == "":
            parsed_minutes[field] = None
            continue
        try:
            value = int(value)
        except (TypeError, ValueError):
            return Response({field: "Must be a non-negative integer or null."}, status=status.HTTP_400_BAD_REQUEST)
        if value < 0:
            return Response({field: "Must be a non-negative integer or null."}, status=status.HTTP_400_BAD_REQUEST)
        parsed_minutes[field] = value

    parsed_datetimes = {}
    for field in ("actual_started_at", "actual_completed_at"):
        if field not in request.data:
            continue
        raw = request.data.get(field)
        if raw in (None, ""):
            parsed_datetimes[field] = None
            continue
        parsed = parse_datetime(str(raw))
        if parsed is None or timezone.is_naive(parsed):
            return Response(
                {field: "Must be a timezone-aware ISO-8601 datetime or null."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        parsed_datetimes[field] = parsed

    with transaction.atomic():
        link = LessonPlanLesson.objects.select_for_update().select_related("lesson_plan__section").get(
            id=link.id,
            school_id=school_id,
        )
        # Revalidate section authority after taking the row lock.
        if not _can_write_section(request.user, school_id, link.lesson_plan.section):
            return Response(
                {"detail": "Lesson execution authority was revoked before the write completed."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if delivery_status is not None:
            link.delivery_status = delivery_status
        for field, value in parsed_minutes.items():
            setattr(link, field, value)
        for field, value in parsed_datetimes.items():
            setattr(link, field, value)
        if "completion_notes" in request.data:
            link.completion_notes = str(request.data.get("completion_notes") or "")
        try:
            link.save()
        except Exception as exc:
            # DRF ValidationError from the model signal is returned as a normal 400.
            from rest_framework.exceptions import ValidationError

            if isinstance(exc, ValidationError):
                return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
            raise

    return Response(_payload(link))
