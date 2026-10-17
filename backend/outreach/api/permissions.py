"""School-scoped Outreach permissions; request headers never grant authority."""

from rest_framework.permissions import BasePermission, SAFE_METHODS

from core.models import School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id


def _school(request):
    school = getattr(request, "school", None)
    if school is not None:
        return school
    school_id = get_request_school_id(request, required=True)
    return School.objects.filter(pk=school_id).first()


def _allowed(request, code):
    return user_has_permission(getattr(request, "user", None), code, school=_school(request))


def _is_coordinator(request):
    return _allowed(request, "service.manage")


class IsStudentOrStaff(BasePermission):
    """Authorize school managers or students with an explicit self-service grant."""

    def has_permission(self, request, view):
        return _is_coordinator(request) or _allowed(request, "service.self")


class IsStaffOnly(BasePermission):
    """School-scoped manager authority, independent of client-supplied role headers."""

    def has_permission(self, request, view):
        return _is_coordinator(request)


class IsServiceApprover(BasePermission):
    """Approval authority is separate from general record management."""

    def has_permission(self, request, view):
        return _allowed(request, "service.approve")
