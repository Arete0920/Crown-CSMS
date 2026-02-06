"""
API views for AssignmentCategory and Assignment CRUD operations.

Endpoints:
- GET/POST /api/v1/academics/sections/<section_id>/categories/
- PATCH/DELETE /api/v1/academics/categories/<category_id>/
- GET/POST /api/v1/academics/sections/<section_id>/assignments/
- PATCH/DELETE /api/v1/academics/assignments/<assignment_id>/

Permissions:
- Read: Any authenticated user in school
- Write: Users with ADMIN or DIRECTOR role
"""
from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from core.models import UserRole
from households.scoping import get_request_school_id

from .models import Assignment, AssignmentCategory, Section


def _role_codes(user, school_id) -> set[str]:
    """Get role codes for user in school."""
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    return set(
        UserRole.objects.filter(user=user, school_id=school_id).values_list("role_code", flat=True)
    )


def _can_write(user, school_id) -> bool:
    """Check if user has write permissions (ADMIN or DIRECTOR role)."""
    if getattr(user, "is_superuser", False):
        return True
    roles = _role_codes(user, school_id)
    return "ADMIN" in roles or "DIRECTOR" in roles


def _validate_category_weights(section_id, school_id, exclude_category_id=None):
    """
    Validate that active category weights sum to 0 or 100.
    
    Args:
        section_id: UUID of section
        school_id: UUID of school
        exclude_category_id: Optional UUID to exclude from sum (for updates)
    
    Raises:
        ValidationError if sum is not 0 or 100
    """
    qs = AssignmentCategory.objects.filter(
        section_id=section_id,
        school_id=school_id,
        is_active=True
    )
    if exclude_category_id:
        qs = qs.exclude(id=exclude_category_id)
    
    total = qs.aggregate(total=Sum("weight_percent"))["total"] or Decimal("0")
    
    if total not in (Decimal("0"), Decimal("100")):
        raise ValidationError(
            f"Active category weights must sum to 0 (unconfigured) or 100 (configured). Current sum: {total}"
        )


