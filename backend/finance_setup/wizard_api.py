"""
finance_setup.wizard_api
========================
Four thin view functions — all side-effect logic lives in services.py.

GET  /api/v1/finance-setup/wizard/status/     -> current policy (or 404 if not created)
POST /api/v1/finance-setup/wizard/configure/  -> upsert full policy (409 if locked)
POST /api/v1/finance-setup/wizard/lock/       -> permanently lock a year
GET  /api/v1/finance-setup/wizard/snapshot/   -> alias for status (read-only presentation)
"""

import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .serializers import FinancePolicySnapshotSerializer, FinanceSetupWizardPayloadSerializer
from .services import PolicyLockedError, get_policy_snapshot, lock_finance_policies, upsert_finance_policies
from .tenant import school_id_from_request

logger = logging.getLogger(__name__)


def _json_body(request):
    import json

    try:
        return json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return None


@csrf_exempt
@require_http_methods(["GET"])
def wizard_status(request):
    """
    Return the current finance policy snapshot for the requesting school + academic_year.
    academic_year is passed as a query param: ?year=2026-2027
    """
    school_id = school_id_from_request(request)
    academic_year = request.GET.get("year", "").strip()

    if not academic_year:
        return JsonResponse({"error": "year query param required (e.g. ?year=2026-2027)"}, status=400)

    version = get_policy_snapshot(school_id=school_id, academic_year=academic_year)

    if version is None:
        return JsonResponse(
            {"status": "not_configured", "academic_year": academic_year},
            status=404,
        )

    data = FinancePolicySnapshotSerializer(version).data
    return JsonResponse({"status": "ok", "data": data})


@csrf_exempt
@require_http_methods(["POST"])
def wizard_configure(request):
    """
    Create or update the full finance policy.
    Returns 409 if the policy is already locked for that school+year.
    """
    school_id = school_id_from_request(request)
    body = _json_body(request)

    if body is None:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    ser = FinanceSetupWizardPayloadSerializer(data=body)
    if not ser.is_valid():
        return JsonResponse({"error": "Validation failed.", "details": ser.errors}, status=422)

    academic_year = ser.validated_data["academic_year"]

    try:
        version = upsert_finance_policies(
            school_id=school_id,
            academic_year=academic_year,
            payload=ser.validated_data,
        )
    except PolicyLockedError:
        logger.warning("configure blocked — locked: school=%s year=%s", school_id, academic_year)
        return JsonResponse({"error": "Policy is locked for this academic year."}, status=409)

    snapshot = get_policy_snapshot(school_id=school_id, academic_year=academic_year)
    data = FinancePolicySnapshotSerializer(snapshot).data
    return JsonResponse({"status": "saved", "data": data}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def wizard_lock(request):
    """
    Permanently lock the finance policy for a given school + academic_year.
    Idempotent: calling on an already-locked policy returns 200.
    """
    school_id = school_id_from_request(request)
    body = _json_body(request)

    if body is None:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    academic_year = (body.get("academic_year") or "").strip()
    locked_by = (body.get("locked_by") or "").strip() or None

    if not academic_year:
        return JsonResponse({"error": "academic_year is required."}, status=400)

    try:
        version = lock_finance_policies(
            school_id=school_id,
            academic_year=academic_year,
            locked_by=locked_by,
        )
    except ValueError:
        logger.warning("wizard_lock failed — missing finance policy snapshot: school=%s year=%s", school_id, academic_year)
        return JsonResponse({"error": "Finance policy snapshot not found for this academic year."}, status=404)

    return JsonResponse(
        {
            "status": "locked",
            "academic_year": version.academic_year,
            "locked_at": version.locked_at.isoformat() if version.locked_at else None,
            "locked_by": version.locked_by,
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
def wizard_snapshot(request):
    """
    Read-only alias for wizard_status — returns complete denormalized snapshot.
    Used by reporting surfaces and export pipelines.
    """
    return wizard_status(request)
