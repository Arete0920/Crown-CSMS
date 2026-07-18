"""
Crown Module Gate System
-------------------------
Use these helpers to check module entitlements anywhere in the codebase.

Usage in a view:
    from subscriptions.gates import require_module, school_has_module

    # As a decorator:
    @require_module('financial_aid')
    def my_view(request):
        ...

    # As a check:
    if school_has_module(school_id, 'financial_aid'):
        ...
"""
from functools import wraps

from django.http import JsonResponse

from crown_api.tenant import get_tenant_school_id

from .models import SchoolModule


def school_has_module(school_id, module_key):
    """
    Returns True if the school has an active (or active trial) entitlement
    for the given module_key.

    Fail-closed: any exception -> returns False (safe default).
    """
    try:
        module = SchoolModule.objects.get(school_id=school_id, module_key=module_key)
        return module.is_active or module.is_trial
    except SchoolModule.DoesNotExist:
        return False
    except Exception:
        return False


def get_school_modules(school_id):
    """
    Returns a dict of all module keys -> status for a school.
    Used by the frontend to build the module visibility map.
    """
    all_keys = [key for key, _ in SchoolModule.MODULE_CHOICES]
    result = {key: "inactive" for key in all_keys}

    active_modules = SchoolModule.objects.filter(school_id=school_id)
    for mod in active_modules:
        if mod.is_active:
            result[mod.module_key] = "active"
        elif mod.is_trial:
            result[mod.module_key] = "trial"
        else:
            result[mod.module_key] = mod.status

    return result


def require_module(module_key):
    """
    View decorator that gates access to a module entitlement.
    Returns 400 when canonical tenant context is unavailable and 403 when the
    resolved tenant does not have the requested module enabled.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                school_id = get_tenant_school_id(request, required=True)
            except PermissionError:
                return JsonResponse(
                    {"error": "School context required", "code": "NO_SCHOOL_CONTEXT"},
                    status=400,
                )

            if not school_has_module(school_id, module_key):
                return JsonResponse(
                    {
                        "error": "Module not enabled for this school",
                        "code": "MODULE_NOT_ENABLED",
                        "module": module_key,
                    },
                    status=403,
                )
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
