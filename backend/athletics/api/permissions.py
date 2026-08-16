# backend/athletics/api/permissions.py
from __future__ import annotations

from rest_framework.permissions import BasePermission

from core.permissions import user_has_permission


def _request_school(request):
    """Resolve the already-authorized tenant for an Athletics permission check."""
    context = getattr(request, "crown_tenant", None)
    school = getattr(context, "school", None)
    if school is None:
        school = getattr(request, "school", None) or getattr(request, "tenant_school", None)
    if school is not None:
        return school

    from core.models import School
    from households.scoping import get_request_school_id

    school_id = get_request_school_id(request, required=True)
    return School.objects.filter(pk=school_id).first()


def has_athletics_view(request) -> bool:
    """Return whether the principal has persistent tenant-scoped Athletics authority."""
    user = getattr(request, "user", None)
    if not (user and getattr(user, "is_authenticated", False)):
        return False

    school = _request_school(request)
    if school is None:
        return False
    return user_has_permission(user, "athletics.view", school=school)


def _is_active_coach(request) -> bool:
    user = getattr(request, "user", None)
    if not (user and getattr(user, "is_authenticated", False)):
        return False

    school = _request_school(request)
    if school is None:
        return False

    from athletics.models import TeamCoach

    return TeamCoach.objects.filter(
        school=school,
        user=user,
        is_active=True,
    ).exists()


class IsAthleticDirector(BasePermission):
    """Require persistent tenant-scoped CROWN Athletics authority."""

    def has_permission(self, request, view) -> bool:
        return has_athletics_view(request)


class IsCoachOrAD(BasePermission):
    """Allow persistent Athletics authority or a verified active coach assignment."""

    def has_permission(self, request, view) -> bool:
        return has_athletics_view(request) or _is_active_coach(request)
