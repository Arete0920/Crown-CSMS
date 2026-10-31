"""Platform-only, tenant-scoped module entitlements management.

School staff do not have authority to activate, trial, or bill modules.
These state changes do not constitute payment collection or product pricing.
"""
import json
from functools import wraps

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from core.models import School
from crown_api.tenant import get_tenant_school_id
from platform_ops.models import AuditEvent

from .gates import get_school_modules
from .models import SchoolModule

CARE_MODULES = frozenset({"before_care", "after_care"})


def is_crown_admin(user):
    """Only active, unscoped platform superusers may change entitlements."""
    return bool(
        user and getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and getattr(user, "is_superuser", False)
        and getattr(user, "school_id", None) is None
    )


def platform_only(view):
    @wraps(view)
    def guarded(request, *args, **kwargs):
        if not is_crown_admin(getattr(request, "user", None)):
            return JsonResponse({"detail": "Platform operator access required."}, status=403)
        return view(request, *args, **kwargs)
    return guarded


def _canonical_school_id(request):
    try:
        return get_tenant_school_id(request, required=True)
    except PermissionError:
        return None


def _tenant_required_response():
    return JsonResponse(
        {"error": "Canonical school context is required", "code": "TENANT_REQUIRED"},
        status=400,
    )


def _body(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _module_key(body):
    key = body.get("module_key")
    return key if isinstance(key, str) and key in {k for k, _ in SchoolModule.MODULE_CHOICES} else None


def _duration(value, max_allowed):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    if isinstance(value, str) and not value.isdigit():
        return None
    days = int(value)
    return days if 1 <= days <= max_allowed else None


def _locked_school(school_id):
    return School.objects.select_for_update().filter(pk=school_id, is_active=True).first()


def _audit(request, school, module, previous_status, action):
    # State and expiry are operational facts, not receipts or approved prices.
    AuditEvent.objects.create(
        school_id=school.pk,
        actor_user_id=request.user.pk,
        action=action,
        resource_kind="SchoolModule",
        resource_id=module.pk,
        payload={
            "module_key": module.module_key,
            "previous_status": previous_status,
            "new_status": module.status,
            "expiry_date": module.expiry_date.isoformat() if module.expiry_date else None,
        },
    )


@platform_only
@require_http_methods(["GET"])
def list_school_modules(request):
    school_id = _canonical_school_id(request)
    if not school_id:
        return _tenant_required_response()
    if not School.objects.filter(pk=school_id, is_active=True).exists():
        return JsonResponse({"error": "Active school not found"}, status=404)

    module_map = get_school_modules(school_id)
    rows = []
    for mod in SchoolModule.objects.filter(school_id=school_id).select_related("activated_by"):
        rows.append({
            "module_key": mod.module_key,
            "module_label": mod.get_module_key_display(),
            "status": mod.status,
            "is_active": mod.is_active,
            "price_paid": str(mod.price_paid) if mod.price_paid is not None else None,
            "billing_cycle": mod.billing_cycle,
            "purchased_date": mod.purchased_date.isoformat() if mod.purchased_date else None,
            "expiry_date": mod.expiry_date.isoformat() if mod.expiry_date else None,
            "activated_by": mod.activated_by.email if mod.activated_by else None,
            "notes": mod.notes,
        })
    return JsonResponse({
        "school_id": str(school_id),
        "module_map": module_map,
        "modules": rows,
    })


@platform_only
@require_http_methods(["POST"])
@transaction.atomic
def activate_module(request):
    school_id = _canonical_school_id(request)
    if not school_id:
        return _tenant_required_response()
    body = _body(request)
    if body is None:
        return JsonResponse({"error": "JSON object required"}, status=400)
    key = _module_key(body)
    if not key:
        return JsonResponse({"error": "Valid module_key required"}, status=400)
    months = _duration(body.get("months", 12), max_allowed=36)
    if months is None:
        return JsonResponse({"error": "months must be an integer from 1 to 36"}, status=400)
    billing_cycle = body.get("billing_cycle", "annual")
    if billing_cycle not in {key for key, _ in SchoolModule.BILLING_CYCLE_CHOICES}:
        return JsonResponse({"error": "Invalid billing_cycle"}, status=400)
    if key in CARE_MODULES and "price_paid" in body:
        return JsonResponse({"error": "Care-module prices have not been approved; price_paid is unsupported"}, status=400)
    notes = body.get("notes", "")
    if not isinstance(notes, str) or len(notes) > 2000:
        return JsonResponse({"error": "notes must be text of at most 2000 characters"}, status=400)

    school = _locked_school(school_id)
    if school is None:
        return JsonResponse({"error": "Active school not found"}, status=404)
    module, created = SchoolModule.objects.get_or_create(school=school, module_key=key)
    old_status = module.status
    module.activate(activated_by_user=request.user, price_paid=body.get("price_paid"), months=months)
    module.billing_cycle = billing_cycle
    module.notes = notes
    module.save(update_fields=["billing_cycle", "notes", "updated_at"])
    _audit(request, school, module, old_status, "subscription.module_activated")
    return JsonResponse({
        "success": True,
        "module_key": key,
        "status": module.status,
        "expiry_date": module.expiry_date.isoformat(),
        "activated_by": request.user.email,
    }, status=201 if created else 200)


@platform_only
@require_http_methods(["POST"])
@transaction.atomic
def deactivate_module(request):
    school_id = _canonical_school_id(request)
    if not school_id:
        return _tenant_required_response()
    body = _body(request)
    if body is None:
        return JsonResponse({"error": "JSON object required"}, status=400)
    key = _module_key(body)
    if not key:
        return JsonResponse({"error": "Valid module_key required"}, status=400)
    school = _locked_school(school_id)
    if school is None:
        return JsonResponse({"error": "Active school not found"}, status=404)
    module = SchoolModule.objects.filter(school=school, module_key=key).first()
    if module is None:
        return JsonResponse({"error": "Module record not found for this school"}, status=404)
    old_status = module.status
    if old_status != "inactive":
        module.deactivate()
        _audit(request, school, module, old_status, "subscription.module_deactivated")
    return JsonResponse({"success": True, "module_key": key, "status": "inactive"})


@platform_only
@require_http_methods(["POST"])
@transaction.atomic
def start_trial(request):
    school_id = _canonical_school_id(request)
    if not school_id:
        return _tenant_required_response()
    body = _body(request)
    if body is None:
        return JsonResponse({"error": "JSON object required"}, status=400)
    key = _module_key(body)
    if not key:
        return JsonResponse({"error": "Valid module_key required"}, status=400)
    days = _duration(body.get("days", 30), max_allowed=30)
    if days is None:
        return JsonResponse({"error": "days must be an integer from 1 to 30"}, status=400)
    school = _locked_school(school_id)
    if school is None:
        return JsonResponse({"error": "Active school not found"}, status=404)
    module, _ = SchoolModule.objects.get_or_create(school=school, module_key=key)
    old_status = module.status
    module.start_trial(days=days)
    _audit(request, school, module, old_status, "subscription.module_trial_started")
    return JsonResponse({
        "success": True,
        "module_key": key,
        "status": "trial",
        "expiry_date": module.expiry_date.isoformat(),
    })
