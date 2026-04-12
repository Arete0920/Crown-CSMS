from __future__ import annotations

import json
from decimal import Decimal
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.db import transaction

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods

from households.models import Household
from households.scoping import get_request_school_id
from core.models import UserRole
from .models import Payment, PaymentAllocation, Charge, LedgerAccount
from .models import Allocation, compute_account_balance
from .services import allocate_payment_fifo, account_balance, charge_remaining_balance
from .services import build_account_statement


LedgerOpenChargeItemSerializer = inline_serializer(
    name="LedgerOpenChargeItemSerializer",
    fields={
        "charge": serializers.DictField(),
        "remaining_balance": serializers.CharField(),
        "invoice": serializers.DictField(required=False, allow_null=True),
    },
)
LedgerOpenChargeEnvelopeSerializer = inline_serializer(
    name="LedgerOpenChargeEnvelopeSerializer",
    fields={
        "ok": serializers.BooleanField(),
        "data": serializers.ListField(child=serializers.DictField()),
    },
)
LedgerOpenInvoiceItemSerializer = inline_serializer(
    name="LedgerOpenInvoiceItemSerializer",
    fields={
        "invoice_id": serializers.CharField(),
        "household_id": serializers.CharField(),
        "due_on": serializers.CharField(allow_null=True),
        "total_amount": serializers.CharField(),
        "ledger_charge_id": serializers.CharField(),
        "paid_amount": serializers.CharField(),
        "balance": serializers.CharField(),
    },
)
LedgerOpenInvoiceEnvelopeSerializer = inline_serializer(
    name="LedgerOpenInvoiceEnvelopeSerializer",
    fields={
        "ok": serializers.BooleanField(),
        "data": serializers.ListField(child=serializers.DictField()),
    },
)
LedgerEnvelopeSerializer = inline_serializer(
    name="LedgerEnvelopeSerializer",
    fields={
        "ok": serializers.BooleanField(),
        "data": serializers.DictField(),
    },
)
LedgerEnsureAccountRequestSerializer = inline_serializer(
    name="LedgerEnsureAccountRequestSerializer",
    fields={"household_id": serializers.CharField()},
)
LedgerCreateChargeRequestSerializer = inline_serializer(
    name="LedgerCreateChargeRequestSerializer",
    fields={
        "account_id": serializers.CharField(),
        "description": serializers.CharField(),
        "amount": serializers.CharField(),
    },
)
LedgerPaymentAllocationRequestSerializer = inline_serializer(
    name="LedgerPaymentAllocationRequestSerializer",
    fields={
        "charge_id": serializers.CharField(),
        "amount": serializers.CharField(),
    },
)
LedgerRecordPaymentRequestSerializer = inline_serializer(
    name="LedgerRecordPaymentRequestSerializer",
    fields={
        "account_id": serializers.CharField(required=False),
        "household_id": serializers.CharField(required=False),
        "reference": serializers.CharField(required=False, allow_blank=True),
        "payment_reference": serializers.CharField(required=False, allow_blank=True),
        "source": serializers.CharField(required=False, allow_blank=True),
        "amount": serializers.CharField(),
        "payment_date": serializers.CharField(required=False, allow_blank=True),
        "allocations": serializers.ListField(child=LedgerPaymentAllocationRequestSerializer, required=False),
        "allow_partial": serializers.BooleanField(required=False),
        "allow_overpay": serializers.BooleanField(required=False),
    },
)

SCHOOL_CONTEXT_ERROR = "school_id could not be derived for request"
INVALID_JSON_BODY_ERROR = "Invalid JSON body"
NOT_FOUND_ERROR = "Not found"
INVALID_REQUEST_PAYLOAD_ERROR = "Invalid request payload"


def _get_account_for_scope(*, sid, account_id: str | None, household_id: str | None):
    acct = None
    if account_id:
        acct = LedgerAccount.objects.get(pk=_parse_uuid(account_id, "account_id"), school_id=sid)
    if household_id:
        hh = Household.objects.get(pk=_parse_uuid(household_id, "household_id"), school_id=sid)
        acct2, _ = LedgerAccount.objects.get_or_create(school_id=sid, household=hh)
        if acct is not None and acct.id != acct2.id:
            raise ValueError("account_id does not match household_id")
        acct = acct2
    return acct


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"ok": False, "error": {"message": message}}, status=status)


def _envelope(data, status: int = 200) -> JsonResponse:
    return JsonResponse({"ok": True, "data": data}, status=status, safe=False)


