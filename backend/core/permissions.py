# backend/core/permissions.py
#
# Crown Central Permission Engine — Layer 1 of the institutional architecture.
#
# Does NOT use Django's built-in Permission framework — Crown uses its own
# CrownPermission / RolePermission models keyed on role_code strings that
# match core.models.UserRole.role_code.
#
# Usage:
#   from core.permissions import require_permission, user_has_permission
#
#   @require_permission("finance.view")
#   def my_view(request): ...
#
#   # Or in code:
#   if user_has_permission(request.user, "health.view", school=request.school):
#       ...

from functools import wraps

from django.http import JsonResponse
from rest_framework.permissions import BasePermission


def user_has_permission(user, permission_code, school=None):
    """
    Return True if `user` holds a role (optionally scoped to `school`) that
    grants `permission_code`.

    `user` must be a UserAccount instance (the Crown custom auth model).
    `school` is an optional School instance used to scope the role lookup to a
    single tenant; when None, roles across all schools are checked.
    """
    if not user.is_authenticated:
        return False

    qs = user.roles.all()
    if school is not None:
        qs = qs.filter(school=school)

    role_codes = qs.values_list("role_code", flat=True)
    if not role_codes:
        return False

    from .models import RolePermission

    return RolePermission.objects.filter(
        role_code__in=role_codes,
        permission__code=permission_code,
    ).exists()


def require_permission(permission_code):
    """View decorator that enforces a Crown permission gate."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            school = getattr(request, "school", None)
            if not user_has_permission(request.user, permission_code, school=school):
                return JsonResponse({"detail": "Permission denied."}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class CrownModulePermission:
    """DRF permission factory using Crown role/permission mappings."""

    def __new__(cls, read_code: str, write_code: str | None = None):
        _read_code = read_code
        _write_code = write_code or read_code

        class _CrownPerm(BasePermission):
            def has_permission(self, request, view):
                if not request.user or not request.user.is_authenticated:
                    return False
                school = getattr(request, "school", None)
                if school is None:
                    from households.scoping import get_request_school_id
                    from .models import School

                    school_id = get_request_school_id(request, required=True)
                    school = School.objects.filter(pk=school_id).first()
                    if school is None:
                        return False
                code = _write_code if request.method not in ("GET", "HEAD", "OPTIONS") else _read_code
                return user_has_permission(request.user, code, school=school)

        _CrownPerm.__name__ = f"CrownPerm[{read_code}]"
        return _CrownPerm


class RoleRequired(BasePermission):
    """DRF permission that checks the user's role field."""

    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, "is_authenticated", False):
            return False
        roles = getattr(view, "required_roles", None) or set()
        if not roles:
            return True
        user_role = getattr(request.user, "role", None)
        return user_role in roles
