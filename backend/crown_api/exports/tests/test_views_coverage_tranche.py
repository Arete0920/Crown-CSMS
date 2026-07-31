from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from crown_api.exports.views import (
    Echo,
    InstallmentScheduleCSVExportView,
    InvoicesCSVExportView,
    _as_iso,
    _as_str,
    _csv_stream,
    _log_export_access,
)


class Request:
    def __init__(self, query_params=None):
        self.query_params = query_params or {}
        self.path = "/api/v1/exports/test.csv"
        self.user = SimpleNamespace(id=17)


def body(response):
    return b"".join(response.streaming_content).decode("utf-8")


def test_csv_helpers_cover_null_date_datetime_and_fallback_values():
    assert Echo().write("value") == "value"
    assert list(_csv_stream([["a", "b"], ["1", "2"]])) == ["a,b\r\n", "1,2\r\n"]
    assert _as_iso(None) == ""
    assert _as_iso(date(2026, 7, 31)) == "2026-07-31"
    assert _as_iso(datetime(2026, 7, 31, 3, 58)) == "2026-07-31T03:58:00"
    assert _as_iso(SimpleNamespace(__str__=lambda self: "fallback"))
    assert _as_str(None) == ""
    assert _as_str(42) == "42"


def test_export_access_logging_failure_never_breaks_request():
    request = Request()
    with patch("crown_api.exports.views.EXPORT_AUDIT_LOGGER.info", side_effect=RuntimeError("log unavailable")):
        assert _log_export_access(request, "invoices.csv", 9) is None


def test_invoices_export_fails_closed_without_school_scope():
    request = Request()
    with (
        patch("crown_api.exports.views.get_request_school_id", return_value=None),
        patch("crown_api.exports.views.log_export") as audit,
    ):
        response = InvoicesCSVExportView().get(request)

    assert response.status_code == 403
    assert body(response) == ""
    audit.assert_called_once_with(
        request,
        "invoices.csv",
        status_code=403,
        school_id="",
        row_count=0,
    )


def test_invoice_export_applies_scope_filters_and_serializes_rows():
    request = Request(
        {
            "household_id": "22",
            "due_on_from": "2026-08-01",
            "due_on_to": "2026-08-31",
        }
    )
    invoice = SimpleNamespace(
        id=101,
        household_id=22,
        due_on=date(2026, 8, 15),
        issued_on=date(2026, 7, 31),
        status="open",
        currency="USD",
        total_amount="125.00",
        amount_due="100.00",
        ledger_charge_id=501,
        installment_plan_id=601,
        installment_schedule_item_id=701,
        created_at=datetime(2026, 7, 31, 1, 0),
        updated_at=datetime(2026, 7, 31, 2, 0),
    )
    queryset = MagicMock()
    queryset.order_by.return_value = queryset
    queryset.filter.return_value = queryset
    queryset.iterator.return_value = iter([invoice])
    queryset.count.return_value = 1

    with (
        patch("crown_api.exports.views.get_request_school_id", return_value=9),
        patch("crown_api.exports.views.Invoice.objects.filter", return_value=queryset) as scoped,
        patch("crown_api.exports.views.log_export") as audit,
    ):
        response = InvoicesCSVExportView().get(request)
        csv_body = body(response)

    assert response.status_code == 200
    assert response["Content-Disposition"].startswith('attachment; filename="invoices_')
    scoped.assert_called_once_with(school_id=9)
    queryset.filter.assert_any_call(household_id="22")
    queryset.filter.assert_any_call(due_on__gte="2026-08-01")
    queryset.filter.assert_any_call(due_on__lte="2026-08-31")
    assert "invoice_id,household_id,due_on" in csv_body
    assert "101,22,2026-08-15,2026-07-31,open,USD,125.00,100.00,501,601,701,2026-07-31T01:00:00,2026-07-31T02:00:00" in csv_body
    audit.assert_called_once_with(
        request,
        "invoices.csv",
        status_code=200,
        school_id="9",
        row_count=1,
    )


def test_invoice_export_tolerates_count_failure():
    request = Request()
    queryset = MagicMock()
    queryset.order_by.return_value = queryset
    queryset.iterator.return_value = iter([])
    queryset.count.side_effect = RuntimeError("count unavailable")

    with (
        patch("crown_api.exports.views.get_request_school_id", return_value=3),
        patch("crown_api.exports.views.Invoice.objects.filter", return_value=queryset),
        patch("crown_api.exports.views.log_export") as audit,
    ):
        response = InvoicesCSVExportView().get(request)
        assert "invoice_id" in body(response)

    audit.assert_called_once_with(
        request,
        "invoices.csv",
        status_code=200,
        school_id="3",
        row_count=None,
    )


def test_installment_export_fails_closed_without_school_scope():
    request = Request()
    with (
        patch("crown_api.exports.views.get_request_school_id", return_value=None),
        patch("crown_api.exports.views.log_export") as audit,
    ):
        response = InstallmentScheduleCSVExportView().get(request)

    assert response.status_code == 403
    assert body(response) == ""
    audit.assert_called_once_with(
        request,
        "installment-schedule.csv",
        status_code=403,
        school_id="",
        row_count=0,
    )


def test_installment_export_applies_filters_and_serializes_invoice_link():
    request = Request({"household_id": "22", "plan_id": "7"})
    item = SimpleNamespace(
        id=81,
        plan_id=7,
        household_id=22,
        due_on=date(2026, 8, 20),
        amount="50.00",
        invoice_id=101,
        invoice=SimpleNamespace(ledger_charge_id=501),
        status="scheduled",
        created_at=datetime(2026, 7, 31, 1, 0),
        updated_at=datetime(2026, 7, 31, 2, 0),
    )
    queryset = MagicMock()
    queryset.filter.return_value = queryset
    queryset.order_by.return_value = queryset
    queryset.iterator.return_value = iter([item])
    queryset.count.return_value = 1
    manager = MagicMock()
    manager.select_related.return_value = manager
    manager.filter.return_value = queryset

    with (
        patch("crown_api.exports.views.get_request_school_id", return_value=9),
        patch("crown_api.exports.views.InstallmentScheduleItem.objects", manager),
        patch("crown_api.exports.views.log_export") as audit,
    ):
        response = InstallmentScheduleCSVExportView().get(request)
        csv_body = body(response)

    manager.select_related.assert_called_once_with("plan", "invoice")
    manager.filter.assert_called_once_with(school_id=9)
    queryset.filter.assert_any_call(plan_id="7")
    queryset.filter.assert_any_call(household_id="22")
    assert "schedule_item_id,plan_id,household_id" in csv_body
    assert "81,7,22,2026-08-20,50.00,101,501,scheduled,2026-07-31T01:00:00,2026-07-31T02:00:00" in csv_body
    audit.assert_called_once_with(
        request,
        "installment-schedule.csv",
        status_code=200,
        school_id="9",
        row_count=1,
    )