def _parse_json(request: HttpRequest):
    # Handle both DRF Request (request.data) and plain Django HttpRequest (request.body)
    if hasattr(request, "data") and isinstance(request.data, dict):
        return request.data
    try:
        if not request.body:
            return {}
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return None


def _parse_uuid(value, field_name: str):
    if value in (None, ""):
        raise ValueError(f"{field_name} is required")
    try:
        return UUID(str(value))
    except Exception:
        raise ValueError(f"{field_name} must be a uuid")


def _parse_decimal(value, field_name: str) -> Decimal:
    if value is None or value == "":
        raise ValueError(f"{field_name} is required")
    try:
        return Decimal(str(value))
    except Exception:
        raise ValueError(f"{field_name} must be a decimal")


def _resolve_payment_account(*, sid, account_id: str | None, household_id: str | None):
    try:
        acct = _get_account_for_scope(sid=sid, account_id=account_id, household_id=household_id)
    except (Household.DoesNotExist, LedgerAccount.DoesNotExist):
        return None, _json_error(NOT_FOUND_ERROR, status=404)
    except ValueError:
        return None, _json_error(INVALID_REQUEST_PAYLOAD_ERROR, status=400)

    if acct is None:
        return None, _json_error(NOT_FOUND_ERROR, status=404)
    return acct, None


def _aggregate_requested_allocations(allocations_input) -> dict[UUID, Decimal]:
    requested_by_charge: dict[UUID, Decimal] = {}
    for item in allocations_input:
        if not isinstance(item, dict):
            raise ValueError("allocations must be objects")
        charge_id = _parse_uuid(item.get("charge_id"), "charge_id")
        amount = _parse_decimal(item.get("amount"), "allocation.amount")
        if amount <= Decimal("0"):
            raise ValueError("allocation.amount must be > 0")
        requested_by_charge[charge_id] = requested_by_charge.get(charge_id, Decimal("0")) + amount
    return requested_by_charge


def _validate_allocation_totals(*, requested_by_charge: dict[UUID, Decimal], amount: Decimal, allow_partial: bool):
    if not requested_by_charge:
        return None

    total_requested = sum(requested_by_charge.values(), Decimal("0"))
    if total_requested > amount:
        return _json_error("allocations total exceeds payment amount", status=400)
    if (not allow_partial) and total_requested != amount:
        return _json_error("allocations total must equal payment amount (or set allow_partial=true)", status=400)
    return None


def _resolve_charge_allocations(*, sid, acct, requested_by_charge: dict[UUID, Decimal], allow_overpay: bool):
    resolved_allocations = []
    for charge_id, amount in requested_by_charge.items():
        try:
            charge = Charge.objects.get(pk=charge_id, school_id=sid, account=acct)
        except Charge.DoesNotExist:
            return None, _json_error("charge not found", status=404)

        if getattr(charge, "is_void", False):
            return None, _json_error("cannot allocate to void charge", status=400)

        if not allow_overpay and amount > charge_remaining_balance(charge):
            return None, _json_error("allocation exceeds charge remaining balance", status=400)

        resolved_allocations.append((charge, amount))
    return resolved_allocations, None


def _create_allocations(*, sid, payment, resolved_allocations):
    created_allocations = []
    for charge, amount in resolved_allocations:
        alloc, created = Allocation.objects.get_or_create(
            school_id=sid,
            payment=payment,
            charge=charge,
            defaults={"amount": amount},
        )
        if not created:
            alloc.amount = Decimal(str(alloc.amount)) + amount
            alloc.save(update_fields=["amount"])

        created_allocations.append(
            {
                "id": str(alloc.id),
                "charge_id": str(alloc.charge_id),
                "amount": str(alloc.amount),
            }
        )
    return created_allocations


def _build_invoice_lookup(*, sid, charge_ids):
    invoice_by_charge = {}
    try:
        from billing.models import Invoice
    except Exception:
        return invoice_by_charge

    if not charge_ids:
        return invoice_by_charge

    for inv in Invoice.objects.filter(school_id=sid, ledger_charge_id__in=charge_ids).iterator():
        invoice_by_charge[str(inv.ledger_charge_id)] = {
            "invoice_id": str(inv.id),
            "due_on": inv.due_on.isoformat() if inv.due_on else None,
            "total_amount": str(inv.total_amount),
        }
    return invoice_by_charge


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
        "source": getattr(p, "source", "EXTERNAL"),
        "reference": p.reference,
        "amount": str(p.amount),
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


