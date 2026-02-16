from __future__ import annotations

from rest_framework.exceptions import ValidationError

from core.models import School


def get_school_from_header(request) -> School:
    """
    Canonical demo-safe scoping:
    require X-School-Id and resolve core.School.
    """
    raw = request.headers.get("X-School-Id") or request.META.get("HTTP_X_SCHOOL_ID")
    if not raw:
        raise ValidationError({"detail": "CTX_MISSING_SCHOOL_ID: X-School-Id header is required."})
    try:
        return School.objects.get(id=raw)
    except School.DoesNotExist:
        raise ValidationError({"detail": f"CTX_INVALID_SCHOOL_ID: no school found for X-School-Id={raw}."})
