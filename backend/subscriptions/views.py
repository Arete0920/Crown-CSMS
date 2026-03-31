"""
Crown Admin Module Management API
-----------------------------------
Endpoints for Crown staff to activate/deactivate school modules after payment.

All endpoints require:
  - IsAdminUser (Django staff/superuser)
  - X-School-Id header (standard tenant middleware)

These are internal Crown operations - NOT exposed to school users.
"""

import logging
import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt

from .models import SchoolModule
from .gates import get_school_modules

logger = logging.getLogger(__name__)


def is_crown_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@csrf_exempt
@user_passes_test(is_crown_admin)
@require_http_methods(["GET"])
def list_school_modules(request):
    """
    GET /api/v1/admin/modules/
    Returns all module entitlements for the school in X-School-Id header.
    """
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
@user_passes_test(is_crown_admin)
@require_http_methods(["POST"])
def activate_module(request):
    """
    POST /api/v1/admin/modules/activate/
    Body (JSON):
    {
        "module_key": "financial_aid",
        "price_paid": 1500.00,
        "billing_cycle": "annual",
        "months": 12,
        "notes": "Invoice #1234"
    }
    """
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
@user_passes_test(is_crown_admin)
@require_http_methods(["POST"])
def deactivate_module(request):
    """
    POST /api/v1/admin/modules/deactivate/
    Body (JSON): { "module_key": "financial_aid" }
    """
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
@user_passes_test(is_crown_admin)
@require_http_methods(["POST"])
def start_trial(request):
    """
    POST /api/v1/admin/modules/trial/
    Body (JSON): { "module_key": "financial_aid", "days": 30 }
    Starts a free trial for a module.
    """
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
