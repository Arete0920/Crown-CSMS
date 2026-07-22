from functools import wraps

from django.http import JsonResponse


def _normalize_role(value):
    if value is None:
        return None
    normalized = str(value).strip().lower()
    return normalized or None


def _get_user_role(request):
    """Return the authenticated principal's normalized runtime role.

    Authorization must derive only from an authenticated principal. Request
    headers and environment flags are intentionally ignored so deployed
    configuration cannot create an anonymous role-elevation path.
    """
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return None
    return _normalize_role(getattr(user, "role", None))


def require_roles(allowed_roles):
    """Require an authenticated principal with one of the allowed roles."""
    allowed = {
        normalized
        for role in allowed_roles
        if (normalized := _normalize_role(role)) is not None
    }

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            actual = _get_user_role(request)
            if actual not in allowed:
                return JsonResponse(
                    {
                        "ok": False,
                        "error": "Forbidden",
                        "required_roles": sorted(allowed),
                        "actual_role": actual,
                    },
                    status=403,
                )
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
