from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounting.models import (
    AccountingDimension,
    Budget,
    BudgetLine,
    Fund,
    PayableBill,
    PayableBillLine,
    PurchaseOrder,
    PurchaseOrderLine,
    Vendor,
)
from apps.accounting.reports import (
    balance_sheet,
    budget_vs_actual,
    income_statement,
    trial_balance,
)
from apps.accounting.services.institutional import (
    approve_budget,
    approve_payable_bill,
    approve_purchase_order,
    post_payable_bill,
    submit_purchase_order,
    void_payable_bill,
)
from crown_api.billing_api.permissions import has_finance_runtime_role
from households.scoping import get_request_school_id
from journal.models import GLAccount


def _school_id(request):
    return get_request_school_id(request, required=True)


def _finance_guard(request):
    if not has_finance_runtime_role(request.user):
        return Response({"detail": "Finance role required."}, status=status.HTTP_403_FORBIDDEN)
    return None


def _required_text(data, key):
    value = str(data.get(key) or "").strip()
    if not value:
        raise ValidationError({key: "This field is required."})
    return value


def _decimal(data, key, *, allow_zero=False):
    try:
        value = Decimal(str(data.get(key)))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError({key: "A valid decimal amount is required."})
    if value < 0 or (value == 0 and not allow_zero):
        raise ValidationError({key: "Amount must be positive." if not allow_zero else "Amount cannot be negative."})
    return value.quantize(Decimal("0.01"))


def _date(data, key, *, required=True):
    raw = data.get(key)
    if raw in (None, ""):
        if required:
            raise ValidationError({key: "This field is required."})
        return None
    value = parse_date(str(raw))
    if value is None:
        raise ValidationError({key: "Use ISO date format YYYY-MM-DD."})
    return value


def _account(school_id, account_id):
    account = GLAccount.objects.filter(pk=account_id, school_id=school_id, active=True).first()
    if account is None:
        raise ValidationError({"account_id": "Active account not found for this school."})
    return account


def _fund(school_id, fund_id):
    if not fund_id:
        return None
    value = Fund.objects.filter(pk=fund_id, tenant_id=school_id, active=True).first()
    if value is None:
        raise ValidationError({"fund_id": "Active fund not found for this school."})
    return value


def _dimension(school_id, dimension_id):
    if not dimension_id:
        return None
    value = AccountingDimension.objects.filter(
        pk=dimension_id, tenant_id=school_id, active=True
    ).first()
    if value is None:
        raise ValidationError({"dimension_id": "Active dimension not found for this school."})
    return value


def _error(exc):
    detail = getattr(exc, "message_dict", None) or getattr(exc, "messages", None) or str(exc)
    return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)


def _vendor_json(row):
    return {
        "id": row.id,
        "code": row.code,
        "legal_name": row.legal_name,
        "display_name": row.display_name,
        "email": row.email,
        "phone": row.phone,
        "payment_terms_days": row.payment_terms_days,
        "default_expense_account_id": row.default_expense_account_id,
        "active": row.active,
    }


def _fund_json(row):
    return {
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "restriction": row.restriction,
        "active": row.active,
    }


def _dimension_json(row):
    return {
        "id": row.id,
        "kind": row.kind,
        "code": row.code,
        "name": row.name,
        "active": row.active,
    }


def _po_json(row):
    return {
        "id": row.id,
        "vendor_id": row.vendor_id,
        "number": row.number,
        "status": row.status,
        "ordered_on": row.ordered_on,
        "expected_on": row.expected_on,
        "currency": row.currency,
        "memo": row.memo,
        "total_amount": row.total_amount,
        "approved_by": row.approved_by,
        "approved_at": row.approved_at,
        "lines": [
            {
                "id": line.id,
                "description": line.description,
                "quantity": line.quantity,
                "unit_cost": line.unit_cost,
                "line_total": line.line_total,
                "account_id": line.account_id,
                "fund_id": line.fund_id,
                "dimension_id": line.dimension_id,
            }
            for line in row.lines.select_related("account", "fund", "dimension").all()
        ],
    }


