import os
from functools import wraps
from django.http import JsonResponse


def _get_user_role(request):
    """
    Crown demo-friendly role resolution.
    Priority:
      1) request.user.role (if your User model has it)
      2) HTTP header X-Demo-Role (only if ALLOW_DEMO_ROLE_HEADER=1)
      3) None
    
    SECURITY: X-Demo-Role header only works when ALLOW_DEMO_ROLE_HEADER=1
    to prevent privilege escalation in production.
    """
    # 1) user.role
    user = getattr(request, "user", None)
    role = getattr(user, "role", None)
    if role:
        return str(role)

    # 2) demo header fallback (only if explicitly enabled)
    if os.getenv("ALLOW_DEMO_ROLE_HEADER") == "1":
        hdr = request.headers.get("X-Demo-Role") or request.META.get("HTTP_X_DEMO_ROLE")
        if hdr:
            return str(hdr).strip()

    return None


def require_roles(allowed_roles):
    """
    Decorator enforcing that request has one of allowed roles.
    Returns JSON 403 with required_roles and actual_role.
    """
    allowed = set(str(r) for r in allowed_roles)

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            actual = _get_user_role(request)
            if actual not in allowed:
                return JsonResponse(
                    {
                        "ok": False,
                        "error": "Forbidden",
                        "required_roles": sorted(list(allowed)),
                        "actual_role": actual,
                    },
                    status=403,
                )
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
