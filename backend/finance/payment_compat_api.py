"""Compatibility API for legacy /api/finance/payments routes.

The URL contract remains stable while canonical external money-movement authority
lives in payments.Payment / payments.Refund. finance.FinancePayment and
finance.FinanceRefund are compatibility projections only.
"""
from __future__ import annotations

import logging
import uuid

from django.db import transaction
from core.permissions import CrownModulePermission
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from finance.models import (
    FinanceObligation,
    FinancePayment,
    PaymentStatus as LegacyPaymentStatus,
    Processor,
)
from finance.serializers import PaymentSerializer, RefundSerializer
from finance.services import _verified_household_id_for_user
from households.scoping import get_request_school_id
from payments.authority_services import (
    CanonicalOverRefundError,
    IdempotencyConflict,
    InvalidPaymentState,
    PaymentAuthorityError,
    PaymentCompatibilityRequired,
    create_payment,
    request_refund,
    settle_payment,
    settle_refund,
)
from payments.hold import payment_hold_response
from payments.models import Payment as CanonicalPayment


logger = logging.getLogger(__name__)

DETAIL_AMOUNT_NOT_INT = "amount_cents must be an integer."
DETAIL_AMOUNT_POSITIVE = "amount_cents must be > 0."


def _household_id_for_user(*, school_id, user):
    """Use the same persisted household identity required for ledger posting."""
    return _verified_household_id_for_user(school_id=school_id, user=user)

def _canonical_for_legacy(
    *,
    legacy_payment: FinancePayment,
    created_by=None,
    requested_allocations: list[dict] | None = None,
) -> CanonicalPayment:
    household_id = _household_id_for_user(
        school_id=legacy_payment.school_id, user=legacy_payment.payer_user,
    )
    if household_id is None:
        raise PaymentCompatibilityRequired("Verified payer household is required.")

    canonical = CanonicalPayment.objects.filter(
        school_id=legacy_payment.school_id,
        finance_payment_id=legacy_payment.pk,
    ).first()
    if canonical is not None and (
        canonical.household_id != household_id
        or canonical.amount_cents != legacy_payment.amount_cents
        or canonical.currency != legacy_payment.currency
    ):
        # Canonical identity/amount facts are immutable: never silently repair.
        raise PaymentCompatibilityRequired("Canonical payment conflicts with verified payer facts.")

    if canonical is None:
        canonical = create_payment(
            school_id=legacy_payment.school_id,
            household_id=household_id,
            finance_payment_id=legacy_payment.pk,
            amount_cents=legacy_payment.amount_cents,
            currency=legacy_payment.currency,
            idempotency_key=f"finance_compat_payment:{legacy_payment.pk}",
            created_by=created_by,
        )

    if legacy_payment.status == LegacyPaymentStatus.SETTLED and canonical.status == "pending":
        allocations = requested_allocations
        if allocations is None:
            allocations = [
                {
                    "obligation_id": allocation.obligation_id,
                    "amount_cents": allocation.amount_cents,
                }
                for allocation in legacy_payment.allocations.all()
            ]
        canonical = settle_payment(
            payment=canonical,
            allocations_payload=allocations,
        )
    return canonical


def _provider_processing_requested(processor: str) -> bool:
    return (processor or Processor.MANUAL) != Processor.MANUAL


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def payment_intent_create(request):
    """Create a manual compatibility payment with canonical Payments authority."""
    if "HTTP_X_SCHOOL_ID" not in request.META and "HTTP_X_CROWN_SCHOOL_ID" not in request.META:
        return Response(
            {"detail": "X-School-ID header is required for payment operations."},
            status=400,
        )
    school_id = get_request_school_id(request, required=True)

    try:
        amount_cents = int(request.data.get("amount_cents", 0))
    except (ValueError, TypeError):
        return Response({"detail": DETAIL_AMOUNT_NOT_INT}, status=400)
    if amount_cents <= 0:
        return Response({"detail": DETAIL_AMOUNT_POSITIVE}, status=400)

    processor = request.data.get("processor", Processor.MANUAL)
    if _provider_processing_requested(processor):
        return payment_hold_response()

    currency = (request.data.get("currency", "USD") or "USD").strip().upper()
    idempotency_key = (request.data.get("idempotency_key", "") or "").strip()
    household_id = _household_id_for_user(school_id=school_id, user=request.user)
    if household_id is None:
        return Response({"detail": "Verified payer household is required."}, status=403)

    if idempotency_key:
        existing = (
            FinancePayment.objects.filter(
                school_id=school_id,
                idempotency_key=idempotency_key,
            )
            .exclude(status=LegacyPaymentStatus.FAILED)
            .first()
        )
        if existing is not None:
            if (
                existing.payer_user_id != request.user.pk
                or existing.amount_cents != amount_cents
                or existing.currency != currency
                or existing.processor != Processor.MANUAL
            ):
                return Response(
                    {"detail": "Existing payment conflicts with requested payment facts."},
                    status=409,
                )
            try:
                _canonical_for_legacy(
                    legacy_payment=existing,
                    created_by=request.user,
                )
            except PaymentAuthorityError:
                logger.exception(
                    "finance compatibility payment adoption failed",
                    extra={"finance_payment_id": existing.pk},
                )
                return Response(
                    {"detail": "Existing payment conflicts with canonical payment facts."},
                    status=409,
                )
            return Response(PaymentSerializer(existing).data, status=200)

    with transaction.atomic():
        legacy_payment = FinancePayment.objects.create(
            school_id=school_id,
            payer_user=request.user,
            amount_cents=amount_cents,
            currency=currency,
            processor=Processor.MANUAL,
            status=LegacyPaymentStatus.PENDING,
            idempotency_key=idempotency_key,
            created_by=request.user,
        )
        create_payment(
            school_id=school_id,
            household_id=household_id,
            finance_payment_id=legacy_payment.pk,
            amount_cents=amount_cents,
            currency=currency,
            idempotency_key=(
                f"finance_api:{idempotency_key}"
                if idempotency_key
                else f"finance_compat_payment:{legacy_payment.pk}"
            ),
            created_by=request.user,
        )

    payload = PaymentSerializer(legacy_payment).data
    payload["client_secret"] = None
    return Response(payload, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated, CrownModulePermission("finance.edit", write_code="finance.edit")])
