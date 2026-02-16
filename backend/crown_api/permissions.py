"""
Role-based access control helpers for production permission enforcement.
"""
from django.http import JsonResponse


def require_role(allowed_roles):
    """
    Decorator to enforce role-based access control.
    
    Usage:
        @require_role(["admin", "finance"])
        def finance_dashboard(request):
            ...
    
    Returns 403 if user role not in allowed_roles.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user_role = getattr(request.user, "role", None) if hasattr(request, "user") else None
            if user_role not in allowed_roles:
                return JsonResponse({
                    "ok": False,
                    "error": "Forbidden",
                    "required_roles": allowed_roles
                }, status=403)
            return view_func(request, *args, **kwargs)
        wrapper.__name__ = view_func.__name__
        wrapper.__doc__ = view_func.__doc__
        return wrapper
    return decorator
