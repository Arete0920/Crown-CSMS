from __future__ import annotations

import json
from decimal import Decimal
from uuid import UUID
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods

from households.models import Household
from households.scoping import get_request_school_id
from .models import AidApplication, AidAward
from .services import submit_aid_application, decide_aid_application, create_disbursement


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


def _app_to_dict(a: AidApplication):
    return {
        "id": str(a.id),
        "school_id": str(a.school_id),
        "household_id": str(a.household_id),
        "academic_year": a.academic_year,
        "status": a.status,
        "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
        "decided_at": a.decided_at.isoformat() if a.decided_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


def _award_to_dict(w: AidAward):
    return {
        "id": str(w.id),
        "school_id": str(w.school_id),
        "aid_application_id": str(w.aid_application_id),
        "status": w.status,
        "amount_annual": str(w.amount_annual),
        "created_at": w.created_at.isoformat() if w.created_at else None,
    }


@login_required
@require_http_methods(["GET", "POST"])
def aid_applications(request: HttpRequest):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    if request.method == "GET":
        qs = AidApplication.objects.filter(school_id=sid).order_by("-created_at")
        return _envelope([_app_to_dict(a) for a in qs], status=200)

    payload = _parse_json(request)
    if payload is None:
        return _json_error("Invalid JSON body", status=400)

    household_id = payload.get("household_id")
    academic_year = payload.get("academic_year")

    if not household_id:
        return _json_error("household_id is required", status=400)
    if not academic_year:
        return _json_error("academic_year is required", status=400)

    # no-leak: ensure household is in-scope
    try:
        hh = Household.objects.get(id=UUID(str(household_id)), school_id=sid)
    except Household.DoesNotExist:
        return _json_error("Not found", status=404)

    app = AidApplication.objects.create(
        school_id=sid,
        household=hh,
        academic_year=str(academic_year)[:16],
    )
    return _envelope(_app_to_dict(app), status=201)


@login_required
@require_http_methods(["POST"])
def aid_submit(request: HttpRequest, aid_application_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    try:
        app = AidApplication.objects.get(id=UUID(aid_application_id), school_id=sid)
    except AidApplication.DoesNotExist:
        return _json_error("Not found", status=404)

    try:
        submit_aid_application(app)
    except ValueError as e:
        return _json_error(str(e), status=400)

    return _envelope(_app_to_dict(app), status=200)


@login_required
@require_http_methods(["POST"])
def aid_decide(request: HttpRequest, aid_application_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    payload = _parse_json(request)
    if payload is None:
        return _json_error("Invalid JSON body", status=400)

    decision = payload.get("decision")
    amount = payload.get("amount_annual")

    try:
        app = AidApplication.objects.get(id=UUID(aid_application_id), school_id=sid)
    except AidApplication.DoesNotExist:
        return _json_error("Not found", status=404)

    amt = None
    if amount is not None:
        try:
            amt = Decimal(str(amount))
        except Exception:
            return _json_error("amount_annual must be a decimal", status=400)

    try:
        award = decide_aid_application(app, decision=decision, amount_annual=amt)
    except ValueError as e:
        return _json_error(str(e), status=400)

    return _envelope({"application": _app_to_dict(app), "award": _award_to_dict(award)}, status=200)


@login_required
@require_http_methods(["POST"])
def aid_disburse(request: HttpRequest, award_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    payload = _parse_json(request)
    if payload is None:
        return _json_error("Invalid JSON body", status=400)

    amount = payload.get("amount")
    disbursed_on = payload.get("disbursed_on")

    if amount is None:
        return _json_error("amount is required", status=400)
    if not disbursed_on:
        return _json_error("disbursed_on is required (YYYY-MM-DD)", status=400)

    try:
        award = AidAward.objects.select_related("aid_application").get(id=UUID(award_id), school_id=sid)
    except AidAward.DoesNotExist:
        return _json_error("Not found", status=404)

    try:
        amt = Decimal(str(amount))
    except Exception:
        return _json_error("amount must be a decimal", status=400)

    try:
        d = date.fromisoformat(str(disbursed_on))
    except Exception:
        return _json_error("disbursed_on must be YYYY-MM-DD", status=400)

    try:
        disb = create_disbursement(award, amount=amt, disbursed_on=d)
    except ValueError as e:
        return _json_error(str(e), status=400)

    return _envelope(
        {"award_id": str(award.id), "amount": str(disb.amount), "disbursed_on": str(disb.disbursed_on)},
        status=201,
    )
