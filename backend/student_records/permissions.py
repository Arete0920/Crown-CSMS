from rest_framework.permissions import BasePermission

from core.models import School
from core.permissions import user_has_permission
from tenants.tenant_context import get_request_school_id


class CanViewStudentRecords(BasePermission):
    """Require registrar-scoped authority for sensitive student-master records."""

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        school_id = get_request_school_id(request, required=True)
        school = School.objects.filter(pk=school_id).first()
        if school is None:
            return False
        return user_has_permission(user, "registrar.view", school=school)
