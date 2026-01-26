from __future__ import annotations
from typing import Optional
from uuid import UUID

from django.db.models import QuerySet


SCHOOL_OVERRIDE_HEADER = "X-Crown-School-Id"


def get_request_school_id(request) -> Optional[UUID]:
    """
    Hard rule: never leak cross-school data.
    We only return a school_id if we can derive it from the authenticated user or request.
    If we cannot, we return None and the caller must return an empty queryset.
    """
    user = getattr(request, "user", None)

    # MVP-safe compromise:
    # - Default school context comes from the authenticated user.
    # - Staff/superusers may override via header for cross-school testing.
    if user and getattr(user, "is_authenticated", False):
        is_staffish = bool(getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
        raw_override = None
        try:
            # Django exposes headers in request.headers (preferred). Fall back to META for older patterns.
            raw_override = (getattr(request, "headers", {}) or {}).get(SCHOOL_OVERRIDE_HEADER) or request.META.get(
                "HTTP_X_CROWN_SCHOOL_ID"
            )
        except Exception:
            raw_override = request.META.get("HTTP_X_CROWN_SCHOOL_ID")

        if is_staffish and raw_override:
            raw_override = str(raw_override).strip()
            try:
                override_id = UUID(raw_override)
            except Exception:
                # For staff/superusers only, treat invalid override as a client error.
                from rest_framework.exceptions import ValidationError

                raise ValidationError({"detail": f"Invalid {SCHOOL_OVERRIDE_HEADER}"})

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

    return None


def scope_to_school(request, qs: QuerySet) -> QuerySet:
    sid = get_request_school_id(request)
    if not sid:
        return qs.none()
    return qs.filter(school_id=sid)
