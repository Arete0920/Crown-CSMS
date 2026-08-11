from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import UserRole
from households.scoping import get_request_school_id

from .models import Assignment, AssignmentCategory, Section, TeacherAssignment


def _roles(user, school_id) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    return set(
        UserRole.objects.filter(user=user, school_id=school_id).values_list("role_code", flat=True)
    )


def _can_manage_section(user, school_id, section: Section) -> bool:
    if getattr(user, "is_superuser", False):
        return True
    roles = _roles(user, school_id)
    if "ADMIN" in roles or "DIRECTOR" in roles:
        return True
    if "TEACHER" not in roles:
        return False
    staff = getattr(user, "staff", None)
    if staff is None:
        return False
    return bool(
        str(section.teacher_id or "") == str(user.id)
        or TeacherAssignment.objects.filter(
            school_id=school_id,
            section=section,
            staff=staff,
        ).exists()
    )


def _serialize(assignment: Assignment) -> dict:
    return {
        "id": str(assignment.id),
        "name": assignment.name,
        "category_id": str(assignment.category_id),
        "category_name": assignment.category.name,
        "points_possible": f"{assignment.points_possible:.2f}",
        "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
        "assigned_date": assignment.assigned_date.isoformat() if assignment.assigned_date else None,
        "is_published": assignment.is_published,
        "created_at": assignment.created_at.isoformat(),
        "updated_at": assignment.updated_at.isoformat(),
    }


def _positive_points(value) -> Decimal:
    try:
        points = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError("points_possible must be a valid number")
    if not points.is_finite() or points <= 0:
        raise ValidationError("points_possible must be greater than 0")
    return points


def _optional_date(value, field_name):
    if value in (None, ""):
        return None
    if hasattr(value, "isoformat") and not isinstance(value, str):
        return value
    parsed = parse_date(str(value))
    if parsed is None:
        raise ValidationError(f"{field_name} must be a valid ISO date (YYYY-MM-DD)")
    return parsed


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def assignment_list_create(request, section_id):
    school_id = get_request_school_id(request)
    section = get_object_or_404(Section, id=section_id, school_id=school_id)

    if request.method == "GET":
        assignments = (
            Assignment.objects.filter(section=section, school_id=school_id)
            .select_related("category")
            .order_by("category__sort_order", "due_date", "name")
        )
        return Response({"assignments": [_serialize(row) for row in assignments]})

    if not _can_manage_section(request.user, school_id, section):
        raise PermissionDenied("Only school leaders or teachers assigned to this section can create assignments")

    name = str(request.data.get("name") or "").strip()
    if not name:
        raise ValidationError("name is required")
    category_id = request.data.get("category_id")
    if not category_id:
        raise ValidationError("category_id is required")
    category = get_object_or_404(
        AssignmentCategory,
        id=category_id,
        section=section,
        school_id=school_id,
    )
    assignment = Assignment.objects.create(
        school_id=school_id,
        section=section,
        category=category,
        name=name,
        points_possible=_positive_points(request.data.get("points_possible", "0")),
        due_date=_optional_date(request.data.get("due_date"), "due_date"),
        assigned_date=_optional_date(request.data.get("assigned_date"), "assigned_date"),
        is_published=bool(request.data.get("is_published", True)),
    )
    return Response(_serialize(assignment), status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def assignment_update_delete(request, assignment_id):
    school_id = get_request_school_id(request)
    assignment = get_object_or_404(
        Assignment.objects.select_related("section", "category"),
        id=assignment_id,
        school_id=school_id,
    )
    if not _can_manage_section(request.user, school_id, assignment.section):
        raise PermissionDenied("Only school leaders or teachers assigned to this section can modify assignments")

    if request.method == "DELETE":
        assignment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    if "name" in request.data:
        name = str(request.data.get("name") or "").strip()
        if not name:
            raise ValidationError("name cannot be empty")
        assignment.name = name
    if "points_possible" in request.data:
        assignment.points_possible = _positive_points(request.data.get("points_possible"))
    if "category_id" in request.data:
        assignment.category = get_object_or_404(
            AssignmentCategory,
            id=request.data.get("category_id"),
            section=assignment.section,
            school_id=school_id,
        )
    if "due_date" in request.data:
        assignment.due_date = _optional_date(request.data.get("due_date"), "due_date")
    if "assigned_date" in request.data:
        assignment.assigned_date = _optional_date(request.data.get("assigned_date"), "assigned_date")
    if "is_published" in request.data:
        assignment.is_published = bool(request.data.get("is_published"))
    assignment.save()
    return Response(_serialize(assignment))
