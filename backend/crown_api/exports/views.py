import csv
from datetime import date
from typing import Iterable, List

from django.http import StreamingHttpResponse
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from households.scoping import get_request_school_id

# IMPORTANT:
# These imports must match your actual model locations.
# Adjust ONLY the import lines if your apps are named differently.
from billing.models import Invoice, InstallmentScheduleItem


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

    permission_classes = [IsAuthenticated]

    def get(self, request):
        sid = get_request_school_id(request)
        if not sid:
            # Stay safe: no scoping => no data
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

        filename = f"invoices_{now().date().isoformat()}.csv"
        resp = StreamingHttpResponse(_csv_stream(rows()), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp


class InstallmentScheduleCSVExportView(APIView):
    """Exports installment schedule items as flat CSV (school-scoped).

    Filters (optional):
      - household_id
      - plan_id
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        sid = get_request_school_id(request)
        if not sid:
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

        filename = f"installment_schedule_{now().date().isoformat()}.csv"
        resp = StreamingHttpResponse(_csv_stream(rows()), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp
