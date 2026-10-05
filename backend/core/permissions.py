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


# ──────────────────────────────────────────────────────────────────────────────
# DRF-compatible permission class for expansion module ViewSets.
# ──────────────────────────────────────────────────────────────────────────────

class CrownModulePermission:
    """
    DRF BasePermission factory.

    Usage:
        from core.permissions import CrownModulePermission
        class EmployeeViewSet(viewsets.ModelViewSet):
            permission_classes = [CrownModulePermission("hr.view")]

    For write-scoped checks (list vs mutate):
        permission_classes = [CrownModulePermission("hr.view", write_code="hr.edit")]
    - Authenticated + school context required (middleware normally enforces X-School-Id).
    - GET/HEAD/OPTIONS -> read_code; POST/PUT/PATCH/DELETE -> write_code (falls
      back to read_code if write_code is not supplied).
    """

    def __new__(cls, read_code: str, write_code: str | None = None):
        _read_code = read_code
        _write_code = write_code or read_code

        class _CrownPerm(BasePermission):
            def has_permission(self, request, view):
                if not request.user or not request.user.is_authenticated:
                    return False
                school = getattr(request, "school", None)
                if school is None:
                    school_header = request.headers.get("X-School-Id")
                    if not school_header:
                        # Tenant-bound module permissions must fail on missing tenant
                        # context before RBAC evaluation so a missing X-School-Id is
                        # never misreported as a generic permission denial.
                        from households.scoping import MissingSchoolContext

                        raise MissingSchoolContext()

                    from households.scoping import get_request_school_id
                    from .models import School

                    school_id = get_request_school_id(request, required=True)
                    school = School.objects.filter(pk=school_id).first()
                    if school is None:
                        return False
                    request.school = school
                code = _write_code if request.method not in ("GET", "HEAD", "OPTIONS") else _read_code
                return user_has_permission(request.user, code, school=school)

        _CrownPerm.__name__ = f"CrownPerm[{read_code}]"
        return _CrownPerm


class RoleRequired(BasePermission):
    """
    DRF permission that checks the user's role field.

    Usage on a ViewSet:
        permission_classes = [RoleRequired]
        required_roles = {"ADMIN", "STAFF"}

    If required_roles is empty or not set, all authenticated users pass.
    """

    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, "is_authenticated", False):
            return False
        roles = getattr(view, "required_roles", None) or set()
        if not roles:
            return True
        user_role = getattr(request.user, "role", None)
        return user_role in roles
