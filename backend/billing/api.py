from __future__ import annotations

import json
from decimal import Decimal
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods

from households.scoping import get_request_school_id
from .models import BillingRun, Invoice, InvoiceLine
from .services import create_tuition_billing_run


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


def _run_to_dict(r: BillingRun):
    return {
        "id": str(r.id),
        "school_id": str(r.school_id),
        "term": r.term,
        "run_type": r.run_type,
        "description": r.description,
        "amount_per_student": str(r.amount_per_student),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@login_required
@require_http_methods(["GET", "POST"])
def billing_runs(request: HttpRequest):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    if request.method == "GET":
        qs = BillingRun.objects.filter(school_id=sid).order_by("-created_at")
        return _envelope([_run_to_dict(r) for r in qs], status=200)

    payload = _parse_json(request)
    if payload is None:
        return _json_error("Invalid JSON body", status=400)

    term = payload.get("term")
    amount = payload.get("amount_per_student")
    description = payload.get("description") or "Tuition Billing Run"

    if not term:
        return _json_error("term is required", status=400)
    if amount is None:
        return _json_error("amount_per_student is required", status=400)

    try:
        amt = Decimal(str(amount))
    except Exception:
        return _json_error("amount_per_student must be a decimal", status=400)

    try:
        result = create_tuition_billing_run(
            school_id=sid,
            term=str(term),
            amount_per_student=amt,
            description=str(description),
        )
    except ValueError as e:
        return _json_error(str(e), status=400)

    run = BillingRun.objects.get(id=result.billing_run_id, school_id=sid)
    return _envelope(
        {
            "billing_run": _run_to_dict(run),
            "invoices_created": result.invoices_created,
            "students_billed": result.students_billed,
            "total_amount": str(result.total_amount),
        },
        status=201,
    )


@login_required
@require_http_methods(["GET"])
def billing_run_detail(request: HttpRequest, billing_run_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    try:
        run = BillingRun.objects.get(id=UUID(billing_run_id), school_id=sid)
    except BillingRun.DoesNotExist:
        return _json_error("Not found", status=404)

    invoices = (
        Invoice.objects.filter(school_id=sid, billing_run=run)
        .prefetch_related("lines")
        .order_by("created_at")
    )

    data = _run_to_dict(run)
    data["invoices"] = []
    for inv in invoices:
        data["invoices"].append(
            {
                "id": str(inv.id),
                "household_id": str(inv.household_id),
                "total_amount": str(inv.total_amount),
                "ledger_charge_id": str(inv.ledger_charge_id) if inv.ledger_charge_id else None,
                "lines": [
                    {
                        "id": str(line.id),
                        "student_id": str(line.student_id),
                        "description": line.description,
                        "amount": str(line.amount),
                    }
                    for line in inv.lines.all()
                ],
            }
        )

    return _envelope(data, status=200)
