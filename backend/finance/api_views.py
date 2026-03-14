"""
finance/api_views.py — Finance & Tuition module API endpoints.

Tenant isolation: every view calls get_request_school_id(request, required=True),
which raises MissingSchoolContext (HTTP 400) or NotFound (HTTP 404) on failure.

Auth: IsAuthenticated guards all endpoints.
Admin-only routes additionally check request.user.is_staff.

Ledger posting: explicit via services.py — no signals, no side-effects in views.
"""
from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from households.scoping import get_request_school_id, MissingSchoolContext
from finance.models import (
    FinanceAllocation,
    FinanceDonation,
    FinanceInvoice,
    FinanceObligation,
    FinancePayment,
    FinanceRefund,
    MoneyStatus,
    PaymentStatus,
    Processor,
)
from finance.serializers import (
    AllocationSerializer,
    DonationSerializer,
    InvoiceSerializer,
    ObligationSerializer,
    PaymentSerializer,
    RefundSerializer,
)
from finance.services import (
    OverRefundError,
    create_invoice_from_obligations,
    initiate_refund,
    ledger_post_donation,
    settle_payment_and_allocate,
)


logger = logging.getLogger(__name__)


def _is_staff(request) -> bool:
    return bool(getattr(request, "user", None) and request.user.is_authenticated and request.user.is_staff)


# ---------------------------------------------------------------------------
# Obligations — admin: create/list; parent: read own
# ---------------------------------------------------------------------------

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def obligations(request):
    """
    GET  — Admin: list all obligations for school.
    POST — Admin: create a single obligation.
    """
    school = get_request_school_id(request, required=True)

    if request.method == "GET":
        if not _is_staff(request):
            return Response({"detail": "Admin required."}, status=403)
        qs = FinanceObligation.objects.filter(school_id=school).order_by("due_date")
        return Response(ObligationSerializer(qs, many=True).data)

    # POST — create
    if not _is_staff(request):
        return Response({"detail": "Admin required."}, status=403)

    required = ["payer_user_id", "obligation_type", "description", "due_date", "amount_cents"]
    for field in required:
        if not request.data.get(field) and request.data.get(field) != 0:
            return Response({"detail": f"Missing required field: {field}"}, status=400)

    try:
        amount_cents = int(request.data["amount_cents"])
        if amount_cents < 0:
            raise ValueError
    except (ValueError, TypeError):
        return Response({"detail": "amount_cents must be a non-negative integer."}, status=400)

    from core.models import School as SchoolModel
    try:
        school_obj = SchoolModel.objects.get(pk=school)
    except SchoolModel.DoesNotExist:
        return Response({"detail": "School not found."}, status=404)

    from core.models import UserAccount
    try:
        payer = UserAccount.objects.get(pk=request.data["payer_user_id"])
    except (UserAccount.DoesNotExist, ValueError, TypeError):
        return Response({"detail": "payer_user not found."}, status=404)

    ob = FinanceObligation.objects.create(
        school=school_obj,
        payer_user=payer,
        obligation_type=request.data["obligation_type"],
        status=request.data.get("status", MoneyStatus.OPEN),
        description=request.data["description"],
        due_date=request.data["due_date"],
        amount_cents=amount_cents,
        currency=request.data.get("currency", "USD"),
        academic_year_label=request.data.get("academic_year_label", ""),
        reference=request.data.get("reference", ""),
        created_by=request.user,
        updated_by=request.user,
    )
    # Ledger posting deferred: call ledger_post_obligation(ob) once wired.
    return Response(ObligationSerializer(ob).data, status=201)


