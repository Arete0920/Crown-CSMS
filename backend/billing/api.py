from __future__ import annotations

import json
import logging
from decimal import Decimal
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum
from django.utils import timezone

from households.scoping import get_request_school_id
from .models import BillingRun, Invoice, InvoiceLine, InstallmentPlan
from .reconciliation import compute_invoice_balance_due
from .services import create_tuition_billing_run
from crown_api.billing_api.permissions import has_finance_runtime_role
from ledger.services import billing_run_summary
from ledger.models import Allocation, Charge


logger = logging.getLogger(__name__)


def _plan_to_dict(p: InstallmentPlan):
    return {
        "id": str(p.id),
        "school_id": str(p.school_id),
        "term": p.term,
        "name": p.name,
        "installment_count": int(p.installment_count),
        "first_due_on": p.first_due_on.isoformat() if p.first_due_on else None,
        "cadence_days": int(p.cadence_days),
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def installment_plans(request: HttpRequest):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    if request.method == "GET":
        qs = InstallmentPlan.objects.filter(school_id=sid).order_by("term", "name", "created_at")
        return _envelope([_plan_to_dict(p) for p in qs], status=200)

    payload = _parse_json(request)
    if payload is None:
        return _json_error("Invalid JSON body", status=400)

    term = payload.get("term")
    name = payload.get("name")
    installment_count = payload.get("installment_count")
    first_due_on = payload.get("first_due_on")
    cadence_days = payload.get("cadence_days")

    if not term:
        return _json_error("term is required", status=400)
    if not name:
        return _json_error("name is required", status=400)
    if installment_count is None:
        return _json_error("installment_count is required", status=400)
    if not first_due_on:
        return _json_error("first_due_on is required", status=400)

    try:
        installment_count_i = int(installment_count)
    except Exception:
        return _json_error("installment_count must be an int", status=400)
    if installment_count_i <= 0:
        return _json_error("installment_count must be > 0", status=400)

    try:
        from datetime import date

        due = date.fromisoformat(str(first_due_on))
    except Exception:
        return _json_error("first_due_on must be YYYY-MM-DD", status=400)

    if cadence_days is None:
        cadence_days_i = 30
    else:
        try:
            cadence_days_i = int(cadence_days)
        except Exception:
            return _json_error("cadence_days must be an int", status=400)
        if cadence_days_i <= 0:
            return _json_error("cadence_days must be > 0", status=400)

    p = InstallmentPlan.objects.create(
        school_id=sid,
        term=str(term)[:24],
        name=str(name)[:120],
        installment_count=installment_count_i,
        first_due_on=due,
        cadence_days=cadence_days_i,
    )
    return _envelope(_plan_to_dict(p), status=201)


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


def _aging_bucket(days_past_due: int) -> str:
    if days_past_due <= 0:
        return "current"
    if days_past_due <= 30:
        return "0-30"
    if days_past_due <= 60:
        return "31-60"
    if days_past_due <= 90:
        return "61-90"
    return "90+"


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


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
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
    installment_plan_id = payload.get("installment_plan_id")

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
            installment_plan_id=(UUID(str(installment_plan_id)) if installment_plan_id else None),
        )
    except ValueError:
        logger.warning("billing_runs: invalid billing run payload", extra={"school_id": str(sid)})
        return _json_error("Unable to create billing run with the provided inputs.", status=400)

    run = BillingRun.objects.get(pk=result.billing_run_id, school_id=sid)
    return _envelope(
        {
            "billing_run": _run_to_dict(run),
            "invoices_created": result.invoices_created,
            "students_billed": result.students_billed,
            "total_amount": str(result.total_amount),
        },
        status=201,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def billing_run_detail(request: HttpRequest, billing_run_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    try:
        run = BillingRun.objects.get(pk=UUID(billing_run_id), school_id=sid)
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
        from django.db.models import Sum
        from ledger.models import Allocation as PaymentAllocation

        aid_applied = Decimal("0.00")
        if inv.ledger_charge_id:
            aid_applied = (
                PaymentAllocation.objects.filter(
                    school_id=sid,
                    charge_id=inv.ledger_charge_id,
                    payment__source="FINANCIAL_AID",
                ).aggregate(total=Sum("amount"))["total"]
                or Decimal("0.00")
            )

        net_due = Decimal(str(inv.total_amount)) - Decimal(str(aid_applied))
        if net_due < Decimal("0.00"):
            net_due = Decimal("0.00")

        data["invoices"].append(
            {
                "id": str(inv.id),
                "household_id": str(inv.household_id),
                "total_amount": str(inv.total_amount),
                "aid_applied": str(aid_applied),
                "net_due": str(net_due),
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def billing_run_summary_view(request: HttpRequest, billing_run_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    try:
        run = BillingRun.objects.get(pk=UUID(billing_run_id), school_id=sid)
    except BillingRun.DoesNotExist:
        return _json_error("Not found", status=404)

    data = billing_run_summary(school_id=sid, billing_run=run)
    return _envelope(data, status=200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def invoices(request):
    """
    School-wide invoice list.
    This is intentionally finance/admin-only until the family-scoped account
    page is built.
    """
    if not has_finance_runtime_role(request.user):
        return Response(
            {"detail": "You do not have permission to view school-wide invoices."},
            status=403,
        )

    sid = get_request_school_id(request, required=True)

    qs = (
        Invoice.objects
        .filter(school_id=sid)
        .select_related("household")
        .order_by("-created_at")
    )

    invoice_rows = list(qs[:2000])  # safety cap for demo; adjust later
    charge_ids = [
        inv.ledger_charge_id
        for inv in invoice_rows
        if getattr(inv, "ledger_charge_id", None)
    ]

    paid_by_charge = {}
    voided_charge_ids = set()

    if charge_ids:
        paid_rows = (
            Allocation.objects
            .filter(school_id=sid, charge_id__in=charge_ids)
            .values("charge_id")
            .annotate(paid=Sum("amount"))
        )
        paid_by_charge = {row["charge_id"]: Decimal(str(row["paid"] or "0.00")) for row in paid_rows}

        voided_charge_ids = set(
            Charge.objects
            .filter(school_id=sid, id__in=charge_ids, is_void=True)
            .values_list("id", flat=True)
        )

    data = []
    today = timezone.localdate()
    for inv in invoice_rows:
        total_amount = Decimal(str(inv.total_amount or "0.00"))
        paid_amount = paid_by_charge.get(inv.ledger_charge_id, Decimal("0.00"))
        balance_due = compute_invoice_balance_due(inv)
        if inv.ledger_charge_id in voided_charge_ids:
            balance_due = Decimal("0.00")
        if balance_due < Decimal("0.00"):
            balance_due = Decimal("0.00")

        credit_amount = paid_amount - total_amount
        if credit_amount < Decimal("0.00"):
            credit_amount = Decimal("0.00")

        due_on = inv.due_on
        days_past_due = 0
        if due_on and balance_due > Decimal("0.00"):
            days_past_due = max((today - due_on).days, 0)

        bucket = _aging_bucket(days_past_due)
        is_delinquent = days_past_due > 0

        data.append(
            {
                "id": str(inv.id),
                "household_id": str(inv.household_id) if inv.household_id else None,
                "household_name": inv.household.name if inv.household_id else None,
                "total_amount": str(total_amount),
                "due_on": due_on.isoformat() if due_on else None,
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
                "updated_at": inv.updated_at.isoformat() if inv.updated_at else None,
                "balance_due": str(balance_due),
                "paid_amount": str(paid_amount),
                "credit_amount": str(credit_amount),
                "days_past_due": days_past_due,
                "aging_bucket": bucket,
                "is_delinquent": is_delinquent,
                "is_reversed": inv.ledger_charge_id in voided_charge_ids,
            }
        )

    return Response({"results": data})
