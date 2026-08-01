from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest
from django.core.exceptions import FieldDoesNotExist

from crown_api.exports import views


def test_echo_write_returns_original_value():
    assert views.Echo().write("a,b\n") == "a,b\n"


def test_csv_stream_serializes_rows():
    assert list(views._csv_stream([["a", "b"], ["1", "2"]])) == [
        "a,b\r\n",
        "1,2\r\n",
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (None, ""),
        (date(2026, 8, 1), "2026-08-01"),
        (datetime(2026, 8, 1, 12, 30), "2026-08-01T12:30:00"),
        ("already-text", "already-text"),
    ),
)
def test_as_iso_normalizes_supported_values(value, expected):
    assert views._as_iso(value) == expected


@pytest.mark.parametrize(("value", "expected"), ((None, ""), (0, "0"), (False, "False"), ("x", "x")))
def test_string_helpers(value, expected):
    assert views._as_str(value) == expected
    assert views._safe_str(value) == expected


def test_log_export_access_never_raises(monkeypatch):
    logger = MagicMock()
    logger.info.side_effect = RuntimeError("logger unavailable")
    monkeypatch.setattr(views, "EXPORT_AUDIT_LOGGER", logger)
    request = SimpleNamespace(path="/api/v1/exports/test.csv", user=SimpleNamespace(id=7))

    assert views._log_export_access(request, "test.csv", "school-a") is None


def test_model_has_field_true_and_false():
    model = MagicMock()
    model._meta.get_field.return_value = object()
    assert views._model_has_field(model, "school_id") is True

    model._meta.get_field.side_effect = FieldDoesNotExist("missing")
    assert views._model_has_field(model, "school_id") is False


def test_base_queryset_fails_closed_without_school(monkeypatch):
    model = MagicMock()
    ordered = MagicMock()
    model.objects.order_by.return_value = ordered
    empty = MagicMock()
    model.objects.none.return_value = empty
    monkeypatch.setattr(views, "_model_has_field", lambda model, name: True)
    monkeypatch.setattr(views, "get_request_school_id", lambda request: None)

    view = views._BaseModelCSVExportView()
    view.request = SimpleNamespace()

    assert view.get_queryset(model) is empty
    model.objects.none.assert_called_once_with()


def test_base_queryset_scopes_school_and_uses_first_valid_order(monkeypatch):
    model = MagicMock()
    initial = MagicMock()
    scoped = MagicMock()
    final = MagicMock()
    model.objects.order_by.return_value = initial
    initial.filter.return_value = scoped
    scoped.order_by.side_effect = [RuntimeError("bad field"), final]
    monkeypatch.setattr(views, "_model_has_field", lambda model, name: True)
    monkeypatch.setattr(views, "get_request_school_id", lambda request: "school-a")

    view = views._BaseModelCSVExportView()
    view.request = SimpleNamespace()
    view.order_by = ["bad", "id"]

    assert view.get_queryset(model) is final
    initial.filter.assert_called_once_with(school_id="school-a")
    assert scoped.order_by.call_args_list == [call("bad"), call("id")]


def test_base_export_returns_error_csv_when_model_resolution_fails(monkeypatch):
    monkeypatch.setattr(
        views,
        "resolve_model",
        MagicMock(side_effect=views.ModelNotFound("No export model available")),
    )
    audit = MagicMock()
    monkeypatch.setattr(views, "log_export", audit)
    monkeypatch.setattr(views, "get_request_school_id", lambda request: "school-a")
    request = SimpleNamespace()
    view = views._BaseModelCSVExportView()
    view.filename_prefix = "students"

    response = view.get(request)

    assert response.status_code == 500
    assert response["Content-Disposition"] == 'attachment; filename="error.csv"'
    body = b"".join(response.streaming_content)
    assert body == b"error\r\nNo export model available\r\n"
    audit.assert_called_once_with(
        request,
        "students.csv",
        status_code=500,
        school_id="school-a",
    )


