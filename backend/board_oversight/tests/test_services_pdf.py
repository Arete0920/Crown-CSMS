from decimal import Decimal

import pytest

from board_oversight import services_pdf


class FakeQuerySet:
    def __init__(self, items=None, count_value=0, calls=None):
        self.items = list(items or [])
        self.count_value = count_value
        self.calls = calls if calls is not None else []

    def __iter__(self):
        return iter(self.items)

    def filter(self, **kwargs):
        self.calls.append(("filter", kwargs))
        if "status" in kwargs:
            return FakeQuerySet(
                items=self.items,
                count_value=2,
                calls=self.calls,
            )
        return self

    def order_by(self, *fields):
        self.calls.append(("order_by", fields))
        return self

    def count(self):
        self.calls.append(("count", None))
        return self.count_value


class FakeManager:
    def __init__(self, queryset):
        self.queryset = queryset

    def filter(self, **kwargs):
        self.queryset.calls.append(("filter", kwargs))
        return self.queryset

    def order_by(self, *fields):
        self.queryset.calls.append(("order_by", fields))
        return self.queryset


class PaymentRecord:
    def __init__(self, amount):
        self.amount = Decimal(amount)


def capture_table_data(monkeypatch):
    platypus = pytest.importorskip("reportlab.platypus")

    captured = {}
    original_table = platypus.Table

    def recording_table(data, *args, **kwargs):
        captured["data"] = data
        return original_table(data, *args, **kwargs)

    monkeypatch.setattr(platypus, "Table", recording_table)
    return captured


def test_generate_board_packet_returns_none_without_reportlab(monkeypatch):
    monkeypatch.setattr(services_pdf, "_reportlab_available", lambda: False)

    assert services_pdf.generate_board_packet() is None


@pytest.mark.django_db
def test_generate_board_packet_scopes_metrics_and_returns_pdf(monkeypatch):
    payment_calls = []
    application_calls = []
    discipline_calls = []
    initiative_calls = []
    captured = capture_table_data(monkeypatch)

    payment_qs = FakeQuerySet(
        items=[PaymentRecord("125.50"), PaymentRecord("74.50")],
        calls=payment_calls,
    )
    application_qs = FakeQuerySet(count_value=7, calls=application_calls)
    discipline_qs = FakeQuerySet(count_value=3, calls=discipline_calls)
    initiative_qs = FakeQuerySet(count_value=5, calls=initiative_calls)

    from applications.models import Application
    from board_oversight.models_governance import StrategicInitiative
    from discipline.models import DisciplineIncident
    from ledger.models import Payment

    monkeypatch.setattr(Payment, "objects", FakeManager(payment_qs))
    monkeypatch.setattr(Application, "objects", FakeManager(application_qs))
    monkeypatch.setattr(DisciplineIncident, "objects", FakeManager(discipline_qs))
    monkeypatch.setattr(StrategicInitiative, "objects", FakeManager(initiative_qs))

    result = services_pdf.generate_board_packet(school_id="school-123")

    assert result is not None
    assert result.getvalue().startswith(b"%PDF")
    assert captured["data"] == [
        ["Metric", "Value"],
        ["Total Revenue (Successful Payments)", "$200.00"],
        ["Applications", "7"],
        ["Discipline Incidents", "3"],
        ["Strategic Initiatives (Complete / Total)", "2 / 5"],
    ]
    assert ("filter", {"status": "success"}) in payment_calls
    assert ("filter", {"school_id": "school-123"}) in payment_calls
    assert ("filter", {"school_id": "school-123"}) in application_calls
    assert ("filter", {"school_id": "school-123"}) in discipline_calls
    assert ("filter", {"school_id": "school-123"}) in initiative_calls
    assert ("filter", {"status": "complete"}) in initiative_calls


@pytest.mark.django_db
def test_generate_board_packet_falls_back_when_metric_queries_fail(monkeypatch):
    captured = capture_table_data(monkeypatch)

    class BrokenManager:
        def filter(self, **kwargs):
            raise RuntimeError("query unavailable")

        def order_by(self, *fields):
            raise RuntimeError("query unavailable")

    from applications.models import Application
    from board_oversight.models_governance import StrategicInitiative
    from discipline.models import DisciplineIncident
    from ledger.models import Payment

    monkeypatch.setattr(Payment, "objects", BrokenManager())
    monkeypatch.setattr(Application, "objects", BrokenManager())
    monkeypatch.setattr(DisciplineIncident, "objects", BrokenManager())
    monkeypatch.setattr(StrategicInitiative, "objects", BrokenManager())

    result = services_pdf.generate_board_packet()

    assert result is not None
    assert result.getvalue().startswith(b"%PDF")
    assert captured["data"] == [
        ["Metric", "Value"],
        ["Total Revenue (Successful Payments)", "$0.00"],
        ["Applications", "0"],
        ["Discipline Incidents", "0"],
        ["Strategic Initiatives (Complete / Total)", "0 / 0"],
    ]
