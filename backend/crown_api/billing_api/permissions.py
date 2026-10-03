from rest_framework.permissions import BasePermission
from core.permissions import user_has_permission


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


FINANCE_RUNTIME_ROLE_IDS = {"super_admin", "school_admin", "finance_admin"}


def has_finance_runtime_role(user) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False):
        return True

    # Crown UserRole/RolePermission is authoritative for current role accounts.
    # Restrict the lookup to the user's bound school; unrelated tenant grants
    # must not authorize school-wide finance access.
    if getattr(user, "school", None) is not None and user_has_permission(user, "finance.edit", school=user.school):
        return True

    group_names = {g.name.lower() for g in user.groups.all()}
    return bool(group_names & FINANCE_RUNTIME_ROLE_IDS)


class IsFinanceRuntimeUser(BasePermission):
    def has_permission(self, request, view):
        return has_finance_runtime_role(request.user)
