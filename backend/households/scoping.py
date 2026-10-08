from __future__ import annotations

from dataclasses import replace
from typing import Optional
from uuid import UUID

from django.db.models import QuerySet
from rest_framework.exceptions import NotFound, ValidationError

from crown_api.tenant import (
    CANONICAL_TENANT_ATTR,
    bind_tenant_context,
    build_tenant_context,
)


# Canonical header per TENANT_PRIVACY_CANON.md
CANONICAL_SCHOOL_HEADER = "X-School-Id"
# Legacy alias for backward compatibility
LEGACY_SCHOOL_HEADER = "X-Crown-School-Id"


class MissingSchoolContext(ValidationError):
    """
    Raised when tenant context is required but missing or invalid.
    Results in HTTP 400 Bad Request per TENANT_PRIVACY_CANON.md.
    """

    status_code = 400
    default_detail = "Missing or invalid school context (X-School-Id)"
    default_code = "missing_school_context"


def _canonical_context(request):
    """Return the immutable request tenant contract, binding it when absent."""
    context = getattr(request, CANONICAL_TENANT_ATTR, None)
    if context is None:
        context = bind_tenant_context(request, build_tenant_context(request))
    return context


def get_request_school_id(request, required: bool = True) -> Optional[UUID]:
    """
    Resolve and validate the school ID through the canonical tenant contract.

    Enforcement contract:
    - malformed tenant header -> 400;
    - missing tenant when required -> 400;
    - unknown school -> 404;
    - conflicting header without explicit override authority -> 404;
    - superuser, explicit permission, or SUPPORT-role override -> allowed.

    Ordinary ``is_staff`` status is not cross-school authority.
    """
    context = _canonical_context(request)

    if context.source == "header_invalid":
        raise MissingSchoolContext("Invalid tenant header UUID")

    school_id = context.school_id
    if not school_id:
        if required:
            raise MissingSchoolContext()
        return None

    if context.override_requested and not context.override_authorized:
        raise NotFound({"detail": "Not found"})

    try:
        from core.models import School

        school = School.objects.filter(pk=school_id).first()
        if school is None:
            raise NotFound({"detail": "Tenant not found"})
    except NotFound:
        raise
    except Exception as exc:
        raise NotFound({"detail": "Tenant not found"}) from exc

    # Permission checks consume the school object, not only its identifier.
    # Bind it only after header validation and cross-school authorization succeed.
    bind_tenant_context(request, replace(context, school=school))
    return school_id


def scope_to_school(request, qs: QuerySet, *, required: bool = True) -> QuerySet:
    """Apply canonical school-level tenant scoping to a queryset."""
    school_id = get_request_school_id(request, required=required)
    if not school_id:
        return qs.none()
    return qs.filter(school_id=school_id)
