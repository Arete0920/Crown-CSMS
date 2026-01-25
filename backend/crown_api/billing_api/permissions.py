from rest_framework.permissions import BasePermission


ALLOWED_GROUPS = {
    "Business Manager",
    "Finance Director",
}


class IsFinanceRole(BasePermission):
    message = "You do not have permission to perform billing actions."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False

        if getattr(user, "is_superuser", False):
            return True

        try:
            user_groups = set(user.groups.values_list("name", flat=True))
        except Exception:
            return False

        return bool(user_groups & ALLOWED_GROUPS)
