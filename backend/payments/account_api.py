from decimal import Decimal

from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from billing.models import Invoice
from billing.reconciliation import compute_invoice_balance_due
from households.scoping import get_request_school_id
from ledger.models import Allocation, Credit, LedgerAccount, Payment, compute_account_balance
from payments.access import user_can_access_household_finance
from payments.models import CanonicalRefundStatus, PaymentIntentRecord, Refund


ZERO = Decimal("0.00")


def _money(value):
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _cents_to_money(value):
    return (Decimal(int(value or 0)) / Decimal("100")).quantize(Decimal("0.01"))


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
    invoice_outstanding = ZERO
    open_invoice_count = 0

    invoice_rows = []
    for inv in invoices:
        total_amount = _money(getattr(inv, "total_amount", ZERO))
        balance_due = compute_invoice_balance_due(inv)

        total_invoiced += total_amount
        invoice_outstanding += balance_due
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
    recent_payments_total = ZERO
    gross_cash_total = ZERO
    allocated_cash_total = ZERO
    credit_total = ZERO
    student_account_balance = ZERO
    if ledger_account is not None:
        all_payments = Payment.objects.filter(
            school_id=school_id,
            account=ledger_account,
            is_void=False,
        )
        gross_cash_total = all_payments.aggregate(total=Sum("amount"))["total"] or ZERO
        allocated_cash_total = (
            Allocation.objects.filter(
                school_id=school_id,
                payment__account=ledger_account,
                payment__is_void=False,
                charge__is_void=False,
            ).aggregate(total=Sum("amount"))["total"]
            or ZERO
        )
        credit_total = (
            Credit.objects.filter(
                school_id=school_id,
                account=ledger_account,
                is_void=False,
            ).aggregate(total=Sum("amount"))["total"]
            or ZERO
        )
        student_account_balance = compute_account_balance(ledger_account)

        payments = all_payments.order_by("-id")[:25]
        for p in payments:
            amount = _money(getattr(p, "amount", ZERO))
            recent_payments_total += amount
            payment_rows.append(
                {
                    "id": str(p.id),
                    "amount": str(amount),
                    "status": "posted",
                    "source": getattr(p, "source", ""),
                    "external_payment_id": getattr(p, "reference", ""),
                    "created_at": getattr(p, "created_at", None),
                }
            )

    refund_cents = (
        Refund.objects.filter(
            school_id=school_id,
            payment__household_id=household_id,
            status=CanonicalRefundStatus.SETTLED,
        ).aggregate(total=Sum("amount_cents"))["total"]
        or 0
    )
    refund_total = _cents_to_money(refund_cents)
    net_cash_total = gross_cash_total - refund_total
    unapplied_cash_total = gross_cash_total - allocated_cash_total

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
                "invoice_outstanding": str(invoice_outstanding),
                "open_invoice_count": open_invoice_count,
                "student_account_balance": str(student_account_balance),
                "gross_cash_total": str(gross_cash_total),
                "allocated_cash_total": str(allocated_cash_total),
                "credit_total": str(credit_total),
                "refund_total": str(refund_total),
                "net_cash_total": str(net_cash_total),
                "unapplied_cash_total": str(unapplied_cash_total),
                "recent_payments_total": str(recent_payments_total),
                # Backward compatibility: total_outstanding now reflects Student Accounts truth.
                "total_outstanding": str(student_account_balance),
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
