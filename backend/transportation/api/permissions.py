# backend/transportation/api/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

from core.permissions import user_has_permission


def _request_school(request):
    school = getattr(request, "school", None) or getattr(request, "tenant_school", None)
    if school is not None:
        return school
    try:
        from core.models import School
        from households.scoping import get_request_school_id

        school_id = get_request_school_id(request, required=True)
        return School.objects.filter(pk=school_id).first()
    except Exception:
        return None


class IsTransportationStaffOrReadOnly(BasePermission):
    """Persistent tenant-scoped Transportation authority; no header/staff bypass."""

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        school = _request_school(request)
        if school is None:
            return False
        permission_code = "transportation.view" if request.method in SAFE_METHODS else "transportation.edit"
        return user_has_permission(user, permission_code, school=school)
