import json
import logging

from functools import wraps

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .gates import get_school_modules
from .models import SchoolModule

logger = logging.getLogger(__name__)


def is_crown_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def crown_admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_crown_admin(request.user):
            return JsonResponse({"error": "Admin privileges required"}, status=403)
        return view_func(request, *args, **kwargs)

    return _wrapped


@csrf_exempt
@crown_admin_required
@require_http_methods(["GET"])
def list_school_modules(request):
    school_id = getattr(request, "school_id", None)
    if not school_id:
        return JsonResponse({"error": "X-School-Id header required"}, status=400)

    module_map = get_school_modules(school_id)
    rows = []
    for mod in SchoolModule.objects.filter(school_id=school_id).select_related("activated_by"):
        rows.append(
            {
                "module_key": mod.module_key,
                "module_label": mod.get_module_key_display(),
                "status": mod.status,
                "is_active": mod.is_active,
                "price_paid": str(mod.price_paid) if mod.price_paid else None,
                "billing_cycle": mod.billing_cycle,
                "purchased_date": mod.purchased_date.isoformat() if mod.purchased_date else None,
                "expiry_date": mod.expiry_date.isoformat() if mod.expiry_date else None,
                "activated_by": mod.activated_by.email if mod.activated_by else None,
                "notes": mod.notes,
            }
        )

    return JsonResponse(
        {
            "school_id": str(school_id),
            "module_map": module_map,
            "modules": rows,
        }
    )


@csrf_exempt
@crown_admin_required
@require_http_methods(["POST"])
def activate_module(request):
    school_id = getattr(request, "school_id", None)
    if not school_id:
        return JsonResponse({"error": "X-School-Id header required"}, status=400)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    module_key = body.get("module_key")
    if not module_key:
        return JsonResponse({"error": "module_key is required"}, status=400)

    valid_keys = [k for k, _ in SchoolModule.MODULE_CHOICES]
    if module_key not in valid_keys:
        return JsonResponse(
            {"error": f"Invalid module_key. Valid options: {valid_keys}"},
            status=400,
        )

    module, created = SchoolModule.objects.get_or_create(
        school_id=school_id,
        module_key=module_key,
    )

    module.activate(
        activated_by_user=request.user,
        price_paid=body.get("price_paid"),
        months=int(body.get("months", 12)),
    )
    module.billing_cycle = body.get("billing_cycle", "annual")
    module.notes = body.get("notes", "")
    module.save()

    logger.info(
        "Module ACTIVATED: school=%s module=%s by=%s price=%s",
        school_id,
        module_key,
        request.user.email,
        module.price_paid,
    )

    return JsonResponse(
        {
            "success": True,
            "module_key": module_key,
            "status": module.status,
            "expiry_date": module.expiry_date.isoformat(),
            "activated_by": request.user.email,
        },
        status=201 if created else 200,
    )


@csrf_exempt
@crown_admin_required
@require_http_methods(["POST"])
def deactivate_module(request):
    school_id = getattr(request, "school_id", None)
    if not school_id:
        return JsonResponse({"error": "X-School-Id header required"}, status=400)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    module_key = body.get("module_key")
    if not module_key:
        return JsonResponse({"error": "module_key is required"}, status=400)

    try:
        module = SchoolModule.objects.get(school_id=school_id, module_key=module_key)
        module.deactivate()
        logger.info(
            "Module DEACTIVATED: school=%s module=%s by=%s",
            school_id,
            module_key,
            request.user.email,
        )
        return JsonResponse({"success": True, "module_key": module_key, "status": "inactive"})
    except SchoolModule.DoesNotExist:
        return JsonResponse({"error": "Module record not found for this school"}, status=404)


@csrf_exempt
@crown_admin_required
@require_http_methods(["POST"])
def start_trial(request):
    school_id = getattr(request, "school_id", None)
    if not school_id:
        return JsonResponse({"error": "X-School-Id header required"}, status=400)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    module_key = body.get("module_key")
    if not module_key:
        return JsonResponse({"error": "module_key is required"}, status=400)

    module, _ = SchoolModule.objects.get_or_create(
        school_id=school_id,
        module_key=module_key,
    )
    module.start_trial(days=int(body.get("days", 30)))

    logger.info(
        "Module TRIAL STARTED: school=%s module=%s by=%s",
        school_id,
        module_key,
        request.user.email,
    )

    return JsonResponse(
        {
            "success": True,
            "module_key": module_key,
            "status": "trial",
            "expiry_date": module.expiry_date.isoformat(),
        }
    )
