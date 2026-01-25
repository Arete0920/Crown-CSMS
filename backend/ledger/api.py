from __future__ import annotations

import json
from decimal import Decimal
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods

from households.models import Household
from households.scoping import get_request_school_id
from .models import Payment, PaymentAllocation, Charge, LedgerAccount
from .models import Allocation, compute_account_balance
from .services import allocate_payment_fifo, account_balance, charge_remaining_balance
from .services import build_account_statement


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


def _acct_to_dict(a: LedgerAccount):
    return {
        "id": str(a.id),
        "school_id": str(a.school_id),
        "household_id": str(a.household_id),
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        "balance": str(compute_account_balance(a)),
    }


def _charge_to_dict(c: Charge):
    return {
        "id": str(c.id),
        "school_id": str(c.school_id),
        "account_id": str(c.account_id),
        "description": c.description,
        "amount": str(c.amount),
        "is_void": c.is_void,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _payment_to_dict(p: Payment):
    return {
        "id": str(p.id),
        "school_id": str(p.school_id),
        "account_id": str(p.account_id),
        "reference": p.reference,
        "amount": str(p.amount),
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


@login_required
@require_http_methods(["POST"])
def ensure_account(request: HttpRequest):
    """
    Create the household's ledger account if missing.
    Body: { "household_id": "<uuid>" }
    """
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    payload = _parse_json(request)
    if payload is None:
        return _json_error("Invalid JSON body", status=400)

    household_id = payload.get("household_id")
    if not household_id:
        return _json_error("household_id is required", status=400)

    # no-leak: ensure household is in-scope
    try:
        hh = Household.objects.get(id=UUID(str(household_id)), school_id=sid)
    except Household.DoesNotExist:
        return _json_error("Not found", status=404)

    acct, _created = LedgerAccount.objects.get_or_create(
        school_id=sid,
        household=hh,
        defaults={},
    )
    return _envelope(_acct_to_dict(acct), status=200)


@login_required
@require_http_methods(["GET"])
def account_detail(request: HttpRequest, account_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    try:
        acct = LedgerAccount.objects.get(id=UUID(account_id), school_id=sid)
    except LedgerAccount.DoesNotExist:
        return _json_error("Not found", status=404)

    data = _acct_to_dict(acct)
    charges = Charge.objects.filter(account=acct, school_id=sid).order_by("-created_at")
    payments = Payment.objects.filter(account=acct, school_id=sid).order_by("-created_at")

    data["charges"] = [_charge_to_dict(c) for c in charges]
    data["payments"] = [_payment_to_dict(p) for p in payments]

    return _envelope(data, status=200)


@login_required
@require_http_methods(["POST"])
def create_charge(request: HttpRequest):
    """
    Body: { "account_id": "<uuid>", "description": "...", "amount": "123.45" }
    """
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    payload = _parse_json(request)
    if payload is None:
        return _json_error("Invalid JSON body", status=400)

    account_id = payload.get("account_id")
    description = payload.get("description") or ""
    amount = payload.get("amount")

    if not account_id:
        return _json_error("account_id is required", status=400)
    if not description.strip():
        return _json_error("description is required", status=400)
    if amount is None:
        return _json_error("amount is required", status=400)

    try:
        acct = LedgerAccount.objects.get(id=UUID(str(account_id)), school_id=sid)
    except LedgerAccount.DoesNotExist:
        return _json_error("Not found", status=404)

    try:
        amt = Decimal(str(amount))
    except Exception:
        return _json_error("amount must be a decimal", status=400)

    c = Charge.objects.create(
        school_id=sid,
        account=acct,
        description=description.strip(),
        amount=amt,
    )
    return _envelope(_charge_to_dict(c), status=201)


@login_required
@require_http_methods(["POST"])
def record_payment(request: HttpRequest):
    """
    Body: {
      "account_id": "<uuid>",
      "reference": "...",
      "amount": "123.45",
      "allocations": [{"charge_id":"<uuid>","amount":"10.00"}, ...]
    }
    allocations are optional.
    """
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    payload = _parse_json(request)
    if payload is None:
        return _json_error("Invalid JSON body", status=400)

    account_id = payload.get("account_id")
    amount = payload.get("amount")
    reference = payload.get("reference") or ""

    if not account_id:
        return _json_error("account_id is required", status=400)
    if amount is None:
        return _json_error("amount is required", status=400)

    try:
        acct = LedgerAccount.objects.get(id=UUID(str(account_id)), school_id=sid)
    except LedgerAccount.DoesNotExist:
        return _json_error("Not found", status=404)

    try:
        amt = Decimal(str(amount))
    except Exception:
        return _json_error("amount must be a decimal", status=400)

    p = Payment.objects.create(
        school_id=sid,
        account=acct,
        reference=str(reference)[:64],
        amount=amt,
    )

    allocs = payload.get("allocations") or []
    for item in allocs:
        charge_id = item.get("charge_id")
        a_amount = item.get("amount")
        if not charge_id or a_amount is None:
            continue

        try:
            ch = Charge.objects.get(id=UUID(str(charge_id)), school_id=sid, account=acct)
        except Charge.DoesNotExist:
            continue

        try:
            a_amt = Decimal(str(a_amount))
        except Exception:
            continue

        Allocation.objects.create(
            school_id=sid,
            payment=p,
            charge=ch,
            amount=a_amt,
        )

    return _envelope(_payment_to_dict(p), status=201)


@login_required
@require_http_methods(["POST"])
def payment_allocate(request: HttpRequest, payment_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    try:
        p = Payment.objects.select_related("account").get(id=UUID(payment_id), school_id=sid)
    except Payment.DoesNotExist:
        return _json_error("Not found", status=404)

    try:
        result = allocate_payment_fifo(school_id=sid, payment=p)
    except ValueError as e:
        return _json_error(str(e), status=400)

    return _envelope(
        {
            "payment_id": str(result.payment_id),
            "allocated_total": str(result.allocated_total),
            "remaining_unallocated": str(result.remaining_unallocated),
            "allocations_created": result.allocations_created,
        },
        status=200,
    )


@login_required
@require_http_methods(["GET"])
def ledger_account_balance(request: HttpRequest, account_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    try:
        acct = LedgerAccount.objects.get(id=UUID(account_id), school_id=sid)
    except LedgerAccount.DoesNotExist:
        return _json_error("Not found", status=404)

    bal = account_balance(acct)
    return _envelope({"account_id": str(acct.id), "balance": str(bal)}, status=200)


@login_required
@require_http_methods(["GET"])
def charge_balance(request: HttpRequest, charge_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    try:
        ch = Charge.objects.get(id=UUID(charge_id), school_id=sid)
    except Charge.DoesNotExist:
        return _json_error("Not found", status=404)

    rem = charge_remaining_balance(ch)
    return _envelope({"charge_id": str(ch.id), "remaining_balance": str(rem)}, status=200)


@login_required
@require_http_methods(["GET"])
def ledger_account_statement(request: HttpRequest, account_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    try:
        acct = LedgerAccount.objects.get(id=UUID(account_id), school_id=sid)
    except LedgerAccount.DoesNotExist:
        return _json_error("Not found", status=404)

    data = build_account_statement(school_id=sid, account=acct)
    return _envelope(data, status=200)
