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
    Return True only for an active user's grant in an explicit school.

    Missing school context is not platform authorization. Platform controls must
    use their own explicit authority rather than combining roles across schools.
    """
    if not user or not user.is_authenticated or not getattr(user, "is_active", True) or school is None:
        return False

    # user.roles is the reverse FK from UserRole (role_code CharField → UserAccount).
    qs = user.roles.all()
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
    - School scope is resolved from request.school or the canonical tenant
      contract (including an explicit X-School-Id header).
    - Works with both function-based and class-based views (wrap dispatch()).
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, "user", None)
            if not user or not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", True):
                return JsonResponse({"detail": "Permission denied."}, status=403)
            school = getattr(request, "school", None)
            if school is None:
                # Exempt non-API routes do not establish a tenant by borrowing
                # a principal's role membership. Require an explicit school.
                if not request.path.startswith("/api/") and not (
                    request.META.get("HTTP_X_SCHOOL_ID")
                    or request.META.get("HTTP_X_CROWN_SCHOOL_ID")
                ):
                    return JsonResponse({"detail": "Permission denied."}, status=403)
                # Resolve explicit tenant context from the canonical request contract.
                # A valid X-School-Id is authority context; absence of any resolvable
                # school remains fail-closed and never falls back to cross-school roles.
                from households.scoping import get_request_school_id
                from .models import School

                school_id = get_request_school_id(request, required=True)
                school = School.objects.filter(pk=school_id).first()
                if school is not None:
                    request.school = school
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
            permission_classes = [CrownModulePermission("hr.view", write_code="hr.edit")]

    For write-scoped checks (list vs mutate):
        permission_classes = [CrownModulePermission("hr.view", write_code="hr.edit")]
    - Authenticated + school context required (middleware normally enforces X-School-Id).
    - GET/HEAD/OPTIONS -> read_code; mutations require an explicit write_code.
      Omitting write_code defines a read-only permission.
    """

    def __new__(cls, read_code: str, write_code: str | None = None):
        _read_code = read_code
        _write_code = write_code

        class _CrownPerm(BasePermission):
            def has_permission(self, request, view):
                if not request.user or not request.user.is_authenticated or not getattr(request.user, "is_active", True):
                    return False
                code = _read_code if request.method in ("GET", "HEAD", "OPTIONS") else _write_code
                if not code:
                    return False
                school = getattr(request, "school", None)
                if school is None:
                    school_header = request.headers.get("X-School-Id")
                    # Selected wizard APIs deliberately require an explicit tenant
                    # header even when the authenticated principal has a home school.
                    if not school_header and request.path.startswith((
                        "/api/v1/scheduling-wizard/",
                        "/api/v1/section-scheduler-wizard/",
                        "/api/v1/staff-onboarding-wizard/",
                        "/api/v1/aid-wizard/",
                    )):
                        from households.scoping import MissingSchoolContext

                        raise MissingSchoolContext()

                    # For normal application APIs, resolve the canonical request
                    # school through the shared scoping helper. It validates any
                    # supplied header and otherwise derives the authenticated
                    # principal's school without broadening cross-tenant authority.
                    from households.scoping import get_request_school_id
                    from .models import School

                    school_id = get_request_school_id(request, required=True)
                    school = School.objects.filter(pk=school_id).first()
                    if school is None:
                        return False
                    request.school = school
                return user_has_permission(request.user, code, school=school)

        _CrownPerm.__name__ = f"CrownPerm[{read_code}]"
        return _CrownPerm


class RoleRequired(BasePermission):
    """
    DRF permission that checks the user's role field.

    Usage on a ViewSet:
        permission_classes = [RoleRequired]
        required_roles = {"ADMIN", "STAFF"}

    Missing or empty required_roles fails closed.
    """

    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, "is_authenticated", False) or not getattr(request.user, "is_active", False):
            return False
        roles = getattr(view, "required_roles", None) or set()
        if not roles:
            return False
        user_role = getattr(request.user, "role", None)
        return user_role in roles