def test_base_export_fails_closed_for_scoped_model_without_school(monkeypatch):
    model = MagicMock()
    monkeypatch.setattr(views, "resolve_model", MagicMock(return_value=model))
    monkeypatch.setattr(views, "_model_has_field", lambda model, name: True)
    monkeypatch.setattr(views, "get_request_school_id", lambda request: None)
    audit = MagicMock()
    monkeypatch.setattr(views, "log_export", audit)
    monkeypatch.setattr(views, "_log_export_access", MagicMock())
    request = SimpleNamespace()
    view = views._BaseModelCSVExportView()
    view.filename_prefix = "households"

    response = view.get(request)

    assert response.status_code == 403
    assert list(response.streaming_content) == []
    audit.assert_called_once_with(
        request,
        "households.csv",
        status_code=403,
        school_id="",
        row_count=0,
    )


def test_base_export_sets_filename_serializes_rows_and_audits(monkeypatch):
    model = MagicMock()
    obj = SimpleNamespace(id=1, name="Family A")
    queryset = MagicMock()
    queryset.count.return_value = 1
    queryset.iterator.return_value = iter([obj])
    monkeypatch.setattr(views, "resolve_model", MagicMock(return_value=model))
    monkeypatch.setattr(views, "_model_has_field", lambda model, name: False)
    monkeypatch.setattr(views, "default_export_fields", MagicMock(return_value=["id", "name"]))
    monkeypatch.setattr(views, "get_request_school_id", lambda request: None)
    monkeypatch.setattr(views, "now", lambda: datetime(2026, 8, 1, 9, 0))
    audit = MagicMock()
    monkeypatch.setattr(views, "log_export", audit)
    monkeypatch.setattr(views, "_log_export_access", MagicMock())
    request = SimpleNamespace()
    view = views._BaseModelCSVExportView()
    view.filename_prefix = "households"
    view.get_queryset = MagicMock(return_value=queryset)

    response = view.get(request)

    assert response.status_code == 200
    assert response["Content-Disposition"] == 'attachment; filename="households_2026-08-01.csv"'
    assert b"".join(response.streaming_content) == b"id,name\r\n1,Family A\r\n"
    audit.assert_called_once_with(
        request,
        "households.csv",
        status_code=200,
        school_id="",
        row_count=1,
    )


def test_invoices_export_fails_closed_without_school(monkeypatch):
    audit = MagicMock()
    access = MagicMock()
    monkeypatch.setattr(views, "get_request_school_id", lambda request: None)
    monkeypatch.setattr(views, "log_export", audit)
    monkeypatch.setattr(views, "_log_export_access", access)
    request = SimpleNamespace(query_params={})

    response = views.InvoicesCSVExportView().get(request)

    assert response.status_code == 403
    assert list(response.streaming_content) == []
    access.assert_called_once_with(request, "invoices.csv", None)
    audit.assert_called_once_with(
        request,
        "invoices.csv",
        status_code=403,
        school_id="",
        row_count=0,
    )


def test_invoices_export_filters_serializes_and_audits(monkeypatch):
    invoice = SimpleNamespace(
        id="inv-1",
        household_id="hh-1",
        due_on=date(2026, 9, 1),
        issued_on=date(2026, 8, 1),
        status="open",
        currency="USD",
        total_amount="120.00",
        amount_due="80.00",
        ledger_charge_id="charge-1",
        installment_plan_id="plan-1",
        installment_schedule_item_id="item-1",
        created_at=datetime(2026, 8, 1, 9, 0),
        updated_at=datetime(2026, 8, 2, 10, 0),
    )
    manager = MagicMock()
    root = MagicMock()
    ordered = MagicMock()
    by_household = MagicMock()
    by_start = MagicMock()
    by_end = MagicMock()
    manager.filter.return_value = root
    monkeypatch.setattr(views, "Invoice", SimpleNamespace(objects=manager))
    root.order_by.return_value = ordered
    ordered.filter.return_value = by_household
    by_household.filter.return_value = by_start
    by_start.filter.return_value = by_end
    by_end.iterator.return_value = iter([invoice])
    by_end.count.return_value = 1
    audit = MagicMock()
    access = MagicMock()
    monkeypatch.setattr(views, "get_request_school_id", lambda request: "school-a")
    monkeypatch.setattr(views, "log_export", audit)
    monkeypatch.setattr(views, "_log_export_access", access)
    monkeypatch.setattr(views, "now", lambda: datetime(2026, 8, 1, 9, 0))
    request = SimpleNamespace(
        query_params={
            "household_id": "hh-1",
            "due_on_from": "2026-08-01",
            "due_on_to": "2026-09-30",
        }
    )

    response = views.InvoicesCSVExportView().get(request)
    body = b"".join(response.streaming_content).decode("utf-8")

    assert response.status_code == 200
    assert response["Content-Disposition"] == 'attachment; filename="invoices_2026-08-01.csv"'
    assert body.splitlines()[0].startswith("invoice_id,household_id,due_on")
    assert "inv-1,hh-1,2026-09-01,2026-08-01,open,USD,120.00,80.00" in body
    manager.filter.assert_called_once_with(school_id="school-a")
    root.order_by.assert_called_once_with("due_on", "id")
    ordered.filter.assert_called_once_with(household_id="hh-1")
    by_household.filter.assert_called_once_with(due_on__gte="2026-08-01")
    by_start.filter.assert_called_once_with(due_on__lte="2026-09-30")
    access.assert_called_once_with(request, "invoices.csv", "school-a")
    audit.assert_called_once_with(
        request,
        "invoices.csv",
        status_code=200,
        school_id="school-a",
        row_count=1,
    )


