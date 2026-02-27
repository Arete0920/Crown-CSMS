# backend/transportation/api/permissions.py
from rest_framework.permissions import BasePermission

TRANSPORT_WRITE_ROLES = frozenset({"transportation_director", "admin", "ops"})


class IsTransportationStaffOrReadOnly(BasePermission):
    """
    Safe methods (GET, HEAD, OPTIONS): any authenticated user.
    Writes: is_staff / is_superuser OR X-Role in TRANSPORT_WRITE_ROLES.
    """
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        if user.is_staff or user.is_superuser:
            return True
        role = request.META.get("HTTP_X_ROLE", "")
        return role in TRANSPORT_WRITE_ROLES
