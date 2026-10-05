from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from django.utils.timezone import now

from django.db import transaction
from django.db.models import Q, Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from households.models import Guardian, Household, Student
from households.scoping import get_request_school_id

from billing.models import (
    BillingAuditEvent,
    BillingPayer,
    BillingResponsibilityRule,
    Invoice as BillingInvoice,
    InvoicePayerShare,
    PayerAllocationAttribution,
)
from ledger.models import Allocation, Charge, LedgerAccount, Payment

from .permissions import IsFinanceRole


def _d(x) -> Decimal:
    if x is None or x == "":
        return Decimal("0")
    try:
        return Decimal(str(x))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _cents_to_amount(cents) -> Decimal:
    try:
        return (Decimal(int(cents)) / Decimal("100")).quantize(Decimal("0.01"))
    except (TypeError, ValueError, InvalidOperation):
        return Decimal("0.00")


def _amount_to_cents(amount: Decimal) -> int:
    try:
        return int((Decimal(str(amount)) * 100).to_integral_value())
    except Exception:
        return 0


class OpenInvoicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, household_id):
        school_id = get_request_school_id(request)
        if not school_id:
            return Response({"detail": "Missing school context"}, status=403)

        # no-leak: ensure household exists in-scope
        if not Household.objects.filter(pk=household_id, school_id=school_id).exists():
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
            hh = Household.objects.get(pk=household_id, school_id=school_id)
        except Household.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        try:
            acct = LedgerAccount.objects.get(pk=account_id, school_id=school_id)
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


