from __future__ import annotations
from typing import Optional
from uuid import UUID

from django.db.models import QuerySet
from rest_framework.exceptions import ValidationError, NotFound

from crown_api.tenant import resolve_tenant_school_id


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


def _is_staff_user(user) -> bool:
    """Check if user is staff or superuser."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return bool(getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))


def get_request_school_id(request, required: bool = True) -> Optional[UUID]:
    """
    Canonical tenant resolver with validation.
    
    Enforces the full contract:
    - Invalid header UUID → 400
    - Valid header UUID but school doesn't exist → 404
    - No tenant when required → 400
    - Non-staff using header for different school → 404 (prevent cross-tenant leakage)
    - Staff can use header to override tenant
    
    Returns:
        school_id (UUID) if resolved successfully
        None if not resolved and not required
    
    Raises:
        MissingSchoolContext (400): Invalid header UUID or no tenant when required
        NotFound (404): Valid UUID but school doesn't exist, or non-staff cross-tenant
    """
    res = resolve_tenant_school_id(request)
    
    # 400: Invalid UUID in header
    if res.source == "header_invalid":
        raise MissingSchoolContext("Invalid tenant header UUID")
    
    # 400: No tenant resolved and it's required
    if not res.school_id:
        if required:
            raise MissingSchoolContext()
        return None
    
    # 404: Valid UUID but school does not exist
    try:
        from core.models import School
        if not School.objects.filter(pk=res.school_id).exists():
            raise NotFound({"detail": "Tenant not found"})
    except NotFound:
        raise
    except Exception:
        raise NotFound({"detail": "Tenant not found"})
    
    # 404: Non-staff user attempting cross-tenant access via header
    # If header was explicitly used, enforce that non-staff can only access their own school
    if res.header_present and res.source == "header":
        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False) and not _is_staff_user(user):
            user_school = getattr(user, "school_id", None)
            if user_school and str(user_school) != str(res.school_id):
                raise NotFound({"detail": "Not found"})
    
    return res.school_id


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
