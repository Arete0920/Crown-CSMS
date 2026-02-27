from rest_framework.permissions import BasePermission, SAFE_METHODS


def _is_coordinator(request) -> bool:
    """
    Returns True if the request comes from a staff/coordinator/admin.
    Requires the user to be authenticated. Checks is_staff / is_superuser
    first; then falls back to the X-Role header for authenticated users.
    """
    user = getattr(request, "user", None)
    if not (user and getattr(user, "is_authenticated", False)):
        return False
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return True
    role = (request.headers.get("X-Role") or "").lower()
    return role in ("staff", "admin", "coordinator")


class IsStudentOrStaff(BasePermission):
    """Allow anyone authenticated; writes restricted to recognised roles."""

    def has_permission(self, request, view):
        if not getattr(request, "user", None):
            return False
        if request.method in SAFE_METHODS:
            return True
        role = (request.headers.get("X-Role") or "").lower()
        return role in ("student", "staff", "admin", "coordinator") or _is_coordinator(request)


class IsStaffOnly(BasePermission):
    """Restrict all methods to staff/coordinator/admin."""

    def has_permission(self, request, view):
        return _is_coordinator(request)
