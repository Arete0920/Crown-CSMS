"""School-bound permissions for facilities, work orders, and campus safety.

A request header is never a role grant. Canonical tenant selection and persisted
school role/permission records independently control writes.
"""
from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS

from core.models import School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id


def _school_for_actor(request):
    user = getattr(request, "user", None)
    if not (
        user
        and getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
    ):
        return None
    school_id = get_request_school_id(request, required=True)
    if not school_id or str(getattr(user, "school_id", "")) != str(school_id):
        return None
    return School.objects.filter(pk=school_id, is_active=True).first()


def _school_grant(request, school, permission_code):
    return bool(
        school
        and user_has_permission(request.user, permission_code, school=school)
    )


class IsFacilitiesStaffOrReadOnly(BasePermission):
    """School members may read; facilities writes require a persisted grant."""

    def has_permission(self, request, view) -> bool:
        school = _school_for_actor(request)
        if school is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return _school_grant(request, school, "facilities.edit")


class CanCreateWorkOrder(BasePermission):
    """School members may request service, not change the job lifecycle."""

    def has_permission(self, request, view) -> bool:
        school = _school_for_actor(request)
        if school is None:
            return False
        if request.method in SAFE_METHODS or getattr(view, "action", None) == "create":
            return True
        return _school_grant(request, school, "facilities.edit")


class IsSafetyOfficerOrReadOnly(BasePermission):
    """School members may read; safety writes require a persisted grant."""

    def has_permission(self, request, view) -> bool:
        school = _school_for_actor(request)
        if school is None:
            return False
        if request.method in SAFE_METHODS:
            # Safety reports, visitor logs and alerts contain private data.
            # School membership is not an authorization to inspect them.
            return (
                _school_grant(request, school, "safety.view")
                or _school_grant(request, school, "safety.edit")
            )
        return _school_grant(request, school, "safety.edit")


class CanViewFacilitiesSummary(BasePermission):
    """Work-order aggregates require a school-bound facilities grant."""

    def has_permission(self, request, view) -> bool:
        school = _school_for_actor(request)
        return bool(
            school and (
                _school_grant(request, school, "facilities.view")
                or _school_grant(request, school, "facilities.edit")
            )
        )
