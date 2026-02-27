# backend/facops/api/permissions.py
from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS


def _authenticated(request) -> bool:
    user = getattr(request, "user", None)
    return bool(user and getattr(user, "is_authenticated", False))


def _is_staff_or_super(request) -> bool:
    user = getattr(request, "user", None)
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
    )


def _role(request) -> str:
    return (request.headers.get("X-Role") or "").lower()


FACILITIES_WRITE_ROLES = frozenset({"facilities_director", "technician", "admin"})
SAFETY_WRITE_ROLES = frozenset({"safety_officer", "admin", "facilities_director"})


class IsFacilitiesStaffOrReadOnly(BasePermission):
    """
    Safe methods: any authenticated user.
    Writes: staff/superuser or recognised facilities role.
    """

    def has_permission(self, request, view) -> bool:
        if not _authenticated(request):
            return False
        if request.method in SAFE_METHODS:
            return True
        return _is_staff_or_super(request) or _role(request) in FACILITIES_WRITE_ROLES


class CanCreateWorkOrder(BasePermission):
    """Any authenticated user may create or read work orders — teachers can request."""

    def has_permission(self, request, view) -> bool:
        return _authenticated(request)


class IsSafetyOfficerOrReadOnly(BasePermission):
    """
    Safe methods: any authenticated user.
    Writes: staff/superuser or recognised safety role.
    """

    def has_permission(self, request, view) -> bool:
        if not _authenticated(request):
            return False
        if request.method in SAFE_METHODS:
            return True
        return _is_staff_or_super(request) or _role(request) in SAFETY_WRITE_ROLES
