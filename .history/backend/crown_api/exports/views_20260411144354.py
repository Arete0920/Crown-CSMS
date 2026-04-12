import csv
import logging
from datetime import date
from typing import Iterable, List

from django.http import StreamingHttpResponse
from django.utils.timezone import now
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from households.scoping import get_request_school_id
from django.core.exceptions import FieldDoesNotExist

from .audit import log_export
from .permissions import IsFinanceRole
from .throttles import ExportIPMinuteThrottle, ExportUserHourThrottle, ExportUserMinuteThrottle

# IMPORTANT:
# These imports must match your actual model locations.
# Adjust ONLY the import lines if your apps are named differently.
from billing.models import Invoice, InstallmentScheduleItem

from .model_resolver import (
    ModelCandidate,
    ModelNotFound,
    resolve_model,
    default_export_fields,
)


EXPORT_AUDIT_LOGGER = logging.getLogger("crown.exports")


def _log_export_access(request, export_name: str, school_id):
    try:
        user = getattr(request, "user", None)
        EXPORT_AUDIT_LOGGER.info(
            "export_access name=%s path=%s school_id=%s user_id=%s",
            export_name,
            getattr(request, "path", ""),
            str(school_id or ""),
            str(getattr(user, "id", "")),
        )
    except Exception:
        # Never break exports on audit logging.
        return


class Echo:
    """An object that implements just the write method of the file-like interface."""

    def write(self, value):
        return value


def _csv_stream(rows: Iterable[List[str]]):
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    for row in rows:
        yield writer.writerow(row)


def _as_iso(d):
    if d is None:
        return ""
    if isinstance(d, (date,)):
        return d.isoformat()
    # datetime
    try:
        return d.date().isoformat()
    except Exception:
        return str(d)


def _as_str(x):
    if x is None:
        return ""
    return str(x)


