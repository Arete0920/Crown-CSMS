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

    # user.roles is the reverse FK from UserRole (role_code CharField → UserAccount).
    qs = user.roles.all()
    if school is not None:
        qs = qs.filter(school=school)

    role_codes = qs.values_list("role_code", flat=True)
    if not role_codes:
        return False

    # Import here to avoid circular imports during app startup.
    from .models import RolePermission

    return RolePermission.objects.filter(
        role_code__in=role_codes,
        permission__code=permission_code,
    ).exists()


def require_permission(permission_code):
    """
    View decorator that enforces a Crown permission gate.

    - Returns 403 JSON {"detail": "Permission denied."} on failure.
    - School scope is picked up automatically from request.school (set by
      TenantHeaderRequiredMiddleware for /api/v1/* routes).
    - Works with both function-based and class-based views (wrap dispatch()).
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            school = getattr(request, "school", None)
            if not user_has_permission(request.user, permission_code, school=school):
                return JsonResponse({"detail": "Permission denied."}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