class PaymentsRecordView(APIView):
    permission_classes = [IsAuthenticated, IsFinanceRole]

    @transaction.atomic
    def post(self, request):
        school_id = get_request_school_id(request)
        if not school_id:
            return Response({"detail": "Missing school context"}, status=403)

        payload = request.data or {}
        invoice_id = payload.get("invoice_id")
        household_id = payload.get("household_id")
        amount_cents = payload.get("amount_cents")
        method = (payload.get("method") or "").strip()
        reference = (payload.get("reference") or "").strip()
        received_on_raw = payload.get("received_on")
        allocations = payload.get("allocations")

        # 0110: allocations[] is optional. If present, it drives charge application.
        # If absent, we keep 0108 behavior: invoice_id is required.
        has_allocations = isinstance(allocations, list) and len(allocations) > 0
        if not has_allocations and not invoice_id:
            return Response({"detail": "invoice_id is required"}, status=400)
        if amount_cents is None:
            return Response({"detail": "amount_cents is required"}, status=400)
        try:
            amount_cents_int = int(amount_cents)
        except (TypeError, ValueError):
            return Response({"detail": "amount_cents must be an integer"}, status=400)
        if amount_cents_int <= 0:
            return Response({"detail": "amount_cents must be > 0"}, status=400)
        if not method:
            return Response({"detail": "method is required"}, status=400)

        # 0110: reference is optional, but if provided we enforce idempotency.
        if reference and Payment.objects.filter(school_id=school_id, reference=reference[:64]).exists():
            return Response({"detail": "duplicate reference"}, status=409)

        received_on = None
        if received_on_raw:
            try:
                received_on = date.fromisoformat(str(received_on_raw))
            except ValueError:
                return Response({"detail": "received_on must be YYYY-MM-DD"}, status=400)
        if not received_on:
            received_on = now().date()

        if has_allocations:
            if not household_id:
                return Response({"detail": "household_id is required when allocations are provided"}, status=400)

            # no-leak: ensure household exists in-scope
            if not Household.objects.filter(pk=household_id, school_id=school_id).exists():
                return Response({"detail": "household not found"}, status=404)

            acct = LedgerAccount.objects.filter(school_id=school_id, household_id=household_id).first()
            if not acct:
                return Response({"detail": "ledger account not found for household"}, status=400)

            total_alloc_cents = 0
            parsed_allocs: list[tuple[Charge, Decimal, int]] = []

            for a in allocations:
                if not isinstance(a, dict):
                    return Response({"detail": "allocations must be objects"}, status=400)

                charge_id = a.get("ledger_charge_id")
                a_cents = a.get("amount_cents")
                if not charge_id:
                    return Response({"detail": "each allocation requires ledger_charge_id"}, status=400)
                if a_cents is None:
                    return Response({"detail": "each allocation requires amount_cents"}, status=400)
                try:
                    a_cents_int = int(a_cents)
                except (TypeError, ValueError):
                    return Response({"detail": "allocation amount_cents must be an integer"}, status=400)
                if a_cents_int <= 0:
                    return Response({"detail": "allocation amount_cents must be > 0"}, status=400)

                ch = Charge.objects.filter(school_id=school_id, id=charge_id, account=acct).first()
                if not ch:
                    return Response({"detail": f"ledger_charge_id {charge_id} not found"}, status=400)
                if ch.is_void:
                    return Response({"detail": f"ledger_charge_id {charge_id} is void"}, status=400)

                a_amount = _cents_to_amount(a_cents_int)
                total_alloc_cents += a_cents_int
                parsed_allocs.append((ch, a_amount, a_cents_int))

            if total_alloc_cents != amount_cents_int:
                return Response({"detail": "allocations sum must equal amount_cents"}, status=400)

            payment_amount = _cents_to_amount(amount_cents_int)
            p = Payment.objects.create(
                school_id=school_id,
                account=acct,
                source=(method or "manual")[:32],
                reference=reference[:64],
                amount=payment_amount,
            )

            created_allocs = []
            for ch, a_amount, a_cents_int in parsed_allocs:
                alloc = Allocation.objects.create(
                    school_id=school_id,
                    payment=p,
                    charge=ch,
                    amount=a_amount,
                )
                created_allocs.append(
                    {
                        "allocation_id": str(alloc.id),
                        "ledger_charge_id": str(ch.id),
                        "amount_cents": int(a_cents_int),
                    }
                )

            audit_details = {
                "household_id": str(household_id),
                "amount_cents": int(amount_cents_int),
                "method": method,
                "reference": reference,
                "received_on": received_on.isoformat(),
                "allocations": created_allocs,
            }
            school_override_id = getattr(request, "_crown_school_override_id", None)
            if school_override_id:
                audit_details["school_override_id"] = str(school_override_id)

            BillingAuditEvent.log(
                school_id=school_id,
                entity_type=BillingAuditEvent.ENTITY_PAYMENT,
                entity_id=p.id,
                action="PAYMENT_RECORDED",
                actor_user=getattr(request, "user", None),
                details=audit_details,
            )

            return Response(
                {
                    "payment_id": str(p.id),
                    "household_id": str(household_id),
                    "amount_cents": int(amount_cents_int),
                    "reference": reference,
                    "method": method,
                    "received_on": received_on.isoformat(),
                    "allocations": created_allocs,
                },
                status=201,
            )

        inv = (
            BillingInvoice.objects.select_related("household")
            .filter(school_id=school_id, id=invoice_id)
            .first()
        )
        if not inv:
            return Response({"detail": "invoice not found"}, status=404)

        if not getattr(inv, "ledger_charge_id", None):
            return Response({"detail": "invoice has no linked ledger charge"}, status=400)

        acct = LedgerAccount.objects.filter(school_id=school_id, household_id=inv.household_id).first()
        if not acct:
            return Response({"detail": "ledger account not found for invoice household"}, status=400)

        ch = Charge.objects.filter(school_id=school_id, id=inv.ledger_charge_id, account=acct).first()
        if not ch:
            return Response({"detail": "linked ledger charge not found"}, status=400)
        if ch.is_void:
            return Response({"detail": "linked ledger charge is void"}, status=400)

        amount = _cents_to_amount(amount_cents_int)

        paid_existing = (
            Allocation.objects.filter(school_id=school_id, charge_id=ch.id)
            .aggregate(total=Sum("amount"))
            .get("total")
        )
        paid_existing = _d(paid_existing)
        balance_before = _d(inv.total_amount) - paid_existing
        if balance_before <= 0:
            return Response({"detail": "invoice already paid"}, status=400)

        apply_amount = amount if amount <= balance_before else balance_before

        p = Payment.objects.create(
            school_id=school_id,
            account=acct,
            source=(method or "manual")[:32],
            reference=reference[:64],
            amount=apply_amount,
        )
        Allocation.objects.create(
            school_id=school_id,
            payment=p,
            charge=ch,
            amount=apply_amount,
        )

        # Best-effort audit event (still in transaction so it rolls back on failure).
        audit_details = {
            "payment_id": str(p.id),
            "charge_id": str(ch.id),
            "amount_cents": _amount_to_cents(apply_amount),
            "requested_amount_cents": int(amount_cents_int),
            "method": method,
            "reference": reference,
            "received_on": received_on.isoformat(),
        }
        school_override_id = getattr(request, "_crown_school_override_id", None)
        if school_override_id:
            audit_details["school_override_id"] = str(school_override_id)

        BillingAuditEvent.log(
            school_id=school_id,
            entity_type=BillingAuditEvent.ENTITY_INVOICE,
            entity_id=inv.id,
            action="PAYMENT_RECORDED",
            actor_user=getattr(request, "user", None),
            details=audit_details,
        )

        paid_total = paid_existing + apply_amount
        balance_after = _d(inv.total_amount) - paid_total

        return Response(
            {
                "invoice_id": str(inv.id),
                "payment_id": str(p.id),
                "applied_amount_cents": _amount_to_cents(apply_amount),
                "reference": reference,
                "method": method,
                "received_on": received_on.isoformat(),
                "invoice": {
                    "total_amount": str(_d(inv.total_amount)),
                    "paid_amount": str(paid_total),
                    "balance": str(balance_after),
                    "total_amount_cents": _amount_to_cents(_d(inv.total_amount)),
                    "paid_amount_cents": _amount_to_cents(paid_total),
                    "balance_cents": _amount_to_cents(balance_after),
                },
            },
            status=201,
        )


class HouseholdBillingPayersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, household_id):
        school_id = get_request_school_id(request)
        if not school_id:
            return Response({"detail": "Missing school context"}, status=403)
        if not IsFinanceRole().has_permission(request, self):
            return Response({"detail": IsFinanceRole.message}, status=403)
        if not Household.objects.filter(pk=household_id, school_id=school_id).exists():
            return Response({"detail": "Not found"}, status=404)
        rows = BillingPayer.objects.filter(
            school_id=school_id, household_id=household_id
        ).select_related("guardian", "account").order_by("created_at", "id")
        return Response({
            "household_id": str(household_id),
            "items": [
                {
                    "payer_id": str(row.id),
                    "payer_type": row.payer_type,
                    "display_name": row.display_name or (str(row.guardian) if row.guardian_id else ""),
                    "guardian_id": str(row.guardian_id) if row.guardian_id else None,
                    "account_id": row.account_id,
                    "email": row.email,
                    "is_active": row.is_active,
                }
                for row in rows
            ],
        })

    @transaction.atomic
    def post(self, request, household_id):
        school_id = get_request_school_id(request)
        if not school_id:
            return Response({"detail": "Missing school context"}, status=403)
        if not IsFinanceRole().has_permission(request, self):
            return Response({"detail": IsFinanceRole.message}, status=403)
        household = Household.objects.filter(pk=household_id, school_id=school_id).first()
        if not household:
            return Response({"detail": "Not found"}, status=404)

        payload = request.data or {}
        payer_type = str(payload.get("payer_type") or BillingPayer.PayerType.GUARDIAN)
        guardian_id = payload.get("guardian_id")
        account_id = payload.get("account_id")
        display_name = str(payload.get("display_name") or "").strip()
        email = str(payload.get("email") or "").strip()

        guardian = None
        if guardian_id:
            guardian = Guardian.objects.filter(
                pk=guardian_id, school_id=school_id, household_id=household_id
            ).select_related("account").first()
            if not guardian:
                return Response({"detail": "guardian_id not found in household"}, status=400)
            if account_id and guardian.account_id and str(guardian.account_id) != str(account_id):
                return Response({"detail": "account_id does not match guardian account"}, status=400)
            if not account_id and guardian.account_id:
                account_id = guardian.account_id
            if not display_name:
                display_name = str(guardian)
            if not email:
                email = guardian.email

        if payer_type == BillingPayer.PayerType.GUARDIAN and not guardian:
            return Response({"detail": "guardian payer_type requires guardian_id"}, status=400)
        if not guardian and not display_name:
            return Response({"detail": "display_name is required for non-guardian payers"}, status=400)

        payer = BillingPayer(
            school_id=school_id,
            household=household,
            guardian=guardian,
            account_id=account_id or None,
            payer_type=payer_type,
            display_name=display_name,
            email=email,
        )
        try:
            payer.full_clean()
            payer.save()
        except Exception as exc:
            return Response({"detail": str(exc)}, status=400)

        BillingAuditEvent.log(
            school_id=school_id,
            entity_type="PAYER",
            entity_id=payer.id,
            action="PAYER_CREATED",
            actor_user=getattr(request, "user", None),
            details={"household_id": str(household_id), "payer_type": payer.payer_type},
        )
        return Response({"payer_id": str(payer.id)}, status=201)


class HouseholdBillingResponsibilityRulesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, household_id):
        school_id = get_request_school_id(request)
        if not school_id:
            return Response({"detail": "Missing school context"}, status=403)
        if not IsFinanceRole().has_permission(request, self):
            return Response({"detail": IsFinanceRole.message}, status=403)
        if not Household.objects.filter(pk=household_id, school_id=school_id).exists():
            return Response({"detail": "Not found"}, status=404)
        rows = BillingResponsibilityRule.objects.filter(
            school_id=school_id, household_id=household_id
        ).select_related("payer", "student").order_by("charge_type", "student_id", "created_at", "id")
        return Response({
            "household_id": str(household_id),
            "items": [
                {
                    "rule_id": str(row.id),
                    "payer_id": str(row.payer_id),
                    "student_id": str(row.student_id) if row.student_id else None,
                    "charge_type": row.charge_type,
                    "percentage_bps": row.percentage_bps,
                    "is_active": row.is_active,
                }
                for row in rows
            ],
        })

    @transaction.atomic
    def post(self, request, household_id):
        school_id = get_request_school_id(request)
        if not school_id:
            return Response({"detail": "Missing school context"}, status=403)
        if not IsFinanceRole().has_permission(request, self):
            return Response({"detail": IsFinanceRole.message}, status=403)
        household = Household.objects.filter(pk=household_id, school_id=school_id).first()
        if not household:
            return Response({"detail": "Not found"}, status=404)

        payload = request.data or {}
        payer_id = payload.get("payer_id")
        student_id = payload.get("student_id")
        charge_type = str(payload.get("charge_type") or "TUITION").strip()[:32]
        try:
            percentage_bps = int(payload.get("percentage_bps"))
        except (TypeError, ValueError):
            return Response({"detail": "percentage_bps must be an integer"}, status=400)

        payer = BillingPayer.objects.filter(
            pk=payer_id, school_id=school_id, household_id=household_id, is_active=True
        ).first()
        if not payer:
            return Response({"detail": "payer_id not found in household"}, status=400)

        student = None
        if student_id:
            student = Student.objects.filter(
                pk=student_id, school_id=school_id, household_id=household_id
            ).first()
            if not student:
                return Response({"detail": "student_id not found in household"}, status=400)

        rule = BillingResponsibilityRule(
            school_id=school_id,
            household=household,
            payer=payer,
            student=student,
            charge_type=charge_type,
            percentage_bps=percentage_bps,
        )
        try:
            rule.full_clean()
            rule.save()
        except Exception as exc:
            return Response({"detail": str(exc)}, status=400)

        scope = BillingResponsibilityRule.objects.filter(
            school_id=school_id,
            household_id=household_id,
            charge_type=charge_type,
            is_active=True,
        )
        if student:
            scope = scope.filter(student=student)
        else:
            scope = scope.filter(student__isnull=True)
        configured_bps = scope.aggregate(total=Sum("percentage_bps")).get("total") or 0

        BillingAuditEvent.log(
            school_id=school_id,
            entity_type="PAYER_RULE",
            entity_id=rule.id,
            action="PAYER_RULE_CREATED",
            actor_user=getattr(request, "user", None),
            details={
                "household_id": str(household_id),
                "payer_id": str(payer.id),
                "student_id": str(student.id) if student else None,
                "charge_type": charge_type,
                "percentage_bps": percentage_bps,
                "configured_scope_bps": configured_bps,
            },
        )
        return Response(
            {"rule_id": str(rule.id), "configured_scope_bps": configured_bps},
            status=201,
        )


class MyPayerSharesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school_id = get_request_school_id(request)
        if not school_id:
            return Response({"detail": "Missing school context"}, status=403)

        shares = (
            InvoicePayerShare.objects.filter(
                school_id=school_id,
                payer__is_active=True,
            )
            .filter(
                Q(payer__account=request.user)
                | Q(payer__guardian__account=request.user)
            )
            .select_related("payer", "invoice", "invoice__billing_run")
            .order_by("invoice__due_on", "invoice_id")
            .distinct()
        )

        items = []
        for share in shares:
            attributed = (
                PayerAllocationAttribution.objects.filter(
                    school_id=school_id,
                    share=share,
                ).aggregate(total=Sum("amount")).get("total")
                or Decimal("0.00")
            )
            due = _d(share.amount) - _d(share.waived_amount) - _d(attributed)
            items.append({
                "share_id": str(share.id),
                "invoice_id": str(share.invoice_id),
                "term": share.invoice.billing_run.term,
                "charge_type": share.invoice.billing_run.run_type,
                "due_on": share.invoice.due_on.isoformat() if share.invoice.due_on else None,
                "assigned_amount": str(_d(share.amount)),
                "waived_amount": str(_d(share.waived_amount)),
                "paid_amount": str(_d(attributed)),
                "balance": str(max(due, Decimal("0.00"))),
            })
        return Response({"items": items})


class PayerAllocationAttributionView(APIView):
    permission_classes = [IsAuthenticated, IsFinanceRole]

    @transaction.atomic
    def post(self, request):
        school_id = get_request_school_id(request)
        if not school_id:
            return Response({"detail": "Missing school context"}, status=403)
        payload = request.data or {}
        share_id = payload.get("share_id")
        allocation_id = payload.get("allocation_id")
        amount = _cents_to_amount(payload.get("amount_cents"))
        if amount <= 0:
            return Response({"detail": "amount_cents must be > 0"}, status=400)

        share = (
            InvoicePayerShare.objects.select_related("invoice")
            .filter(pk=share_id, school_id=school_id)
            .first()
        )
        if not share:
            return Response({"detail": "share_id not found"}, status=404)
        allocation = Allocation.objects.filter(pk=allocation_id, school_id=school_id).first()
        if not allocation:
            return Response({"detail": "allocation_id not found"}, status=404)
        if share.invoice.ledger_charge_id != allocation.charge_id:
            return Response({"detail": "allocation does not belong to the share invoice"}, status=400)

        allocated_to_share = (
            PayerAllocationAttribution.objects.filter(
                school_id=school_id, share=share
            ).aggregate(total=Sum("amount")).get("total")
            or Decimal("0.00")
        )
        share_capacity = _d(share.amount) - _d(share.waived_amount) - _d(allocated_to_share)

        attributed_to_allocation = (
            PayerAllocationAttribution.objects.filter(
                school_id=school_id, allocation=allocation
            ).aggregate(total=Sum("amount")).get("total")
            or Decimal("0.00")
        )
        allocation_capacity = _d(allocation.amount) - _d(attributed_to_allocation)

        if amount > share_capacity:
            return Response({"detail": "amount exceeds payer share balance"}, status=400)
        if amount > allocation_capacity:
            return Response({"detail": "amount exceeds unattributed allocation balance"}, status=400)

        attribution = PayerAllocationAttribution(
            school_id=school_id,
            share=share,
            allocation=allocation,
            amount=amount,
        )
        try:
            attribution.full_clean()
            attribution.save()
        except Exception as exc:
            return Response({"detail": str(exc)}, status=400)

        BillingAuditEvent.log(
            school_id=school_id,
            entity_type="PAYER_ATTRIBUTION",
            entity_id=attribution.id,
            action="PAYER_PAYMENT_ATTRIBUTED",
            actor_user=getattr(request, "user", None),
            details={
                "share_id": str(share.id),
                "allocation_id": str(allocation.id),
                "amount_cents": _amount_to_cents(amount),
            },
        )
        return Response({"attribution_id": str(attribution.id)}, status=201)
