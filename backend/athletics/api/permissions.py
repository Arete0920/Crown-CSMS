# backend/athletics/api/permissions.py
from __future__ import annotations

from rest_framework.permissions import BasePermission


def _is_staff_or_superuser(request) -> bool:
    """True if the authenticated user has Django staff or superuser flag."""
    user = getattr(request, "user", None)
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
    )


def _role(request) -> str:
    return (request.headers.get("X-Role") or "").lower()


class IsAthleticDirector(BasePermission):
    """
    Grants access to authenticated staff/superusers or users presenting
    X-Role: athletic_director.
    """

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not (user and getattr(user, "is_authenticated", False)):
            return False
        if _is_staff_or_superuser(request):
            return True
        return _role(request) == "athletic_director"


class IsCoachOrAD(BasePermission):
    """
    Grants access to authenticated staff/superusers or users presenting
    X-Role: coach or X-Role: athletic_director.
    """

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not (user and getattr(user, "is_authenticated", False)):
            return False
        if _is_staff_or_superuser(request):
            return True
        return _role(request) in ("athletic_director", "coach")