class InvoicesCSVExportView(APIView):
    """Exports invoices as a flat CSV (school-scoped).

    Filters (optional):
      - household_id
      - due_on_from (YYYY-MM-DD)
      - due_on_to (YYYY-MM-DD)
    """

    permission_classes = [IsAuthenticated, IsFinanceRole]
    throttle_classes = [ExportUserMinuteThrottle, ExportUserHourThrottle, ExportIPMinuteThrottle]

    def get(self, request):
        sid = get_request_school_id(request)
        _log_export_access(request, "invoices.csv", sid)
        if not sid:
            # Stay safe: no scoping => no data
            log_export(request, "invoices.csv", status_code=403, school_id="", row_count=0)
            return StreamingHttpResponse(_csv_stream([]), status=403)

        household_id = request.query_params.get("household_id")
        due_on_from = request.query_params.get("due_on_from")
        due_on_to = request.query_params.get("due_on_to")

        qs = Invoice.objects.filter(school_id=sid).order_by("due_on", "id")

        if household_id:
            qs = qs.filter(household_id=household_id)

        if due_on_from:
            qs = qs.filter(due_on__gte=due_on_from)
        if due_on_to:
            qs = qs.filter(due_on__lte=due_on_to)

        header = [
            "invoice_id",
            "household_id",
            "due_on",
            "issued_on",
            "status",
            "currency",
            "total_amount",
            "amount_due",
            "ledger_charge_id",
            "installment_plan_id",
            "installment_schedule_item_id",
            "created_at",
            "updated_at",
        ]

        def rows():
            yield header
            for inv in qs.iterator():
                yield [
                    _as_str(inv.id),
                    _as_str(getattr(inv, "household_id", "")),
                    _as_iso(getattr(inv, "due_on", None)),
                    _as_iso(getattr(inv, "issued_on", None)),
                    _as_str(getattr(inv, "status", "")),
                    _as_str(getattr(inv, "currency", "")),
                    _as_str(getattr(inv, "total_amount", "")),
                    _as_str(getattr(inv, "amount_due", "")),
                    _as_str(getattr(inv, "ledger_charge_id", "")),
                    _as_str(getattr(inv, "installment_plan_id", "")),
                    _as_str(getattr(inv, "installment_schedule_item_id", "")),
                    _as_iso(getattr(inv, "created_at", None)),
                    _as_iso(getattr(inv, "updated_at", None)),
                ]

        row_count = None
        try:
            row_count = qs.count()
        except Exception:
            row_count = None

        filename = f"invoices_{now().date().isoformat()}.csv"
        resp = StreamingHttpResponse(_csv_stream(rows()), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        log_export(request, "invoices.csv", status_code=200, school_id=str(sid or ""), row_count=row_count)
        return resp


class InstallmentScheduleCSVExportView(APIView):
    """Exports installment schedule items as flat CSV (school-scoped).

    Filters (optional):
      - household_id
      - plan_id
    """

    permission_classes = [IsAuthenticated, IsFinanceRole]
    throttle_classes = [ExportUserMinuteThrottle, ExportUserHourThrottle, ExportIPMinuteThrottle]

    def get(self, request):
        sid = get_request_school_id(request)
        _log_export_access(request, "installment-schedule.csv", sid)
        if not sid:
            log_export(request, "installment-schedule.csv", status_code=403, school_id="", row_count=0)
            return StreamingHttpResponse(_csv_stream([]), status=403)

        household_id = request.query_params.get("household_id")
        plan_id = request.query_params.get("plan_id")

        qs = (
            InstallmentScheduleItem.objects.select_related("plan", "invoice")
            .filter(school_id=sid)
            .order_by("due_on", "id")
        )

        if plan_id:
            qs = qs.filter(plan_id=plan_id)

        if household_id:
            qs = qs.filter(household_id=household_id)

        header = [
            "schedule_item_id",
            "plan_id",
            "household_id",
            "due_on",
            "amount",
            "invoice_id",
            "ledger_charge_id",
            "status",
            "created_at",
            "updated_at",
        ]

        def rows():
            yield header
            for item in qs.iterator():
                inv = getattr(item, "invoice", None)
                yield [
                    _as_str(item.id),
                    _as_str(getattr(item, "plan_id", "")),
                    _as_str(getattr(item, "household_id", "")),
                    _as_iso(getattr(item, "due_on", None)),
                    _as_str(getattr(item, "amount", "")),
                    _as_str(getattr(item, "invoice_id", "")),
                    _as_str(getattr(inv, "ledger_charge_id", "") if inv else ""),
                    _as_str(getattr(item, "status", "")),
                    _as_iso(getattr(item, "created_at", None)),
                    _as_iso(getattr(item, "updated_at", None)),
                ]

        row_count = None
        try:
            row_count = qs.count()
        except Exception:
            row_count = None

        filename = f"installment_schedule_{now().date().isoformat()}.csv"
        resp = StreamingHttpResponse(_csv_stream(rows()), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        log_export(request, "installment-schedule.csv", status_code=200, school_id=str(sid or ""), row_count=row_count)
        return resp


def _safe_str(x):
    if x is None:
        return ""
    return str(x)


def _model_has_field(model, name: str) -> bool:
    try:
        model._meta.get_field(name)
        return True
    except FieldDoesNotExist:
        return False


class _BaseModelCSVExportView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ExportUserMinuteThrottle, ExportUserHourThrottle, ExportIPMinuteThrottle]

    # override in subclasses
    model_candidates: list[ModelCandidate] = []
    filename_prefix: str = "export"
    order_by: list[str] = ["id"]

    def get_queryset(self, model):
        qs = model.objects.order_by("id")

        sid = get_request_school_id(self.request)
        if _model_has_field(model, "school_id"):
            if not sid:
                return model.objects.none()
            qs = qs.filter(school_id=sid)

        # apply simple ordering if fields exist
        for field in self.order_by:
            try:
                qs = qs.order_by(field)
                break
            except Exception:
                continue
        return qs

    def get(self, request):
        try:
            model = resolve_model(self.model_candidates)
        except ModelNotFound as e:
            resp = StreamingHttpResponse(
                _csv_stream([["error"], [str(e)]]),
                content_type="text/csv; charset=utf-8",
                status=500,
            )
            resp["Content-Disposition"] = 'attachment; filename="error.csv"'
            log_export(request, f"{self.filename_prefix}.csv", status_code=500, school_id=str(get_request_school_id(request) or ""))
            return resp

        sid = get_request_school_id(request)
        _log_export_access(request, f"{self.filename_prefix}.csv", sid)
        if _model_has_field(model, "school_id") and not sid:
            # Stay safe: a school-scoped model without a school context => no data.
            log_export(request, f"{self.filename_prefix}.csv", status_code=403, school_id="", row_count=0)
            return StreamingHttpResponse(_csv_stream([]), status=403)

        fields = default_export_fields(model)
        qs = self.get_queryset(model)

        row_count = None
        try:
            row_count = qs.count()
        except Exception:
            row_count = None

        def rows():
            yield fields
            for obj in qs.iterator():
                row = []
                for f in fields:
                    try:
                        row.append(_safe_str(getattr(obj, f)))
                    except Exception:
                        row.append("")
                yield row

        filename = f"{self.filename_prefix}_{now().date().isoformat()}.csv"
        resp = StreamingHttpResponse(_csv_stream(rows()), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        log_export(request, f"{self.filename_prefix}.csv", status_code=200, school_id=str(sid or ""), row_count=row_count)
        return resp


class HouseholdsCSVExportView(_BaseModelCSVExportView):
    """0091: Households export."""

    filename_prefix = "households"
    order_by = ["id"]

    model_candidates = [
        ModelCandidate("households", "Household"),
        ModelCandidate("core", "Household"),
        ModelCandidate("students", "Household"),
        ModelCandidate("people", "Household"),
    ]


class StudentsCSVExportView(_BaseModelCSVExportView):
    """0091: Students export."""

    filename_prefix = "students"
    order_by = ["last_name", "id"]

    model_candidates = [
        ModelCandidate("students", "Student"),
        ModelCandidate("core", "Student"),
        ModelCandidate("people", "Student"),
        ModelCandidate("sis", "Student"),
    ]


class StaffCSVExportView(_BaseModelCSVExportView):
    """0091: Staff export."""

    filename_prefix = "staff"
    order_by = ["last_name", "id"]

    model_candidates = [
        ModelCandidate("staff", "StaffMember"),
        ModelCandidate("staff", "Staff"),
        ModelCandidate("core", "StaffMember"),
        ModelCandidate("core", "Staff"),
        ModelCandidate("people", "StaffMember"),
        ModelCandidate("people", "Staff"),
    ]


class LedgerChargesCSVExportView(_BaseModelCSVExportView):
    """0092: Ledger Charges export (A/R charges).

    Optional query params:
      - household_id
      - invoice_id
      - due_on_from (YYYY-MM-DD)
      - due_on_to (YYYY-MM-DD)
    """

    permission_classes = [IsAuthenticated, IsFinanceRole]

    filename_prefix = "ledger_charges"
    order_by = ["posted_on", "due_on", "id"]

    model_candidates = [
        ModelCandidate("ledger", "LedgerCharge"),
        ModelCandidate("accounting", "LedgerCharge"),
        ModelCandidate("billing", "LedgerCharge"),
        ModelCandidate("finance", "LedgerCharge"),
        ModelCandidate("ledger", "Charge"),
        ModelCandidate("accounting", "Charge"),
    ]

    def get_queryset(self, model):
        field_names = {f.name for f in model._meta.get_fields() if getattr(f, "concrete", False)}
        self.order_by = [f for f in self.order_by if f in field_names] + ["id"]

        qs = super().get_queryset(model)

        household_id = self.request.query_params.get("household_id")
        invoice_id = self.request.query_params.get("invoice_id")
        due_on_from = self.request.query_params.get("due_on_from")
        due_on_to = self.request.query_params.get("due_on_to")

        if household_id and "household_id" in field_names:
            qs = qs.filter(household_id=household_id)

        if invoice_id and "invoice_id" in field_names:
            qs = qs.filter(invoice_id=invoice_id)

        if due_on_from and "due_on" in field_names:
            qs = qs.filter(due_on__gte=due_on_from)

        if due_on_to and "due_on" in field_names:
            qs = qs.filter(due_on__lte=due_on_to)

        return qs


class LedgerAllocationsCSVExportView(_BaseModelCSVExportView):
    """0092: Allocations export (payment allocations to charges/invoices).

    Optional query params:
      - household_id
      - payment_id
      - charge_id
      - applied_on_from (YYYY-MM-DD)
      - applied_on_to (YYYY-MM-DD)
    """

    permission_classes = [IsAuthenticated, IsFinanceRole]

    filename_prefix = "ledger_allocations"
    order_by = ["applied_on", "id"]

    model_candidates = [
        ModelCandidate("ledger", "LedgerAllocation"),
        ModelCandidate("accounting", "LedgerAllocation"),
        ModelCandidate("billing", "LedgerAllocation"),
        ModelCandidate("finance", "LedgerAllocation"),
        ModelCandidate("ledger", "Allocation"),
        ModelCandidate("accounting", "Allocation"),
    ]

    def get_queryset(self, model):
        field_names = {f.name for f in model._meta.get_fields() if getattr(f, "concrete", False)}
        self.order_by = [f for f in self.order_by if f in field_names] + ["id"]

        qs = super().get_queryset(model)

        household_id = self.request.query_params.get("household_id")
        payment_id = self.request.query_params.get("payment_id")
        charge_id = self.request.query_params.get("charge_id")
        applied_on_from = self.request.query_params.get("applied_on_from")
        applied_on_to = self.request.query_params.get("applied_on_to")

        if household_id and "household_id" in field_names:
            qs = qs.filter(household_id=household_id)

        if payment_id and "payment_id" in field_names:
            qs = qs.filter(payment_id=payment_id)

        if charge_id:
            if "ledger_charge_id" in field_names:
                qs = qs.filter(ledger_charge_id=charge_id)
            elif "charge_id" in field_names:
                qs = qs.filter(charge_id=charge_id)

        if applied_on_from and "applied_on" in field_names:
            qs = qs.filter(applied_on__gte=applied_on_from)

        if applied_on_to and "applied_on" in field_names:
            qs = qs.filter(applied_on__lte=applied_on_to)

        return qs


class PaymentsCSVExportView(_BaseModelCSVExportView):
    """0092: Payments export (cash receipts).

    Optional query params:
      - household_id
      - posted_on_from (YYYY-MM-DD)
      - posted_on_to (YYYY-MM-DD)
      - method
      - status
    """

    permission_classes = [IsAuthenticated, IsFinanceRole]

    filename_prefix = "payments"
    order_by = ["posted_on", "received_on", "id"]

    model_candidates = [
        ModelCandidate("payments", "Payment"),
        ModelCandidate("ledger", "Payment"),
        ModelCandidate("billing", "Payment"),
        ModelCandidate("finance", "Payment"),
        ModelCandidate("accounting", "Payment"),
    ]

    def get_queryset(self, model):
        field_names = {f.name for f in model._meta.get_fields() if getattr(f, "concrete", False)}
        self.order_by = [f for f in self.order_by if f in field_names] + ["id"]

        qs = super().get_queryset(model)

        household_id = self.request.query_params.get("household_id")
        posted_on_from = self.request.query_params.get("posted_on_from")
        posted_on_to = self.request.query_params.get("posted_on_to")
        method = self.request.query_params.get("method")
        status = self.request.query_params.get("status")

        if household_id and "household_id" in field_names:
            qs = qs.filter(household_id=household_id)

        if posted_on_from:
            if "posted_on" in field_names:
                qs = qs.filter(posted_on__gte=posted_on_from)
            elif "received_on" in field_names:
                qs = qs.filter(received_on__gte=posted_on_from)

        if posted_on_to:
            if "posted_on" in field_names:
                qs = qs.filter(posted_on__lte=posted_on_to)
            elif "received_on" in field_names:
                qs = qs.filter(received_on__lte=posted_on_to)

        if method and "method" in field_names:
            qs = qs.filter(method=method)

        if status and "status" in field_names:
            qs = qs.filter(status=status)

        return qs


from decimal import Decimal, InvalidOperation

from django.db.models import Sum


def _to_decimal(x) -> Decimal:
    if x is None or x == "":
        return Decimal("0")
    try:
        return Decimal(str(x))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _field_names(model) -> set[str]:
    return {f.name for f in model._meta.get_fields() if getattr(f, "concrete", False)}


def _pick_first(existing: set[str], options: list[str]) -> str | None:
    for o in options:
        if o in existing:
            return o
    return None


class StatementsCSVExportView(APIView):
    """0093: Household Statements (as-of) export.

    Output is ONE ROW PER INVOICE, enriched with:
      - paid_amount (from allocations if ledger models exist)
      - balance (amount_due - paid_amount)

    Query params:
      - household_id (optional)
      - as_of (YYYY-MM-DD, optional; defaults to today)
      - due_on_from (optional)
      - due_on_to (optional)
      - status (optional)
    """

    permission_classes = [IsAuthenticated, IsFinanceRole]
    throttle_classes = [ExportUserMinuteThrottle, ExportUserHourThrottle, ExportIPMinuteThrottle]

    invoice_candidates = [
        ModelCandidate("billing", "Invoice"),
        ModelCandidate("finance", "Invoice"),
        ModelCandidate("ledger", "Invoice"),
        ModelCandidate("accounting", "Invoice"),
    ]

    allocation_candidates = [
        ModelCandidate("ledger", "LedgerAllocation"),
        ModelCandidate("accounting", "LedgerAllocation"),
        ModelCandidate("billing", "LedgerAllocation"),
        ModelCandidate("finance", "LedgerAllocation"),
        ModelCandidate("ledger", "Allocation"),
        ModelCandidate("accounting", "Allocation"),
    ]

    def get(self, request):
        household_id = request.query_params.get("household_id")
        as_of = request.query_params.get("as_of")  # YYYY-MM-DD
        due_on_from = request.query_params.get("due_on_from")
        due_on_to = request.query_params.get("due_on_to")
        status_filter = request.query_params.get("status")

        # Resolve Invoice model (required)
        try:
            InvoiceModel = resolve_model(self.invoice_candidates)
        except ModelNotFound as e:
            resp = StreamingHttpResponse(
                _csv_stream([["error"], [str(e)]]),
                content_type="text/csv; charset=utf-8",
                status=500,
            )
            resp["Content-Disposition"] = 'attachment; filename="error.csv"'
            log_export(request, "statements.csv", status_code=500, school_id=str(get_request_school_id(request) or ""))
            return resp

        inv_fields = _field_names(InvoiceModel)
        qs = InvoiceModel.objects.order_by("id")

        # Tenant safety: apply school scoping if possible.
        sid = get_request_school_id(request)
        _log_export_access(request, "statements.csv", sid)
        if "school_id" in inv_fields:
            if not sid:
                log_export(request, "statements.csv", status_code=403, school_id="", row_count=0)
                return StreamingHttpResponse(_csv_stream([]), status=403)
            qs = qs.filter(school_id=sid)

        # Household filter if field exists
        if household_id and "household_id" in inv_fields:
            qs = qs.filter(household_id=household_id)

        # as_of cutoff only if due_on exists
        if as_of and "due_on" in inv_fields:
            qs = qs.filter(due_on__lte=as_of)

        if due_on_from and "due_on" in inv_fields:
            qs = qs.filter(due_on__gte=due_on_from)
        if due_on_to and "due_on" in inv_fields:
            qs = qs.filter(due_on__lte=due_on_to)

        if status_filter and "status" in inv_fields:
            qs = qs.filter(status=status_filter)

        # Stable ordering
        if "due_on" in inv_fields:
            qs = qs.order_by("due_on", "id")
        else:
            qs = qs.order_by("id")

        # Optional: resolve Allocation model
        AllocationModel = None
        alloc_fields: set[str] = set()
        try:
            AllocationModel = resolve_model(self.allocation_candidates)
            alloc_fields = _field_names(AllocationModel)
        except ModelNotFound:
            AllocationModel = None

        inv_has_ledger_charge_id = "ledger_charge_id" in inv_fields
        inv_total_field = _pick_first(inv_fields, ["total_amount", "amount_total", "amount"])
        inv_due_field = _pick_first(inv_fields, ["amount_due", "balance_due", "due_amount"])
        inv_status_field = "status" if "status" in inv_fields else None
        inv_due_on_field = "due_on" if "due_on" in inv_fields else None
        inv_issued_on_field = "issued_on" if "issued_on" in inv_fields else None

        alloc_amount_field = (
            _pick_first(alloc_fields, ["amount", "applied_amount", "allocated_amount"]) if AllocationModel else None
        )
        alloc_charge_link = _pick_first(alloc_fields, ["ledger_charge_id", "charge_id"]) if AllocationModel else None

        paid_by_charge: dict[str, Decimal] = {}
        if AllocationModel and alloc_amount_field and alloc_charge_link:
            alloc_qs = AllocationModel.objects.order_by("id")

            # Apply school scoping to allocations if possible.
            if "school_id" in alloc_fields and sid:
                alloc_qs = alloc_qs.filter(school_id=sid)

            # Apply as_of cutoff to allocations if possible.
            if as_of and "applied_on" in alloc_fields:
                alloc_qs = alloc_qs.filter(applied_on__lte=as_of)

            agg = alloc_qs.values(alloc_charge_link).annotate(paid=Sum(alloc_amount_field))
            for row in agg.iterator():
                cid = row.get(alloc_charge_link)
                if cid is None:
                    continue
                paid_by_charge[str(cid)] = _to_decimal(row.get("paid"))

        header = [
            "as_of",
            "household_id",
            "invoice_id",
            "due_on",
            "issued_on",
            "status",
            "total_amount",
            "amount_due",
            "ledger_charge_id",
            "paid_amount",
            "balance",
        ]

        def rows():
            as_of_val = as_of or now().date().isoformat()
            yield header
            for inv in qs.iterator():
                inv_id = getattr(inv, "id", "")
                hh_id = getattr(inv, "household_id", "") if "household_id" in inv_fields else ""
                due_on_val = getattr(inv, inv_due_on_field, "") if inv_due_on_field else ""
                issued_on_val = getattr(inv, inv_issued_on_field, "") if inv_issued_on_field else ""
                status_val = getattr(inv, inv_status_field, "") if inv_status_field else ""

                total_val = getattr(inv, inv_total_field, "") if inv_total_field else ""
                due_val = getattr(inv, inv_due_field, "") if inv_due_field else ""

                ledger_charge_id = getattr(inv, "ledger_charge_id", "") if inv_has_ledger_charge_id else ""
                paid = paid_by_charge.get(str(ledger_charge_id), Decimal("0")) if ledger_charge_id not in ("", None) else Decimal("0")

                amount_due_dec = _to_decimal(due_val)
                balance = amount_due_dec - paid

                yield [
                    str(as_of_val),
                    str(hh_id),
                    str(inv_id),
                    str(due_on_val) if due_on_val is not None else "",
                    str(issued_on_val) if issued_on_val is not None else "",
                    str(status_val),
                    str(total_val),
                    str(due_val),
                    str(ledger_charge_id),
                    str(paid),
                    str(balance),
                ]

        row_count = None
        try:
            row_count = qs.count()
        except Exception:
            row_count = None

        filename = f"statements_{(as_of or now().date().isoformat())}.csv"
        resp = StreamingHttpResponse(_csv_stream(rows()), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        log_export(request, "statements.csv", status_code=200, school_id=str(sid or ""), row_count=row_count)
        return resp


class StatementLinesCSVExportView(APIView):
    """0094: Statement lines export (detail).

    Priority:
      1) Allocation lines (best) -> one row per allocation
      2) Charge lines -> one row per charge
      3) Invoice lines -> one row per invoice (fallback)

    Query params (optional):
      - household_id
      - as_of (YYYY-MM-DD)
      - due_on_from (YYYY-MM-DD)
      - due_on_to (YYYY-MM-DD)
    """

    permission_classes = [IsAuthenticated, IsFinanceRole]
    throttle_classes = [ExportUserMinuteThrottle, ExportUserHourThrottle, ExportIPMinuteThrottle]

    invoice_candidates = [
        ModelCandidate("billing", "Invoice"),
        ModelCandidate("finance", "Invoice"),
        ModelCandidate("ledger", "Invoice"),
        ModelCandidate("accounting", "Invoice"),
    ]

    charge_candidates = [
        ModelCandidate("ledger", "LedgerCharge"),
        ModelCandidate("accounting", "LedgerCharge"),
        ModelCandidate("billing", "LedgerCharge"),
        ModelCandidate("finance", "LedgerCharge"),
        ModelCandidate("ledger", "Charge"),
        ModelCandidate("accounting", "Charge"),
    ]

    allocation_candidates = [
        ModelCandidate("ledger", "LedgerAllocation"),
        ModelCandidate("accounting", "LedgerAllocation"),
        ModelCandidate("billing", "LedgerAllocation"),
        ModelCandidate("finance", "LedgerAllocation"),
        ModelCandidate("ledger", "Allocation"),
        ModelCandidate("accounting", "Allocation"),
    ]

    payment_candidates = [
        ModelCandidate("payments", "Payment"),
        ModelCandidate("ledger", "Payment"),
        ModelCandidate("billing", "Payment"),
        ModelCandidate("finance", "Payment"),
        ModelCandidate("accounting", "Payment"),
    ]

    def get(self, request):
        household_id = request.query_params.get("household_id")
        as_of = request.query_params.get("as_of")  # YYYY-MM-DD
        due_on_from = request.query_params.get("due_on_from")
        due_on_to = request.query_params.get("due_on_to")

        # Resolve Invoice (required)
        try:
            InvoiceModel = resolve_model(self.invoice_candidates)
        except ModelNotFound as e:
            resp = StreamingHttpResponse(
                _csv_stream([["error"], [str(e)]]),
                content_type="text/csv; charset=utf-8",
                status=500,
            )
            resp["Content-Disposition"] = 'attachment; filename="error.csv"'
            log_export(request, "statement-lines.csv", status_code=500, school_id=str(get_request_school_id(request) or ""))
            return resp

        inv_fields = _field_names(InvoiceModel)

        # Tenant/school scoping (mirrors 0093 behavior)
        school_id = None
        if "school_id" in inv_fields:
            school_id = get_request_school_id(request)
            _log_export_access(request, "statement-lines.csv", school_id)
            if not school_id:
                resp = StreamingHttpResponse(
                    _csv_stream([["error"], ["Missing school context"]]),
                    content_type="text/csv; charset=utf-8",
                    status=403,
                )
                resp["Content-Disposition"] = 'attachment; filename="error.csv"'
                log_export(request, "statement-lines.csv", status_code=403, school_id="", row_count=0)
                return resp
        else:
            _log_export_access(request, "statement-lines.csv", "")

        # Build base invoice queryset for scope + optional filters
        inv_qs = InvoiceModel.objects.order_by("id")
        if "school_id" in inv_fields and school_id:
            inv_qs = inv_qs.filter(school_id=school_id)

        if household_id and "household_id" in inv_fields:
            inv_qs = inv_qs.filter(household_id=household_id)

        if as_of and "due_on" in inv_fields:
            inv_qs = inv_qs.filter(due_on__lte=as_of)

        if due_on_from and "due_on" in inv_fields:
            inv_qs = inv_qs.filter(due_on__gte=due_on_from)
        if due_on_to and "due_on" in inv_fields:
            inv_qs = inv_qs.filter(due_on__lte=due_on_to)

        if "due_on" in inv_fields:
            inv_qs = inv_qs.order_by("due_on", "id")
        else:
            inv_qs = inv_qs.order_by("id")

        # Resolve optional models
        ChargeModel = None
        AllocationModel = None
        PaymentModel = None
        charge_fields: set[str] = set()
        alloc_fields: set[str] = set()
        pay_fields: set[str] = set()

        try:
            ChargeModel = resolve_model(self.charge_candidates)
            charge_fields = _field_names(ChargeModel)
        except ModelNotFound:
            ChargeModel = None

        try:
            AllocationModel = resolve_model(self.allocation_candidates)
            alloc_fields = _field_names(AllocationModel)
        except ModelNotFound:
            AllocationModel = None

        try:
            PaymentModel = resolve_model(self.payment_candidates)
            pay_fields = _field_names(PaymentModel)
        except ModelNotFound:
            PaymentModel = None

        # Determine key invoice fields
        inv_due_on_field = "due_on" if "due_on" in inv_fields else None
        inv_status_field = "status" if "status" in inv_fields else None
        inv_total_field = _pick_first(inv_fields, ["total_amount", "amount_total", "amount"])
        inv_due_field = _pick_first(inv_fields, ["amount_due", "balance_due", "due_amount"])
        inv_has_charge_link = "ledger_charge_id" in inv_fields

        invoice_by_charge: dict[int, dict[str, object]] = {}
        charge_ids_for_map: set[int] = set()

        if inv_has_charge_link:
            for inv in inv_qs.iterator():
                cid = getattr(inv, "ledger_charge_id", None)
                if cid in (None, ""):
                    continue
                try:
                    cid_int = int(cid)
                except Exception:
                    continue

                charge_ids_for_map.add(cid_int)
                invoice_by_charge[cid_int] = {
                    "invoice_id": getattr(inv, "id", ""),
                    "household_id": getattr(inv, "household_id", "") if "household_id" in inv_fields else "",
                    "invoice_due_on": getattr(inv, inv_due_on_field, "") if inv_due_on_field else "",
                    "invoice_status": getattr(inv, inv_status_field, "") if inv_status_field else "",
                    "invoice_total": getattr(inv, inv_total_field, "") if inv_total_field else "",
                    "invoice_amount_due": getattr(inv, inv_due_field, "") if inv_due_field else "",
                    "ledger_charge_id": cid_int,
                }

        # Optionally build charge map for enrichment
        charge_map: dict[int, dict[str, object]] = {}
        if ChargeModel and charge_ids_for_map:
            charge_amount_field = _pick_first(charge_fields, ["amount", "charge_amount", "total_amount"])
            charge_due_on_field = _pick_first(charge_fields, ["due_on", "due_date"])
            charge_posted_on_field = _pick_first(charge_fields, ["posted_on", "created_on", "created_at"])

            ch_qs = ChargeModel.objects.filter(pk__in=charge_ids_for_map)
            if "school_id" in charge_fields and school_id:
                ch_qs = ch_qs.filter(school_id=school_id)

            for ch in ch_qs.iterator():
                cid = getattr(ch, "id", None)
                if cid is None:
                    continue
                try:
                    cid_int = int(cid)
                except Exception:
                    continue
                charge_map[cid_int] = {
                    "charge_id": cid_int,
                    "charge_amount": getattr(ch, charge_amount_field, "") if charge_amount_field else "",
                    "charge_due_on": getattr(ch, charge_due_on_field, "") if charge_due_on_field else "",
                    "charge_posted_on": getattr(ch, charge_posted_on_field, "") if charge_posted_on_field else "",
                }

        # Payment enrichment (optional)
        payment_map: dict[int, dict[str, object]] = {}
        if PaymentModel and "id" in pay_fields and AllocationModel and charge_ids_for_map:
            alloc_payment_link = _pick_first(alloc_fields, ["payment_id"])
            alloc_charge_link = _pick_first(alloc_fields, ["ledger_charge_id", "charge_id"])

            if alloc_payment_link and alloc_charge_link:
                pay_method_field = _pick_first(pay_fields, ["method", "payment_method"])
                pay_status_field = _pick_first(pay_fields, ["status"])
                pay_received_on_field = _pick_first(pay_fields, ["received_on", "posted_on", "created_at"])

                alloc_ids_qs = AllocationModel.objects.order_by("id")
                if "school_id" in alloc_fields and school_id:
                    alloc_ids_qs = alloc_ids_qs.filter(school_id=school_id)
                if as_of and "applied_on" in alloc_fields:
                    alloc_ids_qs = alloc_ids_qs.filter(applied_on__lte=as_of)

                alloc_ids_qs = alloc_ids_qs.filter(**{f"{alloc_charge_link}__in": list(charge_ids_for_map)})
                payment_ids = (
                    alloc_ids_qs.exclude(**{alloc_payment_link: None})
                    .values_list(alloc_payment_link, flat=True)
                    .distinct()
                )

                pid_set: set[int] = set()
                for pid in payment_ids.iterator():
                    try:
                        pid_set.add(int(pid))
                    except Exception:
                        continue

                if pid_set:
                    pqs = PaymentModel.objects.filter(pk__in=pid_set)
                    if "school_id" in pay_fields and school_id:
                        pqs = pqs.filter(school_id=school_id)

                    for p in pqs.iterator():
                        pid = getattr(p, "id", None)
                        if pid is None:
                            continue
                        try:
                            pid_int = int(pid)
                        except Exception:
                            continue
                        payment_map[pid_int] = {
                            "payment_id": pid_int,
                            "payment_method": getattr(p, pay_method_field, "") if pay_method_field else "",
                            "payment_status": getattr(p, pay_status_field, "") if pay_status_field else "",
                            "payment_received_on": getattr(p, pay_received_on_field, "") if pay_received_on_field else "",
                        }

        header = [
            "as_of",
            "school_id",
            "household_id",
            "invoice_id",
            "invoice_due_on",
            "invoice_status",
            "invoice_total",
            "invoice_amount_due",
            "ledger_charge_id",
            "charge_amount",
            "charge_due_on",
            "charge_posted_on",
            "allocation_id",
            "applied_on",
            "allocation_amount",
            "payment_id",
            "payment_method",
            "payment_status",
            "payment_received_on",
            "row_type",
        ]

        as_of_val = as_of or now().date().isoformat()

        def rows():
            yield header

            # 1) Allocation lines (best)
            if AllocationModel and charge_ids_for_map:
                alloc_amount_field = _pick_first(alloc_fields, ["amount", "applied_amount", "allocated_amount"])
                alloc_applied_on_field = _pick_first(alloc_fields, ["applied_on", "posted_on", "created_at"])
                alloc_charge_link = _pick_first(alloc_fields, ["ledger_charge_id", "charge_id"])
                alloc_payment_link = _pick_first(alloc_fields, ["payment_id"])

                if alloc_amount_field and alloc_charge_link:
                    alloc_qs = AllocationModel.objects.order_by("id")

                    alloc_qs = alloc_qs.filter(**{f"{alloc_charge_link}__in": list(charge_ids_for_map)})

                    if "school_id" in alloc_fields and school_id:
                        alloc_qs = alloc_qs.filter(school_id=school_id)

                    if as_of and "applied_on" in alloc_fields:
                        alloc_qs = alloc_qs.filter(applied_on__lte=as_of)

                    if alloc_applied_on_field and alloc_applied_on_field in alloc_fields:
                        alloc_qs = alloc_qs.order_by(alloc_applied_on_field, "id")
                    else:
                        alloc_qs = alloc_qs.order_by("id")

                    for a in alloc_qs.iterator():
                        alloc_id = getattr(a, "id", "")
                        charge_id = getattr(a, alloc_charge_link, None)
                        try:
                            charge_id_int = int(charge_id) if charge_id is not None else None
                        except Exception:
                            charge_id_int = None

                        inv_info = invoice_by_charge.get(charge_id_int, {}) if charge_id_int is not None else {}
                        ch_info = charge_map.get(charge_id_int, {}) if charge_id_int is not None else {}

                        allocation_amount = getattr(a, alloc_amount_field, "")
                        applied_on = getattr(a, alloc_applied_on_field, "") if alloc_applied_on_field else ""

                        payment_id_val: object = ""
                        pay_info: dict[str, object] = {}
                        if alloc_payment_link:
                            pid = getattr(a, alloc_payment_link, None)
                            try:
                                pid_int = int(pid) if pid is not None else None
                            except Exception:
                                pid_int = None
                            payment_id_val = pid_int if pid_int is not None else ""
                            if pid_int is not None:
                                pay_info = payment_map.get(pid_int, {})

                        yield [
                            str(as_of_val),
                            str(school_id or ""),
                            str(inv_info.get("household_id", "")),
                            str(inv_info.get("invoice_id", "")),
                            str(inv_info.get("invoice_due_on", "")),
                            str(inv_info.get("invoice_status", "")),
                            str(inv_info.get("invoice_total", "")),
                            str(inv_info.get("invoice_amount_due", "")),
                            str(charge_id_int or ""),
                            str(ch_info.get("charge_amount", "")),
                            str(ch_info.get("charge_due_on", "")),
                            str(ch_info.get("charge_posted_on", "")),
                            str(alloc_id),
                            str(applied_on),
                            str(allocation_amount),
                            str(payment_id_val),
                            str(pay_info.get("payment_method", "")),
                            str(pay_info.get("payment_status", "")),
                            str(pay_info.get("payment_received_on", "")),
                            "allocation",
                        ]
                    return

            # 2) Charge lines fallback
            if ChargeModel and charge_ids_for_map:
                for cid_int in sorted(charge_ids_for_map):
                    inv_info = invoice_by_charge.get(cid_int, {})
                    ch_info = charge_map.get(cid_int, {})

                    yield [
                        str(as_of_val),
                        str(school_id or ""),
                        str(inv_info.get("household_id", "")),
                        str(inv_info.get("invoice_id", "")),
                        str(inv_info.get("invoice_due_on", "")),
                        str(inv_info.get("invoice_status", "")),
                        str(inv_info.get("invoice_total", "")),
                        str(inv_info.get("invoice_amount_due", "")),
                        str(cid_int),
                        str(ch_info.get("charge_amount", "")),
                        str(ch_info.get("charge_due_on", "")),
                        str(ch_info.get("charge_posted_on", "")),
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "charge",
                    ]
                return

            # 3) Invoice-only fallback
            for inv in inv_qs.iterator():
                yield [
                    str(as_of_val),
                    str(school_id or ""),
                    str(getattr(inv, "household_id", "") if "household_id" in inv_fields else ""),
                    str(getattr(inv, "id", "")),
                    str(getattr(inv, inv_due_on_field, "") if inv_due_on_field else ""),
                    str(getattr(inv, inv_status_field, "") if inv_status_field else ""),
                    str(getattr(inv, inv_total_field, "") if inv_total_field else ""),
                    str(getattr(inv, inv_due_field, "") if inv_due_field else ""),
                    str(getattr(inv, "ledger_charge_id", "") if inv_has_charge_link else ""),
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "invoice",
                ]

        filename = f"statement_lines_{as_of_val}.csv"
        resp = StreamingHttpResponse(_csv_stream(rows()), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        log_export(request, "statement-lines.csv", status_code=200, school_id=str(school_id or ""), row_count=None)
        return resp


class YearEndTuitionPaidCSVExportView(APIView):
    """0095-A: Tuition paid by calendar year.

    Endpoint:
      /api/exports/year-end/tuition-paid.csv?year=2025

    Optional params for *non-guessing* tuition classification:
      - include_tuition=1
      - tuition_account_id=<id>
      - tuition_account_code=<code>
      - tuition_account_name=<name>

    If no classifier is provided (or models don't support it),
    `applied_to_tuition_amount` will be blank.
    """

    permission_classes = [IsAuthenticated, IsFinanceRole]
    throttle_classes = [ExportUserMinuteThrottle, ExportUserHourThrottle, ExportIPMinuteThrottle]

    payment_candidates = [
        ModelCandidate("ledger", "Payment"),
        ModelCandidate("payments", "Payment"),
        ModelCandidate("crown_api", "Payment"),
        ModelCandidate("billing", "Payment"),
        ModelCandidate("finance", "Payment"),
        ModelCandidate("accounting", "Payment"),
    ]

    allocation_candidates = [
        ModelCandidate("ledger", "Allocation"),
        ModelCandidate("ledger", "LedgerAllocation"),
        ModelCandidate("accounting", "Allocation"),
        ModelCandidate("accounting", "LedgerAllocation"),
    ]

    charge_candidates = [
        ModelCandidate("ledger", "Charge"),
        ModelCandidate("ledger", "LedgerCharge"),
        ModelCandidate("accounting", "Charge"),
        ModelCandidate("accounting", "LedgerCharge"),
    ]

    @extend_schema(tags=["Exports"], responses={(200, "text/csv"): OpenApiTypes.BINARY})
    def get(self, request):
        year_raw = request.query_params.get("year")
        try:
            year = int(year_raw)
        except Exception:
            resp = StreamingHttpResponse(
                _csv_stream([["error"], ["Missing or invalid year"]]),
                content_type="text/csv; charset=utf-8",
                status=400,
            )
            resp["Content-Disposition"] = 'attachment; filename="error.csv"'
            log_export(request, "year-end/tuition-paid.csv", status_code=400, school_id=str(get_request_school_id(request) or ""))
            return resp

        try:
            PaymentModel = resolve_model(self.payment_candidates)
        except ModelNotFound as e:
            resp = StreamingHttpResponse(
                _csv_stream([["error"], [str(e)]]),
                content_type="text/csv; charset=utf-8",
                status=500,
            )
            resp["Content-Disposition"] = 'attachment; filename="error.csv"'
            log_export(request, "year-end/tuition-paid.csv", status_code=500, school_id=str(get_request_school_id(request) or ""))
            return resp

        pay_fields = _field_names(PaymentModel)
        sid = get_request_school_id(request)
        _log_export_access(request, "year-end/tuition-paid.csv", sid)

        qs = PaymentModel.objects.order_by("id")

        if "school_id" in pay_fields:
            if not sid:
                log_export(request, "year-end/tuition-paid.csv", status_code=403, school_id="", row_count=0)
                return StreamingHttpResponse(_csv_stream([]), status=403)
            qs = qs.filter(school_id=sid)

        # Find best available date field to interpret "received_on" and filter by year.
        pay_date_field = _pick_first(pay_fields, ["payment_date", "received_on", "posted_on", "created_at", "timestamp"])
        if pay_date_field:
            try:
                qs = qs.filter(**{f"{pay_date_field}__year": year})
            except Exception:
                # If the field isn't date-like, fall back to no date filtering.
                pass

        if "id" in pay_fields:
            qs = qs.order_by("id")

        include_tuition = request.query_params.get("include_tuition") in ("1", "true", "True")
        tuition_account_id = request.query_params.get("tuition_account_id")
        tuition_account_code = request.query_params.get("tuition_account_code")
        tuition_account_name = request.query_params.get("tuition_account_name")

        tuition_by_payment: dict[str, Decimal] = {}

        if include_tuition and (tuition_account_id or tuition_account_code or tuition_account_name):
            AllocationModel = None
            ChargeModel = None
            alloc_fields: set[str] = set()
            charge_fields: set[str] = set()

            try:
                AllocationModel = resolve_model(self.allocation_candidates)
                alloc_fields = _field_names(AllocationModel)
            except ModelNotFound:
                AllocationModel = None

            try:
                ChargeModel = resolve_model(self.charge_candidates)
                charge_fields = _field_names(ChargeModel)
            except ModelNotFound:
                ChargeModel = None

            alloc_amount_field = _pick_first(alloc_fields, ["amount", "applied_amount", "allocated_amount"])
            alloc_payment_group_field = "payment_id" if ("payment" in alloc_fields or "payment_id" in alloc_fields) else None
            alloc_charge_fk = _pick_first(alloc_fields, ["charge", "ledger_charge"])

            if AllocationModel and ChargeModel and alloc_amount_field and alloc_payment_group_field and alloc_charge_fk:
                alloc_qs = AllocationModel.objects.order_by("id")

                if "school_id" in alloc_fields and sid:
                    alloc_qs = alloc_qs.filter(school_id=sid)

                # Filter allocations to the requested calendar year using the payment relation if possible.
                if "payment" in alloc_fields and pay_date_field:
                    try:
                        alloc_qs = alloc_qs.filter(**{f"payment__{pay_date_field}__year": year})
                    except Exception:
                        EXPORT_AUDIT_LOGGER.debug("optional payment date filter failed", exc_info=True)

                # Apply tuition classification filters via charge->account fields when present.
                if "account" in charge_fields:
                    if tuition_account_id:
                        try:
                            alloc_qs = alloc_qs.filter(**{f"{alloc_charge_fk}__account_id": tuition_account_id})
                        except Exception:
                            EXPORT_AUDIT_LOGGER.debug("optional tuition account_id filter failed", exc_info=True)
                    if tuition_account_code:
                        try:
                            alloc_qs = alloc_qs.filter(**{f"{alloc_charge_fk}__account__code": tuition_account_code})
                        except Exception:
                            EXPORT_AUDIT_LOGGER.debug("optional tuition account code filter failed", exc_info=True)
                    if tuition_account_name:
                        try:
                            alloc_qs = alloc_qs.filter(**{f"{alloc_charge_fk}__account__name": tuition_account_name})
                        except Exception:
                            EXPORT_AUDIT_LOGGER.debug("optional tuition account name filter failed", exc_info=True)

                agg = alloc_qs.values(alloc_payment_group_field).annotate(total=Sum(alloc_amount_field))
                for row in agg.iterator():
                    pid = row.get(alloc_payment_group_field)
                    if pid is None:
                        continue
                    tuition_by_payment[str(pid)] = _to_decimal(row.get("total"))

        method_field = _pick_first(pay_fields, ["method", "payment_method", "source"])
        memo_field = _pick_first(pay_fields, ["memo", "notes", "reference", "payment_reference"])
        amount_field = _pick_first(pay_fields, ["amount", "amount_cents"])  # amount_cents handled as-is

        header = [
            "school_id",
            "household_id",
            "payment_id",
            "received_on",
            "method",
            "amount_received",
            "applied_to_tuition_amount",
            "notes_memo",
        ]

        def _household_id_for_payment(p) -> str:
            if hasattr(p, "household_id"):
                return _as_str(getattr(p, "household_id", ""))
            hh = getattr(p, "household", None)
            if hh is not None:
                return _as_str(getattr(hh, "id", ""))
            acct = getattr(p, "account", None)
            if acct is not None:
                if hasattr(acct, "household_id"):
                    return _as_str(getattr(acct, "household_id", ""))
                hh2 = getattr(acct, "household", None)
                if hh2 is not None:
                    return _as_str(getattr(hh2, "id", ""))
            return ""

        def rows():
            yield header
            for p in qs.iterator():
                pid = getattr(p, "id", "")
                school_val = getattr(p, "school_id", sid) if "school_id" in pay_fields else sid
                received_on_val = getattr(p, pay_date_field, "") if pay_date_field else ""

                yield [
                    _as_str(school_val),
                    _household_id_for_payment(p),
                    _as_str(pid),
                    _as_iso(received_on_val),
                    _as_str(getattr(p, method_field, "") if method_field else ""),
                    _as_str(getattr(p, amount_field, "") if amount_field else ""),
                    _as_str(tuition_by_payment.get(str(pid), "")),
                    _as_str(getattr(p, memo_field, "") if memo_field else ""),
                ]

        row_count = None
        try:
            row_count = qs.count()
        except Exception:
            row_count = None

        filename = f"tuition_paid_{year}.csv"
        resp = StreamingHttpResponse(_csv_stream(rows()), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        log_export(request, "year-end/tuition-paid.csv", status_code=200, school_id=str(sid or ""), row_count=row_count)
        return resp


class PaymentsQuickBooksCSVExportView(APIView):
    """0096-A: Payments export in a QuickBooks-friendly column order.

    Endpoint:
      /api/exports/accounting/payments-qb.csv

    Columns:
      Date, Amount, Customer, Payment Method, Reference/Check #, Memo, Deposit Account,
      payment_id, household_id, school_id
    """

    permission_classes = [IsAuthenticated, IsFinanceRole]
    throttle_classes = [ExportUserMinuteThrottle, ExportUserHourThrottle, ExportIPMinuteThrottle]

    payment_candidates = [
        ModelCandidate("ledger", "Payment"),
        ModelCandidate("payments", "Payment"),
        ModelCandidate("crown_api", "Payment"),
        ModelCandidate("billing", "Payment"),
        ModelCandidate("finance", "Payment"),
        ModelCandidate("accounting", "Payment"),
    ]

    @extend_schema(tags=["Exports"], responses={(200, "text/csv"): OpenApiTypes.BINARY})
    def get(self, request):
        try:
            PaymentModel = resolve_model(self.payment_candidates)
        except ModelNotFound as e:
            resp = StreamingHttpResponse(
                _csv_stream([["error"], [str(e)]]),
                content_type="text/csv; charset=utf-8",
                status=500,
            )
            resp["Content-Disposition"] = 'attachment; filename="error.csv"'
            log_export(request, "accounting/payments-qb.csv", status_code=500, school_id=str(get_request_school_id(request) or ""))
            return resp

        pay_fields = _field_names(PaymentModel)
        sid = get_request_school_id(request)
        _log_export_access(request, "accounting/payments-qb.csv", sid)

        qs = PaymentModel.objects.order_by("id")

        if "school_id" in pay_fields:
            if not sid:
                log_export(request, "accounting/payments-qb.csv", status_code=403, school_id="", row_count=0)
                return StreamingHttpResponse(_csv_stream([]), status=403)
            qs = qs.filter(school_id=sid)

        row_count = None
        try:
            row_count = qs.count()
        except Exception:
            row_count = None

        date_field = _pick_first(pay_fields, ["payment_date", "received_on", "posted_on", "created_at", "timestamp"])
        amount_field = _pick_first(pay_fields, ["amount", "amount_cents"])
        method_field = _pick_first(pay_fields, ["method", "payment_method", "source"])
        reference_field = _pick_first(pay_fields, ["reference", "payment_reference", "check_number", "reference_number"])
        memo_field = _pick_first(pay_fields, ["memo", "notes"])

        # Best-effort related lookup for customer name.
        try:
            if "account" in pay_fields:
                qs = qs.select_related("account", "account__household")
            elif "household" in pay_fields:
                qs = qs.select_related("household")
        except Exception:
            EXPORT_AUDIT_LOGGER.debug("optional select_related failed", exc_info=True)

        if date_field and "id" in pay_fields:
            try:
                qs = qs.order_by(date_field, "id")
            except Exception:
                qs = qs.order_by("id")
        elif "id" in pay_fields:
            qs = qs.order_by("id")

        header = [
            "Date",
            "Amount",
            "Customer",
            "Payment Method",
            "Reference/Check #",
            "Memo",
            "Deposit Account",
            "payment_id",
            "household_id",
            "school_id",
        ]

        def _customer_for_payment(p) -> str:
            hh = getattr(p, "household", None)
            if hh is not None:
                return _as_str(getattr(hh, "name", "") or hh)

            acct = getattr(p, "account", None)
            if acct is not None:
                hh2 = getattr(acct, "household", None)
                if hh2 is not None:
                    return _as_str(getattr(hh2, "name", "") or hh2)
            return ""

        def _household_id_for_payment(p) -> str:
            if hasattr(p, "household_id"):
                return _as_str(getattr(p, "household_id", ""))
            hh = getattr(p, "household", None)
            if hh is not None:
                return _as_str(getattr(hh, "id", ""))
            acct = getattr(p, "account", None)
            if acct is not None and hasattr(acct, "household_id"):
                return _as_str(getattr(acct, "household_id", ""))
            return ""

        def rows():
            yield header
            for p in qs.iterator():
                pid = getattr(p, "id", "")
                school_val = getattr(p, "school_id", sid) if "school_id" in pay_fields else sid

                date_val = getattr(p, date_field, "") if date_field else ""
                amount_val = getattr(p, amount_field, "") if amount_field else ""
                method_val = getattr(p, method_field, "") if method_field else ""
                ref_val = getattr(p, reference_field, "") if reference_field else ""
                memo_val = getattr(p, memo_field, "") if memo_field else ""

                yield [
                    _as_iso(date_val),
                    _as_str(amount_val),
                    _customer_for_payment(p),
                    _as_str(method_val),
                    _as_str(ref_val),
                    _as_str(memo_val),
                    "",  # deposit account is intentionally blank (no guessing)
                    _as_str(pid),
                    _household_id_for_payment(p),
                    _as_str(school_val),
                ]

        filename = f"payments_qb_{now().date().isoformat()}.csv"
        resp = StreamingHttpResponse(_csv_stream(rows()), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        log_export(request, "accounting/payments-qb.csv", status_code=200, school_id=str(sid or ""), row_count=row_count)
        return resp