# ========== AssignmentCategory Endpoints ==========

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def category_list_create(request, section_id):
    """
    GET: List all categories for a section
    POST: Create a new category (requires write permissions)
    """
    school_id = get_request_school_id(request)
    section = get_object_or_404(Section, id=section_id, school_id=school_id)
    
    if request.method == "GET":
        categories = AssignmentCategory.objects.filter(
            section_id=section_id,
            school_id=school_id
        ).order_by("sort_order", "name")
        
        data = [
            {
                "id": str(cat.id),
                "name": cat.name,
                "weight_percent": str(cat.weight_percent),
                "sort_order": cat.sort_order,
                "is_active": cat.is_active,
                "created_at": cat.created_at.isoformat(),
                "updated_at": cat.updated_at.isoformat(),
            }
            for cat in categories
        ]
        return Response({"categories": data})
    
    # POST
    if not _can_write(request.user, school_id):
        raise PermissionDenied("Only ADMIN or DIRECTOR can create categories")
    
    name = request.data.get("name", "").strip()
    if not name:
        raise ValidationError("name is required")
    
    try:
        weight_percent = Decimal(str(request.data.get("weight_percent", "0")))
    except (ValueError, TypeError):
        raise ValidationError("weight_percent must be a valid number")
    
    if weight_percent < 0 or weight_percent > 100:
        raise ValidationError("weight_percent must be between 0 and 100")
    
    sort_order = request.data.get("sort_order", 0)
    is_active = request.data.get("is_active", True)
    
    with transaction.atomic():
        category = AssignmentCategory.objects.create(
            school_id=school_id,
            section=section,
            name=name,
            weight_percent=weight_percent,
            sort_order=sort_order,
            is_active=is_active,
        )
        
        # Validate weights after creation
        _validate_category_weights(section_id, school_id)
    
    return Response(
        {
            "id": str(category.id),
            "name": category.name,
            "weight_percent": str(category.weight_percent),
            "sort_order": category.sort_order,
            "is_active": category.is_active,
            "created_at": category.created_at.isoformat(),
            "updated_at": category.updated_at.isoformat(),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def category_update_delete(request, category_id):
    """
    PATCH: Update a category
    DELETE: Delete a category (requires write permissions)
    """
    school_id = get_request_school_id(request)
    
    if not _can_write(request.user, school_id):
        raise PermissionDenied("Only ADMIN or DIRECTOR can modify categories")
    
    category = get_object_or_404(AssignmentCategory, id=category_id, school_id=school_id)
    
    if request.method == "DELETE":
        # Check if category has assignments
        if category.assignments.exists():
            raise ValidationError("Cannot delete category with existing assignments")
        
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    # PATCH
    with transaction.atomic():
        if "name" in request.data:
            name = request.data["name"].strip()
            if not name:
                raise ValidationError("name cannot be empty")
            category.name = name
        
        if "weight_percent" in request.data:
            try:
                weight_percent = Decimal(str(request.data["weight_percent"]))
            except (ValueError, TypeError):
                raise ValidationError("weight_percent must be a valid number")
            
            if weight_percent < 0 or weight_percent > 100:
                raise ValidationError("weight_percent must be between 0 and 100")
            
            category.weight_percent = weight_percent
        
        if "sort_order" in request.data:
            category.sort_order = request.data["sort_order"]
        
        if "is_active" in request.data:
            category.is_active = request.data["is_active"]
        
        category.save()
        
        # Validate weights after update
        _validate_category_weights(category.section_id, school_id)
    
    return Response(
        {
            "id": str(category.id),
            "name": category.name,
            "weight_percent": str(category.weight_percent),
            "sort_order": category.sort_order,
            "is_active": category.is_active,
            "created_at": category.created_at.isoformat(),
            "updated_at": category.updated_at.isoformat(),
        }
    )


# ========== Assignment Endpoints ==========

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def assignment_list_create(request, section_id):
    """
    GET: List all assignments for a section
    POST: Create a new assignment (requires write permissions)
    """
    school_id = get_request_school_id(request)
    section = get_object_or_404(Section, id=section_id, school_id=school_id)
    
    if request.method == "GET":
        assignments = Assignment.objects.filter(
            section_id=section_id,
            school_id=school_id
        ).select_related("category").order_by("category__sort_order", "due_date", "name")
        
        data = [
            {
                "id": str(asg.id),
                "name": asg.name,
                "category_id": str(asg.category_id),
                "category_name": asg.category.name,
                "points_possible": f"{asg.points_possible:.2f}",
                "due_date": asg.due_date.isoformat() if asg.due_date else None,
                "assigned_date": asg.assigned_date.isoformat() if asg.assigned_date else None,
                "is_published": asg.is_published,
                "created_at": asg.created_at.isoformat(),
                "updated_at": asg.updated_at.isoformat(),
            }
            for asg in assignments
        ]
        return Response({"assignments": data})
    
    # POST
    if not _can_write(request.user, school_id):
        raise PermissionDenied("Only ADMIN or DIRECTOR can create assignments")
    
    name = request.data.get("name", "").strip()
    if not name:
        raise ValidationError("name is required")
    
    category_id = request.data.get("category_id")
    if not category_id:
        raise ValidationError("category_id is required")
    
    category = get_object_or_404(
        AssignmentCategory,
        id=category_id,
        section_id=section_id,
        school_id=school_id
    )
    
    try:
        points_possible = Decimal(str(request.data.get("points_possible", "0")))
    except (ValueError, TypeError):
        raise ValidationError("points_possible must be a valid number")
    
    if points_possible <= 0:
        raise ValidationError("points_possible must be greater than 0")
    
    due_date = request.data.get("due_date")
    assigned_date = request.data.get("assigned_date")
    is_published = request.data.get("is_published", True)
    
    assignment = Assignment.objects.create(
        school_id=school_id,
        section=section,
        category=category,
        name=name,
        points_possible=points_possible,
        due_date=due_date,
        assigned_date=assigned_date,
        is_published=is_published,
    )
    
    return Response(
        {
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
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def assignment_update_delete(request, assignment_id):
    """
    PATCH: Update an assignment
    DELETE: Delete an assignment (requires write permissions)
    """
    school_id = get_request_school_id(request)
    
    if not _can_write(request.user, school_id):
        raise PermissionDenied("Only ADMIN or DIRECTOR can modify assignments")
    
    assignment = get_object_or_404(Assignment, id=assignment_id, school_id=school_id)
    
    if request.method == "DELETE":
        assignment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    # PATCH
    if "name" in request.data:
        name = request.data["name"].strip()
        if not name:
            raise ValidationError("name cannot be empty")
        assignment.name = name
    
    if "points_possible" in request.data:
        try:
            points_possible = Decimal(str(request.data["points_possible"]))
        except (ValueError, TypeError):
            raise ValidationError("points_possible must be a valid number")
        
        if points_possible <= 0:
            raise ValidationError("points_possible must be greater than 0")
        
        assignment.points_possible = points_possible
    
    if "category_id" in request.data:
        category = get_object_or_404(
            AssignmentCategory,
            id=request.data["category_id"],
            section_id=assignment.section_id,
            school_id=school_id
        )
        assignment.category = category
    
    if "due_date" in request.data:
        assignment.due_date = request.data["due_date"]
    
    if "assigned_date" in request.data:
        assignment.assigned_date = request.data["assigned_date"]
    
    if "is_published" in request.data:
        assignment.is_published = request.data["is_published"]
    
    assignment.save()
    
    return Response(
        {
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
    )