def test_installment_export_fails_closed_without_school(monkeypatch):
    audit = MagicMock()
    access = MagicMock()
    monkeypatch.setattr(views, "get_request_school_id", lambda request: None)
    monkeypatch.setattr(views, "log_export", audit)
    monkeypatch.setattr(views, "_log_export_access", access)
    request = SimpleNamespace(query_params={})

    response = views.InstallmentScheduleCSVExportView().get(request)

    assert response.status_code == 403
    assert list(response.streaming_content) == []
    access.assert_called_once_with(request, "installment-schedule.csv", None)
    audit.assert_called_once_with(
        request,
        "installment-schedule.csv",
        status_code=403,
        school_id="",
        row_count=0,
    )


def test_installment_export_filters_serializes_and_audits(monkeypatch):
    invoice = SimpleNamespace(ledger_charge_id="charge-1")
    item = SimpleNamespace(
        id="item-1",
        plan_id="plan-1",
        household_id="hh-1",
        due_on=date(2026, 9, 15),
        amount="50.00",
        invoice_id="inv-1",
        invoice=invoice,
        status="scheduled",
        created_at=datetime(2026, 8, 1, 9, 0),
        updated_at=datetime(2026, 8, 2, 10, 0),
    )
    manager = MagicMock()
    selected = MagicMock()
    scoped = MagicMock()
    ordered = MagicMock()
    by_plan = MagicMock()
    by_household = MagicMock()
    monkeypatch.setattr(
        views,
        "InstallmentScheduleItem",
        SimpleNamespace(objects=manager),
    )
    manager.select_related.return_value = selected
    selected.filter.return_value = scoped
    scoped.order_by.return_value = ordered
    ordered.filter.return_value = by_plan
    by_plan.filter.return_value = by_household
    by_household.iterator.return_value = iter([item])
    by_household.count.return_value = 1
    audit = MagicMock()
    access = MagicMock()
    monkeypatch.setattr(views, "get_request_school_id", lambda request: "school-a")
    monkeypatch.setattr(views, "log_export", audit)
    monkeypatch.setattr(views, "_log_export_access", access)
    monkeypatch.setattr(views, "now", lambda: datetime(2026, 8, 1, 9, 0))
    request = SimpleNamespace(query_params={"plan_id": "plan-1", "household_id": "hh-1"})

    response = views.InstallmentScheduleCSVExportView().get(request)
    body = b"".join(response.streaming_content).decode("utf-8")

    assert response.status_code == 200
    assert response["Content-Disposition"] == (
        'attachment; filename="installment_schedule_2026-08-01.csv"'
    )
    assert body.splitlines()[0].startswith("schedule_item_id,plan_id,household_id")
    assert "item-1,plan-1,hh-1,2026-09-15,50.00,inv-1,charge-1,scheduled" in body
    manager.select_related.assert_called_once_with("plan", "invoice")
    selected.filter.assert_called_once_with(school_id="school-a")
    scoped.order_by.assert_called_once_with("due_on", "id")
    ordered.filter.assert_called_once_with(plan_id="plan-1")
    by_plan.filter.assert_called_once_with(household_id="hh-1")
    access.assert_called_once_with(request, "installment-schedule.csv", "school-a")
    audit.assert_called_once_with(
        request,
        "installment-schedule.csv",
        status_code=200,
        school_id="school-a",
        row_count=1,
    )
