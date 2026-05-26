"""
Lesson Plan API views.

Endpoints:
    GET  /api/v1/academics/sections/<section_id>/lesson-plans/
         ?date=YYYY-MM-DD  ? single plan (or 404)
         ?date_from=&date_to=  ? range of plans
    POST /api/v1/academics/sections/<section_id>/lesson-plans/  (upsert by section+date)
    GET  /api/v1/academics/lesson-plans/<plan_id>/
    PATCH/PUT  /api/v1/academics/lesson-plans/<plan_id>/

Lesson Resource endpoints:
    GET  /api/v1/academics/lessons/<lesson_id>/resources/
    POST /api/v1/academics/lessons/<lesson_id>/resources/
    DELETE /api/v1/academics/lesson-resources/<resource_id>/

Permissions:
    - GET (plans without teacher_notes): any authenticated user in school
    - GET (with teacher_notes_private): staff / teachers of section
    - POST/PATCH/PUT: staff or teacher of section (ADMIN/DIRECTOR role)
    - DELETE resources: staff only
"""
from __future__ import annotations

from uuid import UUID

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import UserRole
from households.scoping import get_request_school_id

from .models import Lesson, LessonPlan, LessonResource, Section, TeacherAssignment
from .serializers import (
    LessonPlanPublicSerializer,
    LessonPlanSerializer,
    LessonResourceSerializer,
)


# ---------------------------------------------------------------------------
# Permission helpers
# ---------------------------------------------------------------------------

def _can_write(user, school_id, section: Section | None = None) -> bool:
    """Write access: superuser, ADMIN/DIRECTOR, or assigned TEACHER for the section."""
    if getattr(user, "is_superuser", False):
        return True
    if not getattr(user, "is_authenticated", False):
        return False
    roles = set(
        UserRole.objects.filter(user_id=user.id, school_id=school_id).values_list("role_code", flat=True)
    )
    if "ADMIN" in roles or "DIRECTOR" in roles:
        return True

    if section is None or "TEACHER" not in roles:
        return False

    # Primary teacher link on section.
    if getattr(section, "teacher_id", None) and str(section.teacher_id) == str(user.id):
        return True

    # Assignment-based fallback for sections using TeacherAssignment records.
    staff = getattr(user, "staff", None)
    if staff is not None:
        return TeacherAssignment.objects.filter(
            school_id=school_id,
            section=section,
            staff=staff,
        ).exists()

    return False


def _can_read_private(user, school_id) -> bool:
    """Teacher notes visibility: staff / admin / director."""
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return True
    if not getattr(user, "is_authenticated", False):
        return False
    roles = set(
        UserRole.objects.filter(user_id=user.id, school_id=school_id).values_list("role_code", flat=True)
    )
    return bool(roles)


def _validate_lesson_ids_for_section(*, school_id, section, lesson_ids):
    """Ensure lesson_ids are UUIDs that belong to the same school and section course."""
    if lesson_ids is None:
        return
    if not isinstance(lesson_ids, list):
        raise ValidationError({"lesson_ids": "lesson_ids must be a list of lesson UUID strings."})
    if not lesson_ids:
        return

    normalized_ids = []
    for raw_id in lesson_ids:
        try:
            normalized_ids.append(UUID(str(raw_id)))
        except (TypeError, ValueError):
            raise ValidationError({"lesson_ids": "Each lesson_id must be a valid UUID."})

    lessons = Lesson.objects.filter(
        id__in=normalized_ids,
        school_id=school_id,
        unit__course_id=section.course_id,
    )
    found_ids = {lesson.id for lesson in lessons}
    missing = [str(lesson_id) for lesson_id in normalized_ids if lesson_id not in found_ids]
    if missing:
        raise ValidationError(
            {
                "lesson_ids": "All lesson_ids must belong to lessons in this section course and school.",
                "invalid_lesson_ids": missing,
            }
        )


