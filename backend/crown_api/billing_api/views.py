from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Sum
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from households.models import Household
from households.scoping import get_request_school_id

from billing.models import Invoice as BillingInvoice
from ledger.models import Allocation, Charge, LedgerAccount, Payment


def _d(x) -> Decimal:
    if x is None or x == "":
        return Decimal("0")
    try:
        return Decimal(str(x))
    except (InvalidOperation, ValueError):
        return Decimal("0")


class OpenInvoicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, household_id):
        school_id = get_request_school_id(request)
        if not school_id:
            return Response({"detail": "Missing school context"}, status=403)

        # no-leak: ensure household exists in-scope
        if not Household.objects.filter(id=household_id, school_id=school_id).exists():
            return Response({"detail": "Not found"}, status=404)

        invoices = (
            BillingInvoice.objects.filter(school_id=school_id, household_id=household_id)
            .order_by("due_on", "id")
            .all()
        )

        charge_ids = [
            inv.ledger_charge_id
            for inv in invoices
            if getattr(inv, "ledger_charge_id", None)
        ]

        charges = {}
        if charge_ids:
            charges = {c.id: c for c in Charge.objects.filter(school_id=school_id, id__in=charge_ids)}

        alloc_sums = []
        if charge_ids:
            alloc_sums = (
                Allocation.objects.filter(school_id=school_id, charge_id__in=charge_ids)
                .values("charge_id")
                .annotate(paid=Sum("amount"))
            )
        paid_by_charge = {row["charge_id"]: _d(row["paid"]) for row in alloc_sums}

        data = []
        for inv in invoices:
            cid = inv.ledger_charge_id
            ch = charges.get(cid) if cid else None
            total = _d(getattr(inv, "total_amount", None))
            paid = paid_by_charge.get(cid, Decimal("0")) if cid else Decimal("0")
            balance = total - paid

            # Open means balance > 0 and (if linked) charge not void.
            if balance <= 0:
                continue
            if ch and getattr(ch, "is_void", False):
                continue

            data.append(
                {
                    "invoice_id": str(inv.id),
                    "due_on": inv.due_on.isoformat() if inv.due_on else None,
                    "total_amount": str(total),
                    "paid_amount": str(paid),
                    "balance": str(balance),
                    "ledger_charge_id": str(cid) if cid else None,
                    "charge": {
                        "id": str(ch.id),
                        "description": ch.description,
                        "amount": str(ch.amount),
                        "is_void": bool(ch.is_void),
                    }
                    if ch
                    else None,
                }
            )

        return Response({"household_id": str(household_id), "items": data})


class PaymentsCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        school_id = get_request_school_id(request)
        if not school_id:
            return Response({"detail": "Missing school context"}, status=403)

        payload = request.data or {}
        household_id = payload.get("household_id")
        payment_date = payload.get("payment_date") or str(now().date())
        amount = _d(payload.get("amount"))
        reference = (payload.get("reference") or "").strip()
        source = (payload.get("source") or "manual").strip()
        account_id = payload.get("account_id")
        allocations = payload.get("allocations") or []

        if not household_id:
            return Response({"detail": "household_id is required"}, status=400)
        if not account_id:
            return Response({"detail": "account_id is required"}, status=400)
        if amount <= 0:
            return Response({"detail": "amount must be > 0"}, status=400)

        try:
            hh = Household.objects.get(id=household_id, school_id=school_id)
        except Household.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        try:
            acct = LedgerAccount.objects.get(id=account_id, school_id=school_id)
        except LedgerAccount.DoesNotExist:
            return Response({"detail": "account_id not found"}, status=400)

        if acct.household_id != hh.id:
            return Response({"detail": "account_id does not match household_id"}, status=400)

        p = Payment.objects.create(
            school_id=school_id,
            account=acct,
            source=source[:32],
            reference=reference[:64],
            amount=amount,
        )

        total_alloc = Decimal("0")
        created_allocs = []

        for a in allocations:
            if not isinstance(a, dict):
                return Response({"detail": "allocations must be objects"}, status=400)

            charge_id = a.get("charge_id")
            a_amt = _d(a.get("amount"))
            if not charge_id or a_amt <= 0:
                return Response(
                    {"detail": "each allocation requires charge_id and amount > 0"}, status=400
                )

            ch = Charge.objects.filter(school_id=school_id, id=charge_id, account=acct).first()
            if not ch:
                return Response({"detail": f"charge_id {charge_id} not found"}, status=400)
            if ch.is_void:
                return Response({"detail": f"charge_id {charge_id} is void"}, status=400)

            total_alloc += a_amt
            if total_alloc > amount:
                return Response({"detail": "allocations exceed payment amount"}, status=400)

            alloc, created = Allocation.objects.get_or_create(
                school_id=school_id,
                payment=p,
                charge=ch,
                defaults={"amount": a_amt},
            )
            if not created:
                alloc.amount = Decimal(str(alloc.amount)) + a_amt
                alloc.save(update_fields=["amount"])

            created_allocs.append(
                {"allocation_id": str(alloc.id), "charge_id": str(ch.id), "amount": str(a_amt)}
            )

        return Response(
            {
                "payment_id": str(p.id),
                "school_id": str(school_id),
                "amount": str(amount),
                "payment_date": str(payment_date),
                "reference": reference,
                "allocations": created_allocs,
            },
            status=201,
        )


class PaymentsApplyView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, payment_id):
        school_id = get_request_school_id(request)
        if not school_id:
            return Response({"detail": "Missing school context"}, status=403)

        p = Payment.objects.select_related("account").filter(school_id=school_id, id=payment_id).first()
        if not p:
            return Response({"detail": "payment not found"}, status=404)

        allocations = (request.data or {}).get("allocations") or []
        if not allocations:
            return Response({"detail": "allocations are required"}, status=400)

        existing_total = (
            Allocation.objects.filter(school_id=school_id, payment_id=p.id)
            .aggregate(total=Sum("amount"))
            .get("total")
        )
        already = _d(existing_total)

        total_new = Decimal("0")
        created_allocs = []

        for a in allocations:
            if not isinstance(a, dict):
                return Response({"detail": "allocations must be objects"}, status=400)

            charge_id = a.get("charge_id")
            a_amt = _d(a.get("amount"))
            if not charge_id or a_amt <= 0:
                return Response(
                    {"detail": "each allocation requires charge_id and amount > 0"}, status=400
                )

            ch = Charge.objects.filter(school_id=school_id, id=charge_id, account=p.account).first()
            if not ch:
                return Response({"detail": f"charge_id {charge_id} not found"}, status=400)
            if ch.is_void:
                return Response({"detail": f"charge_id {charge_id} is void"}, status=400)

            total_new += a_amt
            if already + total_new > _d(p.amount):
                return Response({"detail": "allocations exceed payment amount"}, status=400)

            alloc, created = Allocation.objects.get_or_create(
                school_id=school_id,
                payment=p,
                charge=ch,
                defaults={"amount": a_amt},
            )
            if not created:
                alloc.amount = Decimal(str(alloc.amount)) + a_amt
                alloc.save(update_fields=["amount"])

            created_allocs.append(
                {"allocation_id": str(alloc.id), "charge_id": str(ch.id), "amount": str(a_amt)}
            )

        return Response({"payment_id": str(p.id), "allocations": created_allocs}, status=201)