def _bill_json(row):
    return {
        "id": row.id,
        "vendor_id": row.vendor_id,
        "purchase_order_id": row.purchase_order_id,
        "bill_number": row.bill_number,
        "bill_date": row.bill_date,
        "due_date": row.due_date,
        "total_amount": row.total_amount,
        "currency": row.currency,
        "liability_account_id": row.liability_account_id,
        "status": row.status,
        "memo": row.memo,
        "journal_entry_id": row.journal_entry_id,
        "approved_by": row.approved_by,
        "approved_at": row.approved_at,
        "posted_at": row.posted_at,
        "lines": [
            {
                "id": line.id,
                "description": line.description,
                "amount": line.amount,
                "expense_account_id": line.expense_account_id,
                "fund_id": line.fund_id,
                "dimension_id": line.dimension_id,
            }
            for line in row.lines.select_related("expense_account", "fund", "dimension").all()
        ],
    }


def _budget_json(row):
    return {
        "id": row.id,
        "name": row.name,
        "fiscal_start": row.fiscal_start,
        "fiscal_end": row.fiscal_end,
        "status": row.status,
        "approved_by": row.approved_by,
        "approved_at": row.approved_at,
        "total_amount": row.total_amount,
        "lines": [
            {
                "id": line.id,
                "account_id": line.account_id,
                "fund_id": line.fund_id,
                "dimension_id": line.dimension_id,
                "amount": line.amount,
                "note": line.note,
            }
            for line in row.lines.select_related("account", "fund", "dimension").all()
        ],
    }


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def vendors(request):
    denied = _finance_guard(request)
    if denied:
        return denied
    school_id = _school_id(request)
    if request.method == "GET":
        rows = Vendor.objects.filter(tenant_id=school_id).select_related("default_expense_account")
        return Response({"results": [_vendor_json(row) for row in rows]})
    try:
        account = None
        if request.data.get("default_expense_account_id"):
            account = _account(school_id, request.data["default_expense_account_id"])
        row = Vendor.objects.create(
            tenant_id=school_id,
            code=_required_text(request.data, "code"),
            legal_name=_required_text(request.data, "legal_name"),
            display_name=str(request.data.get("display_name") or "").strip(),
            email=str(request.data.get("email") or "").strip(),
            phone=str(request.data.get("phone") or "").strip(),
            payment_terms_days=int(request.data.get("payment_terms_days", 30)),
            default_expense_account=account,
        )
        return Response(_vendor_json(row), status=status.HTTP_201_CREATED)
    except (ValidationError, TypeError, ValueError) as exc:
        return _error(exc)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def funds(request):
    denied = _finance_guard(request)
    if denied:
        return denied
    school_id = _school_id(request)
    if request.method == "GET":
        return Response({"results": [_fund_json(row) for row in Fund.objects.filter(tenant_id=school_id)]})
    try:
        row = Fund.objects.create(
            tenant_id=school_id,
            code=_required_text(request.data, "code"),
            name=_required_text(request.data, "name"),
            restriction=request.data.get("restriction", Fund.Restriction.UNRESTRICTED),
        )
        return Response(_fund_json(row), status=status.HTTP_201_CREATED)
    except ValidationError as exc:
        return _error(exc)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def dimensions(request):
    denied = _finance_guard(request)
    if denied:
        return denied
    school_id = _school_id(request)
    if request.method == "GET":
        return Response({
            "results": [_dimension_json(row) for row in AccountingDimension.objects.filter(tenant_id=school_id)]
        })
    try:
        row = AccountingDimension.objects.create(
            tenant_id=school_id,
            kind=_required_text(request.data, "kind").upper(),
            code=_required_text(request.data, "code"),
            name=_required_text(request.data, "name"),
        )
        return Response(_dimension_json(row), status=status.HTTP_201_CREATED)
    except ValidationError as exc:
        return _error(exc)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def purchase_orders(request):
    denied = _finance_guard(request)
    if denied:
        return denied
    school_id = _school_id(request)
    if request.method == "GET":
        rows = PurchaseOrder.objects.filter(tenant_id=school_id).select_related("vendor").prefetch_related("lines")
        return Response({"results": [_po_json(row) for row in rows]})
    try:
        with transaction.atomic():
            vendor = Vendor.objects.filter(
                pk=request.data.get("vendor_id"), tenant_id=school_id, active=True
            ).first()
            if vendor is None:
                raise ValidationError({"vendor_id": "Active vendor not found for this school."})
            row = PurchaseOrder.objects.create(
                tenant_id=school_id,
                vendor=vendor,
                number=_required_text(request.data, "number"),
                ordered_on=_date(request.data, "ordered_on", required=False) or timezone.localdate(),
                expected_on=_date(request.data, "expected_on", required=False),
                currency=str(request.data.get("currency") or "USD").upper(),
                memo=str(request.data.get("memo") or ""),
                created_by=request.user.id,
            )
            for item in request.data.get("lines") or []:
                PurchaseOrderLine.objects.create(
                    tenant_id=school_id,
                    purchase_order=row,
                    description=_required_text(item, "description"),
                    quantity=_decimal(item, "quantity"),
                    unit_cost=_decimal(item, "unit_cost", allow_zero=True),
                    account=_account(school_id, item.get("account_id")),
                    fund=_fund(school_id, item.get("fund_id")),
                    dimension=_dimension(school_id, item.get("dimension_id")),
                )
            if not row.lines.exists():
                raise ValidationError({"lines": "At least one purchase-order line is required."})
        return Response(_po_json(row), status=status.HTTP_201_CREATED)
    except (ValidationError, TypeError, ValueError) as exc:
        return _error(exc)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def purchase_order_action(request, po_id, action):
    denied = _finance_guard(request)
    if denied:
        return denied
    school_id = _school_id(request)
    row = PurchaseOrder.objects.filter(pk=po_id, tenant_id=school_id).first()
    if row is None:
        return Response({"detail": "Purchase order not found."}, status=status.HTTP_404_NOT_FOUND)
    try:
        if action == "submit":
            row = submit_purchase_order(purchase_order=row)
        elif action == "approve":
            row = approve_purchase_order(purchase_order=row, actor_id=request.user.id)
        else:
            return Response({"detail": "Unsupported purchase-order action."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(_po_json(row))
    except ValidationError as exc:
        return _error(exc)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def payable_bills(request):
    denied = _finance_guard(request)
    if denied:
        return denied
    school_id = _school_id(request)
    if request.method == "GET":
        rows = PayableBill.objects.filter(tenant_id=school_id).select_related(
            "vendor", "purchase_order", "liability_account", "journal_entry"
        ).prefetch_related("lines")
        return Response({"results": [_bill_json(row) for row in rows]})
    try:
        with transaction.atomic():
            vendor = Vendor.objects.filter(
                pk=request.data.get("vendor_id"), tenant_id=school_id, active=True
            ).first()
            if vendor is None:
                raise ValidationError({"vendor_id": "Active vendor not found for this school."})
            po = None
            if request.data.get("purchase_order_id"):
                po = PurchaseOrder.objects.filter(
                    pk=request.data["purchase_order_id"], tenant_id=school_id
                ).first()
                if po is None:
                    raise ValidationError({"purchase_order_id": "Purchase order not found for this school."})
            row = PayableBill.objects.create(
                tenant_id=school_id,
                vendor=vendor,
                purchase_order=po,
                bill_number=_required_text(request.data, "bill_number"),
                bill_date=_date(request.data, "bill_date"),
                due_date=_date(request.data, "due_date"),
                total_amount=_decimal(request.data, "total_amount"),
                currency=str(request.data.get("currency") or "USD").upper(),
                liability_account=_account(school_id, request.data.get("liability_account_id")),
                memo=str(request.data.get("memo") or ""),
                created_by=request.user.id,
            )
            for item in request.data.get("lines") or []:
                PayableBillLine.objects.create(
                    tenant_id=school_id,
                    bill=row,
                    description=_required_text(item, "description"),
                    amount=_decimal(item, "amount"),
                    expense_account=_account(school_id, item.get("expense_account_id")),
                    fund=_fund(school_id, item.get("fund_id")),
                    dimension=_dimension(school_id, item.get("dimension_id")),
                )
            if not row.lines.exists():
                raise ValidationError({"lines": "At least one payable-bill line is required."})
        return Response(_bill_json(row), status=status.HTTP_201_CREATED)
    except (ValidationError, TypeError, ValueError) as exc:
        return _error(exc)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def payable_bill_action(request, bill_id, action):
    denied = _finance_guard(request)
    if denied:
        return denied
    school_id = _school_id(request)
    row = PayableBill.objects.filter(pk=bill_id, tenant_id=school_id).first()
    if row is None:
        return Response({"detail": "Payable bill not found."}, status=status.HTTP_404_NOT_FOUND)
    try:
        if action == "approve":
            row = approve_payable_bill(bill=row, actor_id=request.user.id)
        elif action == "post":
            row = post_payable_bill(bill=row, created_by=request.user)
        elif action == "void":
            row = void_payable_bill(bill=row, reason=str(request.data.get("reason") or ""))
        else:
            return Response({"detail": "Unsupported payable-bill action."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(_bill_json(row))
    except ValidationError as exc:
        return _error(exc)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def budgets(request):
    denied = _finance_guard(request)
    if denied:
        return denied
    school_id = _school_id(request)
    if request.method == "GET":
        rows = Budget.objects.filter(tenant_id=school_id).prefetch_related("lines")
        return Response({"results": [_budget_json(row) for row in rows]})
    try:
        with transaction.atomic():
            row = Budget.objects.create(
                tenant_id=school_id,
                name=_required_text(request.data, "name"),
                fiscal_start=_date(request.data, "fiscal_start"),
                fiscal_end=_date(request.data, "fiscal_end"),
            )
            for item in request.data.get("lines") or []:
                BudgetLine.objects.create(
                    tenant_id=school_id,
                    budget=row,
                    account=_account(school_id, item.get("account_id")),
                    fund=_fund(school_id, item.get("fund_id")),
                    dimension=_dimension(school_id, item.get("dimension_id")),
                    amount=_decimal(item, "amount", allow_zero=True),
                    note=str(item.get("note") or ""),
                )
            if not row.lines.exists():
                raise ValidationError({"lines": "At least one budget line is required."})
        return Response(_budget_json(row), status=status.HTTP_201_CREATED)
    except (ValidationError, TypeError, ValueError) as exc:
        return _error(exc)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def budget_approve(request, budget_id):
    denied = _finance_guard(request)
    if denied:
        return denied
    school_id = _school_id(request)
    row = Budget.objects.filter(pk=budget_id, tenant_id=school_id).first()
    if row is None:
        return Response({"detail": "Budget not found."}, status=status.HTTP_404_NOT_FOUND)
    try:
        return Response(_budget_json(approve_budget(budget=row, actor_id=request.user.id)))
    except ValidationError as exc:
        return _error(exc)


def _report_guard(request):
    denied = _finance_guard(request)
    if denied:
        return None, denied
    return _school_id(request), None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def trial_balance_report(request):
    school_id, denied = _report_guard(request)
    if denied:
        return denied
    try:
        start = _date(request.query_params, "start_date", required=False)
        end = _date(request.query_params, "end_date", required=False)
        return Response(trial_balance(school_id=school_id, start_date=start, end_date=end))
    except ValidationError as exc:
        return _error(exc)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def income_statement_report(request):
    school_id, denied = _report_guard(request)
    if denied:
        return denied
    try:
        start = _date(request.query_params, "start_date")
        end = _date(request.query_params, "end_date")
        if end < start:
            raise ValidationError({"end_date": "End date cannot precede start date."})
        return Response(income_statement(school_id=school_id, start_date=start, end_date=end))
    except ValidationError as exc:
        return _error(exc)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def balance_sheet_report(request):
    school_id, denied = _report_guard(request)
    if denied:
        return denied
    try:
        return Response(balance_sheet(school_id=school_id, as_of=_date(request.query_params, "as_of")))
    except ValidationError as exc:
        return _error(exc)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def budget_variance_report(request, budget_id):
    school_id, denied = _report_guard(request)
    if denied:
        return denied
    row = Budget.objects.filter(pk=budget_id, tenant_id=school_id).first()
    if row is None:
        return Response({"detail": "Budget not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(budget_vs_actual(budget=row))
