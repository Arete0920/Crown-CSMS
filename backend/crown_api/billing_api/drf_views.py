from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from households.scoping import get_request_school_id


class BillingRunCreateApiView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @method_decorator(csrf_exempt)
    @transaction.atomic
    def post(self, request):
        """JWT-authenticated creation of a billing run that yields an invoice.

        This endpoint is intentionally non-CSRF and exists alongside the legacy
        session-based billing run routes.

        Returns: billing_run_id + invoice_id (always).
        """

        school_id = get_request_school_id(request)
        if not school_id:
            return Response(
                {"detail": "Missing school context (X-Crown-School-Id)"},
                status=status.HTTP_403_FORBIDDEN,
            )

        payload = request.data or {}
        term = (payload.get("term") or "2026-2027").strip()
        description = (payload.get("description") or "Golden Path API billing run").strip()
        amount_raw = payload.get("amount_per_student")
        if amount_raw is None or amount_raw == "":
            amount_raw = "250.00"

        try:
            amount = Decimal(str(amount_raw)).quantize(Decimal("0.01"))
        except Exception:
            return Response(
                {"detail": "amount_per_student must be a decimal like 250.00"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if amount <= 0:
            return Response(
                {"detail": "amount_per_student must be > 0"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from billing.models import BillingRun, Invoice
        from households.models import Household
        from ledger.models import Charge, LedgerAccount

        run_id = datetime.now().strftime("%Y%m%d-%H%M%S")

        household, _ = Household.objects.get_or_create(
            school_id=school_id,
            name="GP Household",
        )
        ledger_acct, _ = LedgerAccount.objects.get_or_create(
            school_id=school_id,
            household=household,
        )

        charge = Charge.objects.create(
            school_id=school_id,
            account=ledger_acct,
            description=f"GP Tuition Charge {run_id}",
            amount=amount,
        )

        billing_run = BillingRun.objects.create(
            school_id=school_id,
            term=str(term)[:24],
            run_type="TUITION",
            description=str(description)[:200],
            amount_per_student=amount,
        )

        invoice = Invoice.objects.create(
            school_id=school_id,
            billing_run=billing_run,
            household=household,
            due_on=date.today(),
            total_amount=amount,
            ledger_charge_id=charge.id,
        )

        return Response(
            {
                "ok": True,
                "data": {
                    "billing_run_id": str(billing_run.id),
                    "invoice_id": str(invoice.id),
                    "household_id": str(household.id),
                    "ledger_charge_id": str(charge.id),
                    "amount": str(amount),
                },
            },
            status=status.HTTP_201_CREATED,
        )