# ---------------------------------------------------------------------------
# Lesson Plan endpoints
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def lesson_plan_list_create(request, section_id):
    """
    GET  - list plans for a section; optional ?date=YYYY-MM-DD or ?date_from=&date_to=
    POST - upsert (create or update) plan identified by section + plan_date
    """
    school_id = get_request_school_id(request)
    section = get_object_or_404(Section, id=section_id, school_id=school_id)

    if request.method == "GET":
        qs = LessonPlan.objects.filter(section=section, school_id=school_id)

        single_date = request.query_params.get("date")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        if single_date:
            qs = qs.filter(plan_date=single_date)
        if date_from:
            qs = qs.filter(plan_date__gte=date_from)
        if date_to:
            qs = qs.filter(plan_date__lte=date_to)

        qs = qs.order_by("plan_date")

        include_private = _can_read_private(request.user, school_id)
        ser_class = LessonPlanSerializer if include_private else LessonPlanPublicSerializer
        return Response(ser_class(qs, many=True).data)

    if not _can_write(request.user, school_id, section):
        return Response(
            {"detail": "Write access requires ADMIN, DIRECTOR, or assigned TEACHER role."},
            status=status.HTTP_403_FORBIDDEN,
        )

    plan_date = request.data.get("plan_date")
    if not plan_date:
        return Response({"detail": "plan_date is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        _validate_lesson_ids_for_section(
            school_id=school_id,
            section=section,
            lesson_ids=request.data.get("lesson_ids"),
        )
    except ValidationError as exc:
        return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        plan, created = LessonPlan.objects.select_for_update().get_or_create(
            school_id=school_id,
            section=section,
            plan_date=plan_date,
            defaults={"created_by": request.user, "updated_by": request.user},
        )
        editable_fields = ["lesson_ids", "objectives", "materials", "activities", "homework", "teacher_notes_private"]
        for field in editable_fields:
            if field in request.data:
                setattr(plan, field, request.data[field])
        plan.updated_by = request.user
        plan.save()

    return Response(LessonPlanSerializer(plan).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(["GET", "PATCH", "PUT"])
@permission_classes([IsAuthenticated])
def lesson_plan_detail(request, plan_id):
    """
    GET   - retrieve a single lesson plan
    PATCH/PUT - update fields
    """
    school_id = get_request_school_id(request)
    plan = get_object_or_404(LessonPlan, id=plan_id, school_id=school_id)

    if request.method == "GET":
        include_private = _can_read_private(request.user, school_id)
        ser_class = LessonPlanSerializer if include_private else LessonPlanPublicSerializer
        return Response(ser_class(plan).data)

    if not _can_write(request.user, school_id, plan.section):
        return Response(
            {"detail": "Write access requires ADMIN, DIRECTOR, or assigned TEACHER role."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        _validate_lesson_ids_for_section(
            school_id=school_id,
            section=plan.section,
            lesson_ids=request.data.get("lesson_ids"),
        )
    except ValidationError as exc:
        return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

    editable_fields = ["lesson_ids", "objectives", "materials", "activities", "homework", "teacher_notes_private", "plan_date"]
    with transaction.atomic():
        for field in editable_fields:
            if field in request.data:
                setattr(plan, field, request.data[field])
        plan.updated_by = request.user
        plan.save()

    return Response(LessonPlanSerializer(plan).data)


# ---------------------------------------------------------------------------
# Lesson Resource endpoints
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def lesson_resource_list_create(request, lesson_id):
    """
    GET  - list resources for a lesson (tenant-scoped)
    POST - add a resource to a lesson
    """
    school_id = get_request_school_id(request)
    lesson = get_object_or_404(Lesson, id=lesson_id, school_id=school_id)

    if request.method == "GET":
        resources = LessonResource.objects.filter(lesson=lesson, school_id=school_id).order_by("id")
        return Response(LessonResourceSerializer(resources, many=True).data)

    if not _can_write(request.user, school_id):
        return Response({"detail": "Write access requires ADMIN or DIRECTOR role."}, status=status.HTTP_403_FORBIDDEN)

    title = request.data.get("title", "").strip()
    if not title:
        return Response({"detail": "title is required."}, status=status.HTTP_400_BAD_REQUEST)

    resource = LessonResource.objects.create(
        school_id=school_id,
        lesson=lesson,
        title=title,
        kind=request.data.get("kind", LessonResource.KIND_LINK),
        url=request.data.get("url", ""),
        file_ref=request.data.get("file_ref", ""),
    )
    return Response(LessonResourceSerializer(resource).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def lesson_resource_detail(request, resource_id):
    """
    GET    - retrieve a single resource
    PATCH  - update title/kind/url/file_ref
    DELETE - remove resource (staff only)
    """
    school_id = get_request_school_id(request)
    resource = get_object_or_404(LessonResource, id=resource_id, school_id=school_id)

    if request.method == "GET":
        return Response(LessonResourceSerializer(resource).data)

    if not _can_write(request.user, school_id):
        return Response({"detail": "Write access requires ADMIN or DIRECTOR role."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "DELETE":
        resource.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    for field in ["title", "kind", "url", "file_ref"]:
        if field in request.data:
            setattr(resource, field, request.data[field])
    resource.save()
    return Response(LessonResourceSerializer(resource).data)

