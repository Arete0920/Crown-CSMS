from __future__ import annotations
from typing import Optional
from uuid import UUID

from django.db.models import QuerySet
from rest_framework.exceptions import ValidationError


# Canonical header per TENANT_PRIVACY_CANON.md
CANONICAL_SCHOOL_HEADER = "X-School-Id"
# Legacy alias for backward compatibility
LEGACY_SCHOOL_HEADER = "X-Crown-School-Id"


class MissingSchoolContext(ValidationError):
    """
    Raised when tenant context is required but missing or invalid.
    Results in HTTP 400 Bad Request per TENANT_PRIVACY_CANON.md
    """
    status_code = 400
    default_detail = "Missing or invalid school context (X-School-Id)"
    default_code = "missing_school_context"


def get_request_school_id(request, *, required: bool = False) -> Optional[UUID]:
    """
    Single source of truth for tenant context.
    
    Per TENANT_PRIVACY_CANON.md:
    - Returns school UUID from authenticated user or staff override header
    - If required=True and missing: raises MissingSchoolContext (400)
    - If required=False and missing: returns None (caller handles)
    
    Header precedence (staff/superuser only):
    1. X-School-Id (canonical)
    2. X-Crown-School-Id (legacy alias)
    
    Then falls back to user.school_id / user.school.id
    """
    user = getattr(request, "user", None)

    # MVP-safe compromise:
    # - Default school context comes from the authenticated user.
    # - Staff/superusers may override via header for cross-school testing.
    if user and getattr(user, "is_authenticated", False):
        is_staffish = bool(getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
        raw_override = None
        
        if is_staffish:
            # Try canonical header first (Django test client: HTTP_X_SCHOOL_ID)
            raw_override = request.META.get("HTTP_X_SCHOOL_ID")
            
            # Fall back to legacy alias (Django test client: HTTP_X_CROWN_SCHOOL_ID)
            if not raw_override:
                raw_override = request.META.get("HTTP_X_CROWN_SCHOOL_ID")

        if raw_override:
            raw_override = str(raw_override).strip()
            try:
                override_id = UUID(raw_override)
            except Exception:
                # For staff/superusers only, treat invalid override as a client error.
                raise MissingSchoolContext({"detail": f"Invalid {CANONICAL_SCHOOL_HEADER}"})

            # Ensure the school exists.
            try:
                from core.models import School

                if not School.objects.filter(id=override_id).exists():
                    from rest_framework.exceptions import NotFound

                    raise NotFound({"detail": "School not found"})
            except Exception:
                # If School model isn't available for some reason, fail closed.
                from rest_framework.exceptions import NotFound

                raise NotFound({"detail": "School not found"})

            # Annotate request for downstream audit logging.
            setattr(request, "_crown_school_override_id", override_id)
            return override_id

        # common patterns
        sid = getattr(user, "school_id", None)
        if sid:
            return sid

        school = getattr(user, "school", None)
        if school and getattr(school, "id", None):
            return school.id

    # optional: some stacks attach school_id at middleware
    sid = getattr(request, "school_id", None)
    if sid:
        return sid

    # If required and still None, raise exception
    if required:
        raise MissingSchoolContext()

    return None


def scope_to_school(request, qs: QuerySet, *, required: bool = True) -> QuerySet:
    """
    Apply school-level tenant scoping to a queryset.
    
    Args:
        request: The HTTP request containing tenant context
        qs: The queryset to scope
        required: If True, raises MissingSchoolContext when tenant is missing (default: True)
                  If False, returns qs.none() when tenant is missing (legacy behavior)
    
    Returns:
        Filtered queryset scoped to the tenant's school_id
    """
    sid = get_request_school_id(request, required=required)
    if not sid:
        # Only reachable if required=False
        return qs.none()
    return qs.filter(school_id=sid)
