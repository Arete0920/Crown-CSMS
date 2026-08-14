from rest_framework.permissions import BasePermission

from core.models import UserRole
from households.scoping import get_request_school_id


class CanManageAcademicYear(BasePermission):
    """Restrict academic-year rollover mutations to school leadership."""

    message = "Academic year rollover requires HEAD_OF_SCHOOL authorization."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        if getattr(user, "is_superuser", False):
            return True

        school_id = get_request_school_id(request, required=True)
        return UserRole.objects.filter(
            user_id=getattr(user, "id", None),
            school_id=school_id,
            role_code="HEAD_OF_SCHOOL",
        ).exists()