# ---------------------------------------------------------------------------
# Invoices — admin only
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def invoice_create_from_obligations(request):
    """
    POST — Create an invoice by grouping existing obligations.

    Body:
      payer_user_id   int  (required)
      period_start    date string (required)
      period_end      date string (required)
      due_date        date string (required)
      obligation_ids  list[int]   (required)
    """
    if not _is_staff(request):
        return Response({"detail": "Admin required."}, status=403)

    school = get_request_school_id(request, required=True)

    payer_user_id = request.data.get("payer_user_id")
    period_start = request.data.get("period_start")
    period_end = request.data.get("period_end")
    due_date = request.data.get("due_date")
    obligation_ids = request.data.get("obligation_ids", [])

    if not payer_user_id or not period_start or not period_end or not due_date:
        return Response({"detail": "Missing required fields."}, status=400)

    from core.models import School as SchoolModel, UserAccount
    try:
        school_obj = SchoolModel.objects.get(pk=school)
    except SchoolModel.DoesNotExist:
        return Response({"detail": "School not found."}, status=404)
    try:
        payer = UserAccount.objects.get(pk=payer_user_id)
    except (UserAccount.DoesNotExist, ValueError, TypeError):
        return Response({"detail": "payer_user not found."}, status=404)

    obs = list(
        FinanceObligation.objects.filter(
            school=school_obj,
            payer_user=payer,
            id__in=obligation_ids,
        ).order_by("due_date")
    )
    inv = create_invoice_from_obligations(
        school=school_obj,
        payer_user=payer,
        period_start=period_start,
        period_end=period_end,
        due_date=due_date,
        obligations=obs,
        created_by=request.user,
    )
    return Response(InvoiceSerializer(inv).data, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def invoice_list(request):
    """GET — Admin: list invoices for school."""
    if not _is_staff(request):
        return Response({"detail": "Admin required."}, status=403)
    school = get_request_school_id(request, required=True)
    qs = FinanceInvoice.objects.prefetch_related("lines").filter(school_id=school).order_by("due_date")
    return Response(InvoiceSerializer(qs, many=True).data)


# ---------------------------------------------------------------------------
# Parent balance (family portal) — authenticated, own school only
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def parent_balance(request):
    """
    GET — Return balance summary for the authenticated payer.
    total_due_cents:  sum of all non-void obligation amounts
    paid_cents:       sum of allocations applied to those obligations
    balance_cents:    max(total_due - paid, 0)
    """
    school = get_request_school_id(request, required=True)
    payer = request.user

    obs = list(
        FinanceObligation.objects.filter(
            school_id=school, payer_user=payer
        ).exclude(status=MoneyStatus.VOID)
    )
    total_due = sum(o.amount_cents for o in obs)

    paid = 0
    for o in obs:
        paid += sum(a.amount_cents for a in o.allocations.all())

    balance = max(total_due - paid, 0)
    return Response(
        {"total_due_cents": total_due, "paid_cents": paid, "balance_cents": balance}
    )


# ---------------------------------------------------------------------------
# Payments — intent creation (any auth); settle (admin)
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def payment_intent_create(request):
    """
    POST — Create a pending FinancePayment record (intent before processor settlement).
    Body: amount_cents, processor (optional), idempotency_key (optional)

    Requires an explicit X-School-ID header. Falls back to user.school_id are
    intentionally NOT accepted here to prevent payment creation without an
    explicit tenant context assertion.
    """
    # Require the school header to be explicitly present — never fall back to
    # user.school_id for payment operations (tenant isolation requirement).
    if "HTTP_X_SCHOOL_ID" not in request.META and "HTTP_X_CROWN_SCHOOL_ID" not in request.META:
        return Response(
            {"detail": "X-School-ID header is required for payment operations."},
            status=400,
        )
    school = get_request_school_id(request, required=True)

    try:
        amount_cents = int(request.data.get("amount_cents", 0))
    except (ValueError, TypeError):
        return Response({"detail": "amount_cents must be an integer."}, status=400)

    if amount_cents <= 0:
        return Response({"detail": "amount_cents must be > 0."}, status=400)

    from core.models import School as SchoolModel
    try:
        school_obj = SchoolModel.objects.get(pk=school)
    except SchoolModel.DoesNotExist:
        return Response({"detail": "School not found."}, status=404)

    idempotency_key = request.data.get("idempotency_key", "")

    # Idempotency guard: if a non-failed payment with this key exists, return it.
    if idempotency_key:
        existing = FinancePayment.objects.filter(
            school=school_obj,
            idempotency_key=idempotency_key,
        ).exclude(status=PaymentStatus.FAILED).first()
        if existing:
            return Response(PaymentSerializer(existing).data, status=200)

    pay = FinancePayment.objects.create(
        school=school_obj,
        payer_user=request.user,
        amount_cents=amount_cents,
        currency=request.data.get("currency", "USD"),
        processor=request.data.get("processor", Processor.MANUAL),
        status=PaymentStatus.PENDING,
        idempotency_key=idempotency_key,
        created_by=request.user,
    )
    # TODO: create processor intent (Stripe/Compuwerx) and return client_secret
    return Response(PaymentSerializer(pay).data, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def payment_settle(request, payment_id: int):
    """
    POST — Admin: settle a payment and allocate to obligations.
    Body: allocations = [{"obligation_id": int, "amount_cents": int}, ...]
    Idempotent: already-settled payments return 200.
    """
    if not _is_staff(request):
        return Response({"detail": "Admin required."}, status=403)

    school = get_request_school_id(request, required=True)

    try:
        payment = FinancePayment.objects.get(pk=payment_id, school_id=school)
    except (FinancePayment.DoesNotExist, ValueError):
        return Response({"detail": "Payment not found."}, status=404)

    allocations_payload = request.data.get("allocations", [])

    try:
        payment = settle_payment_and_allocate(
            payment=payment, allocations_payload=allocations_payload
        )
    except FinanceObligation.DoesNotExist:
        return Response({"detail": "Obligation not found for this school."}, status=404)
    except Exception:
        logger.exception("payment_settle: unexpected error while settling payment", extra={"payment_id": payment_id})
        return Response({"detail": "Unable to settle payment at this time."}, status=400)

    return Response(PaymentSerializer(payment).data, status=200)


# ---------------------------------------------------------------------------
# Refunds — admin only
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def refund_create(request, payment_id: int):
    """
    POST — Admin: initiate a refund against a settled payment.
    Body: amount_cents, idempotency_key (optional)
    Raises 409 if refund would exceed original payment amount.
    """
    if not _is_staff(request):
        return Response({"detail": "Admin required."}, status=403)

    school = get_request_school_id(request, required=True)

    try:
        payment = FinancePayment.objects.get(pk=payment_id, school_id=school)
    except (FinancePayment.DoesNotExist, ValueError):
        return Response({"detail": "Payment not found."}, status=404)

    try:
        amount_cents = int(request.data.get("amount_cents", 0))
    except (ValueError, TypeError):
        return Response({"detail": "amount_cents must be an integer."}, status=400)

    if amount_cents <= 0:
        return Response({"detail": "amount_cents must be > 0."}, status=400)

    try:
        refund = initiate_refund(
            payment=payment,
            amount_cents=amount_cents,
            processor=request.data.get("processor", Processor.MANUAL),
            created_by=request.user,
            idempotency_key=request.data.get("idempotency_key", ""),
        )
    except OverRefundError:
        return Response({"detail": "Refund amount exceeds the remaining refundable balance."}, status=409)

    return Response(RefundSerializer(refund).data, status=201)


# ---------------------------------------------------------------------------
# Donations — authenticated users
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def donation_create(request):
    """
    POST — Any authenticated user: record a donation intent.
    Body: amount_cents, fund_code, memo, is_recurring, recurring_rule, next_run_at
    """
    school = get_request_school_id(request, required=True)

    try:
        amount_cents = int(request.data.get("amount_cents", 0))
    except (ValueError, TypeError):
        return Response({"detail": "amount_cents must be an integer."}, status=400)

    if amount_cents <= 0:
        return Response({"detail": "amount_cents must be > 0."}, status=400)

    from core.models import School as SchoolModel
    try:
        school_obj = SchoolModel.objects.get(pk=school)
    except SchoolModel.DoesNotExist:
        return Response({"detail": "School not found."}, status=404)

    donation = FinanceDonation.objects.create(
        school=school_obj,
        donor_user=request.user,
        amount_cents=amount_cents,
        currency=request.data.get("currency", "USD"),
        fund_code=request.data.get("fund_code", ""),
        memo=request.data.get("memo", ""),
        is_recurring=bool(request.data.get("is_recurring", False)),
        recurring_rule=request.data.get("recurring_rule", ""),
        next_run_at=request.data.get("next_run_at"),
    )
    # Ledger posting deferred: call ledger_post_donation(donation) once wired.
    return Response(DonationSerializer(donation).data, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def donation_list(request):
    """GET — Admin: list donations for school."""
    if not _is_staff(request):
        return Response({"detail": "Admin required."}, status=403)
    school = get_request_school_id(request, required=True)
    qs = FinanceDonation.objects.filter(school_id=school).order_by("-created_at")
    return Response(DonationSerializer(qs, many=True).data)