def payment_settle(request, payment_id: int):
    """Settle through canonical Payments, projecting into legacy Finance."""
    school_id = get_request_school_id(request, required=True)

    try:
        legacy_payment = FinancePayment.objects.get(pk=payment_id, school_id=school_id)
    except (FinancePayment.DoesNotExist, ValueError):
        return Response({"detail": "Payment not found."}, status=404)

    if _provider_processing_requested(legacy_payment.processor):
        return payment_hold_response()

    allocations_payload = request.data.get("allocations", [])
    try:
        canonical = _canonical_for_legacy(
            legacy_payment=legacy_payment,
            created_by=request.user,
            requested_allocations=allocations_payload,
        )
        canonical = settle_payment(
            payment=canonical,
            allocations_payload=allocations_payload,
        )
    except FinanceObligation.DoesNotExist:
        return Response({"detail": "Obligation not found for this school."}, status=404)
    except (PaymentAuthorityError, IdempotencyConflict, PaymentCompatibilityRequired) as exc:
        return Response({"detail": str(exc)}, status=409)
    except Exception:
        logger.exception(
            "finance compatibility payment settlement failed",
            extra={"finance_payment_id": payment_id},
        )
        return Response({"detail": "Unable to settle payment at this time."}, status=400)

    legacy_payment.refresh_from_db()
    return Response(PaymentSerializer(legacy_payment).data, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated, CrownModulePermission("finance.edit", write_code="finance.edit")])
def refund_create(request, payment_id: int):
    """Create and settle a manual refund through canonical Payments authority."""
    school_id = get_request_school_id(request, required=True)

    try:
        legacy_payment = FinancePayment.objects.get(pk=payment_id, school_id=school_id)
    except (FinancePayment.DoesNotExist, ValueError):
        return Response({"detail": "Payment not found."}, status=404)

    if _provider_processing_requested(legacy_payment.processor):
        return payment_hold_response()

    try:
        amount_cents = int(request.data.get("amount_cents", 0))
    except (ValueError, TypeError):
        return Response({"detail": DETAIL_AMOUNT_NOT_INT}, status=400)
    if amount_cents <= 0:
        return Response({"detail": DETAIL_AMOUNT_POSITIVE}, status=400)

    try:
        canonical = _canonical_for_legacy(
            legacy_payment=legacy_payment,
            created_by=request.user,
        )
        requested_key = (request.data.get("idempotency_key", "") or "").strip()
        canonical_refund = request_refund(
            payment=canonical,
            amount_cents=amount_cents,
            idempotency_key=(
                f"finance_api_refund:{requested_key}"
                if requested_key
                else f"finance_api_refund:{uuid.uuid4()}"
            ),
            created_by=request.user,
        )
        canonical_refund = settle_refund(refund=canonical_refund)
    except CanonicalOverRefundError:
        return Response(
            {"detail": "Refund amount exceeds the remaining refundable balance."},
            status=409,
        )
    except (InvalidPaymentState, PaymentAuthorityError, IdempotencyConflict, PaymentCompatibilityRequired) as exc:
        return Response({"detail": str(exc)}, status=409)

    legacy_refund = legacy_payment.refunds.get(pk=canonical_refund.finance_refund_id)
    return Response(RefundSerializer(legacy_refund).data, status=201)
