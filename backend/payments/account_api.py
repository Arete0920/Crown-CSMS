from decimal import Decimal

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from billing.models import Invoice
from billing.reconciliation import compute_invoice_balance_due
from households.scoping import get_request_school_id
from ledger.models import LedgerAccount, Payment
from payments.access import user_can_access_household_finance
from payments.models import PaymentIntentRecord


ZERO = Decimal("0.00")


def _money(value):
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def household_finance_summary(request, household_id):
    school_id = get_request_school_id(request, required=True)

    if not user_can_access_household_finance(request.user, household_id):
        return Response(
            {"detail": "You do not have permission to view this household account."},
            status=status.HTTP_403_FORBIDDEN,
        )

    invoices = (
        Invoice.objects.filter(school_id=school_id, household_id=household_id)
        .select_related("household")
        .order_by("-id")
    )

    total_invoiced = ZERO
    total_outstanding = ZERO
    open_invoice_count = 0

    invoice_rows = []
    for inv in invoices:
        total_amount = _money(getattr(inv, "total_amount", ZERO))
        balance_due = compute_invoice_balance_due(inv)

        total_invoiced += total_amount
        total_outstanding += balance_due
        if balance_due > ZERO:
            open_invoice_count += 1

        invoice_rows.append(
            {
                "id": str(inv.id),
                "invoice_number": getattr(inv, "invoice_number", None) or getattr(inv, "number", None),
                "status": getattr(inv, "status", ""),
                "issue_date": getattr(inv, "issue_date", None),
                "due_date": getattr(inv, "due_date", None),
                "total_amount": str(total_amount),
                "balance_due": str(balance_due),
            }
        )

    ledger_account = LedgerAccount.objects.filter(
        school_id=school_id,
        household_id=household_id,
    ).first()

    payment_rows = []
    total_paid = ZERO
    if ledger_account is not None:
        payments = Payment.objects.filter(
            school_id=school_id,
            account=ledger_account,
        ).order_by("-id")[:25]

        for p in payments:
            amount = _money(getattr(p, "amount", ZERO))
            total_paid += amount
            payment_rows.append(
                {
                    "id": str(p.id),
                    "amount": str(amount),
                    "status": "void" if getattr(p, "is_void", False) else "posted",
                    "source": getattr(p, "source", ""),
                    "external_payment_id": getattr(p, "reference", ""),
                    "created_at": getattr(p, "created_at", None),
                }
            )

    intents = (
        PaymentIntentRecord.objects.filter(school_id=school_id, household_id=household_id)
        .order_by("-id")[:25]
    )

    intent_rows = [
        {
            "id": intent.id,
            "provider": intent.provider,
            "amount": str(intent.amount),
            "status": intent.status,
            "provider_intent_id": intent.provider_intent_id,
            "provider_payment_id": intent.provider_payment_id,
            "created_at": intent.created_at,
        }
        for intent in intents
    ]

    return Response(
        {
            "household_id": str(household_id),
            "summary": {
                "total_invoiced": str(total_invoiced),
                "total_outstanding": str(total_outstanding),
                "open_invoice_count": open_invoice_count,
                "recent_payments_total": str(total_paid),
            },
            "invoices": invoice_rows,
            "payments": payment_rows,
            "gateway_intents": intent_rows,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def household_payment_history(request, household_id):
    school_id = get_request_school_id(request, required=True)

    if not user_can_access_household_finance(request.user, household_id):
        return Response(
            {"detail": "You do not have permission to view this household payment history."},
            status=status.HTTP_403_FORBIDDEN,
        )

    ledger_account = LedgerAccount.objects.filter(
        school_id=school_id,
        household_id=household_id,
    ).first()

    if ledger_account is None:
        return Response({"results": []})

    payments = Payment.objects.filter(
        school_id=school_id,
        account=ledger_account,
    ).order_by("-id")

    rows = []
    for p in payments:
        rows.append(
            {
                "id": str(p.id),
                "amount": str(_money(getattr(p, "amount", ZERO))),
                "status": "void" if getattr(p, "is_void", False) else "posted",
                "source": getattr(p, "source", ""),
                "external_payment_id": getattr(p, "reference", ""),
                "created_at": getattr(p, "created_at", None),
            }
        )

    return Response({"results": rows})
