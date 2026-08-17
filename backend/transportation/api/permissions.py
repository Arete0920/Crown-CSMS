# backend/transportation/api/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

from core.models import School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id


class IsTransportationStaffOrReadOnly(BasePermission):
    """Tenant-scoped persistent CROWN authorization for Transportation.

    Caller-supplied role headers and Django staff/superuser flags are never
    Transportation authority. Reads require ``transportation.view`` and
    mutations require the recovered canonical ``transportation.edit`` capability
    for the active school.
    """

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        school = getattr(request, "school", None)
        if school is None:
            school_id = get_request_school_id(request, required=True)
            school = School.objects.filter(pk=school_id).first()
            if school is None:
                return False

        code = "transportation.view" if request.method in SAFE_METHODS else "transportation.edit"
        return user_has_permission(user, code, school=school)