@extend_schema(request=LedgerEnsureAccountRequestSerializer, responses=LedgerEnvelopeSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
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
        hh = Household.objects.get(pk=UUID(str(household_id)), school_id=sid)
    except Household.DoesNotExist:
        return _json_error(NOT_FOUND_ERROR, status=404)

    acct, _created = LedgerAccount.objects.get_or_create(
        school_id=sid,
        household=hh,
        defaults={},
    )
    return _envelope(_acct_to_dict(acct), status=200)


@extend_schema(responses=LedgerEnvelopeSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def account_detail(request: HttpRequest, account_id: str):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error(SCHOOL_CONTEXT_ERROR, status=403)

    try:
        acct = LedgerAccount.objects.get(pk=UUID(account_id), school_id=sid)
    except LedgerAccount.DoesNotExist:
        return _json_error(NOT_FOUND_ERROR, status=404)

    data = _acct_to_dict(acct)
    charges = Charge.objects.filter(account=acct, school_id=sid).order_by("-created_at")
    payments = Payment.objects.filter(account=acct, school_id=sid).order_by("-created_at")

    data["charges"] = [_charge_to_dict(c) for c in charges]
    data["payments"] = [_payment_to_dict(p) for p in payments]

    return _envelope(data, status=200)


@extend_schema(request=LedgerCreateChargeRequestSerializer, responses={201: LedgerEnvelopeSerializer})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_charge(request: HttpRequest):
    sid = get_request_school_id(request)
    if not sid:
        return _json_error(SCHOOL_CONTEXT_ERROR, status=403)

    payload = _parse_json(request)
    if payload is None:
        return _json_error(INVALID_JSON_BODY_ERROR, status=400)

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
        acct = LedgerAccount.objects.get(pk=UUID(str(account_id)), school_id=sid)
    except LedgerAccount.DoesNotExist:
        return _json_error(NOT_FOUND_ERROR, status=404)

    try:
        amt = Decimal(str(amount))
    except Exception:
        return _json_error("amount must be a decimal", status=400)

    # Write-safety guard: charges must be positive (negative/zero charges corrupt the ledger).
    if amt <= Decimal("0"):
        return _json_error("amount must be > 0", status=400)

    with transaction.atomic():
        c = Charge.objects.create(
            school_id=sid,
            account=acct,
            description=description.strip(),
            amount=amt,
        )
    return _envelope(_charge_to_dict(c), status=201)


@extend_schema(request=LedgerRecordPaymentRequestSerializer, responses={201: LedgerEnvelopeSerializer})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
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
        return _json_error(SCHOOL_CONTEXT_ERROR, status=403)

    payload = _parse_json(request)
    if payload is None:
        return _json_error(INVALID_JSON_BODY_ERROR, status=400)

    account_id = payload.get("account_id")
    household_id = payload.get("household_id")
    amount = payload.get("amount")
    reference = payload.get("reference") or payload.get("payment_reference") or ""
    source = payload.get("source") or "EXTERNAL"
    payment_date = payload.get("payment_date")

    if not account_id and not household_id:
        return _json_error("account_id or household_id is required", status=400)

    try:
        amt = _parse_decimal(amount, "amount")
        requested_by_charge = _aggregate_requested_allocations(payload.get("allocations") or [])
    except ValueError:
        return _json_error(INVALID_REQUEST_PAYLOAD_ERROR, status=400)

    if amt <= Decimal("0"):
        return _json_error("amount must be > 0", status=400)

    acct, account_error = _resolve_payment_account(sid=sid, account_id=account_id, household_id=household_id)
    if account_error is not None:
        return account_error

    allow_partial = bool(payload.get("allow_partial"))
    allow_overpay = bool(payload.get("allow_overpay"))
    allocation_error = _validate_allocation_totals(
        requested_by_charge=requested_by_charge,
        amount=amt,
        allow_partial=allow_partial,
    )
    if allocation_error is not None:
        return allocation_error

    resolved_allocations, resolved_error = _resolve_charge_allocations(
        sid=sid,
        acct=acct,
        requested_by_charge=requested_by_charge,
        allow_overpay=allow_overpay,
    )
    if resolved_error is not None:
        return resolved_error

    with transaction.atomic():
        payment = Payment.objects.create(
            school_id=sid,
            account=acct,
            source=str(source)[:32],
            reference=str(reference)[:64],
            amount=amt,
        )
        created_allocations = _create_allocations(
            sid=sid,
            payment=payment,
            resolved_allocations=resolved_allocations,
        )
        allocated_total = (
            Allocation.objects.filter(school_id=sid, payment=payment).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

    remaining_unallocated = Decimal(str(amt)) - Decimal(str(allocated_total))
    if remaining_unallocated < Decimal("0"):
        remaining_unallocated = Decimal("0")

    data = _payment_to_dict(payment)
    data["allocations"] = created_allocations
    data["allocated_total"] = str(allocated_total)
    data["remaining_unallocated"] = str(remaining_unallocated)
    if payment_date is not None:
        data["payment_date_input"] = str(payment_date)

    return _envelope(data, status=201)


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
        return _json_error("Invalid request payload", status=400)

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
        acct = LedgerAccount.objects.get(pk=UUID(account_id), school_id=sid)
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
        ch = Charge.objects.get(pk=UUID(charge_id), school_id=sid)
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
        acct = LedgerAccount.objects.get(pk=UUID(account_id), school_id=sid)
    except LedgerAccount.DoesNotExist:
        return _json_error("Not found", status=404)

    data = build_account_statement(school_id=sid, account=acct)
    return _envelope(data, status=200)


@extend_schema(responses=LedgerOpenChargeEnvelopeSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def open_charges(request: HttpRequest):
    """List open (unpaid) charges for an account/household.

    Query params:
      - account_id=<uuid> OR household_id=<uuid>
    """
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    account_id = request.GET.get("account_id")
    household_id = request.GET.get("household_id")
    if not account_id and not household_id:
        return _json_error("account_id or household_id is required", status=400)

    acct, account_error = _resolve_payment_account(sid=sid, account_id=account_id, household_id=household_id)
    if account_error is not None:
        return account_error

    charges = Charge.objects.filter(school_id=sid, account=acct, is_void=False).order_by("created_at", "id")

    open_rows = []
    charge_ids = []
    for ch in charges.iterator():
        remaining = charge_remaining_balance(ch)
        if remaining <= Decimal("0.00"):
            continue
        charge_ids.append(ch.id)
        open_rows.append(
            {
                "charge": _charge_to_dict(ch),
                "remaining_balance": str(remaining),
            }
        )

    invoice_by_charge = _build_invoice_lookup(sid=sid, charge_ids=charge_ids)

    for row in open_rows:
        cid = row["charge"]["id"]
        row["invoice"] = invoice_by_charge.get(cid)

    return _envelope(open_rows, status=200)


@extend_schema(responses=LedgerOpenInvoiceEnvelopeSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def open_invoices(request: HttpRequest):
    """List open invoices (via billing.Invoice) with computed balances from ledger allocations.

    Query params:
      - household_id=<uuid> (optional)
    """
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    try:
        from billing.models import Invoice
    except Exception:
        return _json_error("Invoice model not available", status=500)

    household_id = request.GET.get("household_id")
    qs = Invoice.objects.filter(school_id=sid).exclude(ledger_charge_id=None)
    if household_id:
        try:
            qs = qs.filter(household_id=_parse_uuid(household_id, "household_id"))
        except ValueError:
            return _json_error(INVALID_REQUEST_PAYLOAD_ERROR, status=400)
    invoices = list(qs.order_by("due_on", "id"))
    charge_ids = [inv.ledger_charge_id for inv in invoices if inv.ledger_charge_id]

    paid_by_charge = {}
    if charge_ids:
        agg = (
            Allocation.objects.filter(school_id=sid, charge_id__in=charge_ids)
            .values("charge_id")
            .annotate(total=Sum("amount"))
        )
        for row in agg.iterator():
            paid_by_charge[str(row["charge_id"])] = row.get("total") or Decimal("0.00")

    out = []
    for inv in invoices:
        cid = inv.ledger_charge_id
        paid = Decimal(str(paid_by_charge.get(str(cid), Decimal("0.00"))))
        total = Decimal(str(inv.total_amount))
        balance = total - paid
        if balance <= Decimal("0.00"):
            continue
        out.append(
            {
                "invoice_id": str(inv.id),
                "household_id": str(inv.household_id),
                "due_on": inv.due_on.isoformat() if inv.due_on else None,
                "total_amount": str(inv.total_amount),
                "ledger_charge_id": str(cid),
                "paid_amount": str(paid),
                "balance": str(balance),
            }
        )

    return _envelope(out, status=200)


# ---------------------------------------------------------------------------
# Phase 2 Priority 2 — Ledger Invariants (read-only, tenant-scoped)
# ---------------------------------------------------------------------------

@extend_schema(responses=LedgerEnvelopeSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ledger_invariants(request: HttpRequest):
    """
    GET /api/v1/ledger/invariants/

    Returns a JSON report of known accounting violations within the
    caller's school. Safe to call at any time; makes no writes.

    Invariants checked:
      1. over_allocated  – charges where SUM(allocations.amount) > charge.amount
      2. negative_charges – non-void charges with amount < 0
      3. negative_payments – non-void payments with amount < 0

    Response shape:
      { ok: true, data: { school_id, violations: {...}, clean: bool } }
    """
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    # RBAC: HEAD_OF_SCHOOL or FINANCE_DIRECTOR only
    roles = set(
        UserRole.objects.filter(user_id=request.user.id, school_id=sid)
        .values_list("role_code", flat=True)
    )
    if not roles.intersection({"HEAD_OF_SCHOOL", "FINANCE_DIRECTOR"}):
        return _json_error("Forbidden: requires HEAD_OF_SCHOOL or FINANCE_DIRECTOR role.", status=403)

    # 1. Over-allocated charges
    alloc_agg = (
        Allocation.objects.filter(school_id=sid)
        .values("charge_id")
        .annotate(total_applied=Sum("amount"))
    )
    alloc_by_charge = {str(row["charge_id"]): row["total_applied"] for row in alloc_agg}

    over_allocated = []
    for charge in Charge.objects.filter(school_id=sid, is_void=False).only("id", "amount", "description"):
        applied = alloc_by_charge.get(str(charge.id), Decimal("0.00"))
        if applied and Decimal(str(applied)) > Decimal(str(charge.amount)):
            over_allocated.append({
                "charge_id": str(charge.id),
                "charge_amount": str(charge.amount),
                "allocated_amount": str(applied),
                "overage": str(Decimal(str(applied)) - Decimal(str(charge.amount))),
            })

    # 2. Negative-amount charges (non-void)
    negative_charges = [
        {"charge_id": str(c.id), "amount": str(c.amount)}
        for c in Charge.objects.filter(school_id=sid, is_void=False, amount__lt=0).only("id", "amount")
    ]

    # 3. Negative-amount payments (non-void)
    negative_payments = [
        {"payment_id": str(p.id), "amount": str(p.amount)}
        for p in Payment.objects.filter(school_id=sid, is_void=False, amount__lt=0).only("id", "amount")
    ]

    violations = {
        "over_allocated": over_allocated,
        "negative_charges": negative_charges,
        "negative_payments": negative_payments,
    }
    clean = not any(violations.values())

    return _envelope(
        {
            "school_id": str(sid),
            "clean": clean,
            "violations": violations,
        },
        status=200,
    )


# ---------------------------------------------------------------------------
# Phase 2 Priority 5 — Void endpoints (charge / payment)
# Reversal journal entries are handled by ledger/signals.py automatically.
# Both endpoints are idempotent: voiding twice returns 200 cleanly.
# ---------------------------------------------------------------------------

@extend_schema(responses=LedgerEnvelopeSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def void_charge(request: HttpRequest, charge_id: str):
    """
    POST /api/v1/ledger/charges/<charge_id>/void/

    Idempotent: voiding an already-void charge returns 200.
    Allocations on the charge are deleted before void so that
    balance/invariant queries remain consistent.
    """
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    with transaction.atomic():
        try:
            ch = Charge.objects.select_for_update().get(id=UUID(charge_id), school_id=sid)
        except (Charge.DoesNotExist, Exception):
            return _json_error("charge not found", status=404)

        if ch.is_void:
            return _envelope({"id": str(ch.id), "is_void": True, "note": "already void"}, status=200)

        Allocation.objects.filter(school_id=sid, charge=ch).delete()
        ch.is_void = True
        ch.save(update_fields=["is_void"])

    return _envelope({"id": str(ch.id), "school_id": str(sid), "is_void": True}, status=200)


@extend_schema(responses=LedgerEnvelopeSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def void_payment(request: HttpRequest, payment_id: str):
    """
    POST /api/v1/ledger/payments/<payment_id>/void/

    Idempotent: voiding an already-void payment returns 200.
    Allocations on the payment are deleted before void so that
    balance/invariant queries remain consistent.
    """
    sid = get_request_school_id(request)
    if not sid:
        return _json_error("school_id could not be derived for request", status=403)

    with transaction.atomic():
        try:
            p = Payment.objects.select_for_update().get(id=UUID(payment_id), school_id=sid)
        except (Payment.DoesNotExist, Exception):
            return _json_error("payment not found", status=404)

        if p.is_void:
            return _envelope({"id": str(p.id), "is_void": True, "note": "already void"}, status=200)

        Allocation.objects.filter(school_id=sid, payment=p).delete()
        p.is_void = True
        p.save(update_fields=["is_void"])

    return _envelope({"id": str(p.id), "school_id": str(sid), "is_void": True}, status=200)

