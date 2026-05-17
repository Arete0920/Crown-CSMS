from rest_framework.permissions import BasePermission


class SensitiveFaithDataPermission(BasePermission):
    """
    Elevated permission gate for spiritual/pastoral data.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        return user.is_superuser or user.has_perm("students.view_sensitive_faith_data")
