from __future__ import annotations

import uuid

from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import NotFound

from households.scoping import CANONICAL_SCHOOL_HEADER, LEGACY_SCHOOL_HEADER


def get_dashboard_school_id(request, *, required: bool = True) -> uuid.UUID | None:
    """Dashboards require an explicit tenant header (no fallback to user.school_id).

    - Missing tenant header -> 400
    - Invalid UUID -> 400
    """

    raw = request.headers.get(CANONICAL_SCHOOL_HEADER) or request.headers.get(LEGACY_SCHOOL_HEADER)
    if not raw:
        if required:
            raise ValidationError(
                {
                    "school_id": [
                        f"Missing {CANONICAL_SCHOOL_HEADER} header (tenant context required)."
                    ]
                }
            )
        return None

    try:
        sid = uuid.UUID(str(raw))
    except (TypeError, ValueError):
        raise ValidationError({"school_id": ["Invalid school_id UUID."]})

    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False):
        is_staffish = bool(getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
        if not is_staffish:
            user_sid = getattr(user, "school_id", None)
            if not user_sid:
                school = getattr(user, "school", None)
                user_sid = getattr(school, "id", None) if school else None

            if not user_sid:
                raise ValidationError({"school_id": ["Authenticated user is missing school context."]})

            if str(user_sid) != str(sid):
                raise NotFound({"detail": "Not found"})

    try:
        from core.models import School

        if not School.objects.filter(id=sid).exists():
            raise NotFound({"detail": "School not found"})
    except NotFound:
        raise
    except Exception:
        # Fail closed if School model isn't available for some reason.
        raise NotFound({"detail": "School not found"})

    return sid
