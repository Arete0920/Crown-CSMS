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
    from .experience_access import is_leader, taught_sections
    if is_leader(user, school_id):
        return True
    staff = getattr(user, 'staff', None)
    return bool(staff and staff.school_id == school_id and staff.status == 'ACTIVE'
                and _roles(user, school_id) & {'TEACHER', 'teacher'}
                and taught_sections(user, school_id).filter(id=section.id).exists())


def _serialize(assignment: Assignment) -> dict:
    return {
        **{key: getattr(assignment, key) for key in ("purpose", "instructions", "success_criteria", "home_support")},
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
    if not points.is_finite() or points <= 0 or points > Decimal("99999.99") or points.as_tuple().exponent < -2:
        raise ValidationError("points_possible must be greater than 0")
    return points


def _optional_date(value, field_name):
    if value in (None, ""):
        return None
    if hasattr(value, "isoformat") and not isinstance(value, str):
        return value
    try:
        parsed = parse_date(str(value))
    except ValueError:
        parsed = None
    if parsed is None:
        raise ValidationError(f"{field_name} must be a valid ISO date (YYYY-MM-DD)")
    return parsed


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def assignment_list_create(request, section_id):
    school_id = get_request_school_id(request)
    section = get_object_or_404(Section, id=section_id, school_id=school_id)

    if request.method == "GET":
        from .experience_access import accessible_enrollments
        manager = _can_manage_section(request.user, school_id, section)
        if not manager and not accessible_enrollments(request.user, school_id).filter(section=section).exists():
            raise PermissionDenied("No relationship to this classroom.")
        assignments = (
            Assignment.objects.filter(section=section, school_id=school_id)
            .select_related("category")
            .order_by("category__sort_order", "due_date", "name")
        )
        if not manager:
            assignments = assignments.filter(is_published=True)
        return Response({"assignments": [_serialize(row) for row in assignments]})

    if not _can_manage_section(request.user, school_id, section):
        raise PermissionDenied("Only school leaders or teachers assigned to this section can create assignments")

    name = str(request.data.get("name") or "").strip()
    if not name or len(name) > 120:
        raise ValidationError("name is required and must be at most 120 characters")
    category_id = request.data.get("category_id")
    if not category_id:
        raise ValidationError("category_id is required")
    category = get_object_or_404(
        AssignmentCategory,
        id=category_id,
        section=section,
        school_id=school_id,
    )
    details = _details(request.data)
    if Assignment.objects.filter(section=section, name=name).exists():
        raise ValidationError("An assignment with this name already exists in the section.")
    assignment = Assignment.objects.create(
        **details,
        school_id=school_id,
        section=section,
        category=category,
        name=name,
        points_possible=_positive_points(request.data.get("points_possible", "0")),
        due_date=_optional_date(request.data.get("due_date"), "due_date"),
        assigned_date=_optional_date(request.data.get("assigned_date"), "assigned_date"),
        is_published=_published(request.data.get("is_published", True)),
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
        if assignment.submissions.exists() or assignment.grade_entries.exists():
            return Response({"detail": "Assignment has student evidence and cannot be deleted."}, status=409)
        assignment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    if "name" in request.data:
        name = str(request.data.get("name") or "").strip()
        if not name:
            raise ValidationError("name cannot be empty")
        assignment.name = name
    if "points_possible" in request.data:
        points = _positive_points(request.data.get("points_possible"))
        if points != assignment.points_possible and (assignment.submissions.filter(submitted_at__isnull=False).exists() or assignment.grade_entries.filter(points_earned__isnull=False).exists()):
            return Response({'detail': 'Recorded student evidence fixes possible points. Reuse as a new assignment to change the denominator.'}, status=409)
        assignment.points_possible = points
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
        assignment.is_published = _published(request.data.get("is_published"))
    for key, value in _details(request.data).items():
        setattr(assignment, key, value)
    assignment.save()
    return Response(_serialize(assignment))


def _details(payload):
    result = {}
    for key in ("purpose", "instructions", "success_criteria", "home_support"):
        if key in payload:
            value = payload[key]
            if not isinstance(value, str) or len(value) > 20000:
                raise ValidationError(f"{key} must be text of at most 20000 characters.")
            result[key] = value
    return result


def _published(value):
    if not isinstance(value, bool):
        raise ValidationError("is_published must be true or false.")
    return value


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assignment_copy(request, assignment_id):
    from django.db import transaction
    school_id = get_request_school_id(request)
    source = get_object_or_404(Assignment, id=assignment_id, school_id=school_id)
    if not _can_manage_section(request.user, school_id, source.section):
        raise PermissionDenied('Source section access required.')
    targets = request.data.get('targets')
    name = request.data.get('name', source.name)
    if not isinstance(name, str) or not name.strip() or len(name) > 120:
        raise ValidationError('A name of at most 120 characters is required.')
    if not isinstance(targets, list) or not 1 <= len(targets) <= 20:
        raise ValidationError('Choose 1 to 20 target sections.')
    prepared, seen = [], set()
    for target in targets:
        if not isinstance(target, dict):
            raise ValidationError('Each target must be an object.')
        from .submission_workflow_views import _uuid
        section = get_object_or_404(Section, id=_uuid(target.get('section_id'), 'section_id'), school_id=school_id)
        if section.id in seen or not _can_manage_section(request.user, school_id, section):
            raise PermissionDenied('Each target must be unique and authorized.')
        seen.add(section.id)
        category = get_object_or_404(AssignmentCategory, id=_uuid(target.get('category_id'), 'category_id'),
                                     section=section, school_id=school_id, is_active=True)
        due = _optional_date(target.get('due_date', source.due_date), 'due_date')
        prepared.append((section, category, due))
    with transaction.atomic():
        for section, _, _ in prepared:
            Section.objects.select_for_update().get(id=section.id)
            if Assignment.objects.filter(section=section, name=name.strip()).exists():
                raise ValidationError('An assignment with this name already exists in a target section.')
        copies = [Assignment.objects.create(school_id=school_id, section=section, category=category,
                    name=name.strip(), due_date=due, points_possible=source.points_possible,
                    purpose=source.purpose, instructions=source.instructions,
                    success_criteria=source.success_criteria, home_support=source.home_support,
                    classroom_rubric=source.classroom_rubric, is_published=False) for section, category, due in prepared]
    return Response({'assignments': [_serialize(a) for a in copies]}, status=201)
