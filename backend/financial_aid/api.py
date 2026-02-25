from __future__ import annotations

import json
from decimal import Decimal
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods

from households.scoping import get_request_school_id
from .models import FinancialAidApplication, AidAward
from .services import apply_financial_aid_to_billing_run


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"ok": False, "error": {"message": message}}, status=status)


def _envelope(data, status: int = 200) -> JsonResponse:
    return JsonResponse({"ok": True, "data": data}, status=status, safe=False)


def _parse_json(request: HttpRequest):
    try:
        if not request.body:
            return {}
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


def _app_to_dict(a: FinancialAidApplication) -> dict:
    return {
        "id": str(a.id),
        "school_id": str(a.school_id),
        "household_id": str(a.household_id),
        "academic_year": a.academic_year,
        "status": a.status,
        "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
        "household_income": str(a.household_income) if a.household_income is not None else None,
        "household_size": a.household_size,
    }


def _award_to_dict(w: AidAward) -> dict:
    return {
        "id": str(w.id),
        "school_id": str(w.school_id),
        "bucket": w.bucket,
        "amount": str(w.amount),
        "rationale": w.rationale,
        "approved_by_user_id": str(w.approved_by_user_id) if w.approved_by_user_id else None,
        "application_id": str(w.application_id) if w.application_id else None,
        "created_at": w.created_at.isoformat() if w.created_at else None,
        "updated_at": w.updated_at.isoformat() if w.updated_at else None,
    }


@login_required
@require_http_methods(["GET"])
def aid_applications(request: HttpRequest):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    qs = FinancialAidApplication.objects.filter(school_id=sid).order_by("-submitted_at")
    return _envelope([_app_to_dict(a) for a in qs], status=200)


@login_required
@require_http_methods(["GET"])
def aid_awards(request: HttpRequest):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    qs = AidAward.objects.filter(school_id=sid).select_related("application").order_by("-created_at")
    return _envelope([_award_to_dict(w) for w in qs], status=200)


@login_required
@require_http_methods(["POST"])
def disburse_to_billing_run(request: HttpRequest, billing_run_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    try:
        result = apply_financial_aid_to_billing_run(
            school_id=sid,
            billing_run_id=UUID(billing_run_id),
        )
    except Exception as e:
        return _json_error(str(e), status=400)

    return _envelope(result, status=200)
