from functools import wraps

from django.http import JsonResponse

from .models import SchoolModule


def school_has_module(school_id, module_key):
    """Return True only when school has active or active-trial module entitlement."""
    try:
        module = SchoolModule.objects.get(school_id=school_id, module_key=module_key)
        return module.is_active or module.is_trial
    except SchoolModule.DoesNotExist:
        return False
    except Exception:
        return False


def get_school_modules(school_id):
    """Return module_key -> status mapping for all known module keys."""
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
    """Decorator that returns 403 when module entitlement is missing."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            school_id = getattr(request, "school_id", None)
            if not school_id:
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
