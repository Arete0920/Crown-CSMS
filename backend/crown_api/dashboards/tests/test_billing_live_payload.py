from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest
from django.utils import timezone

from crown_api.dashboards.batch5_extra_payloads import billing_live_payload


class FakeInvoiceQuerySet:
    def __init__(self, rows):
        self.rows = list(rows)

    def filter(self, **kwargs):
        return self

    def __iter__(self):
        return iter(self.rows)


class FakePaymentQuerySet:
    def __init__(self, total):
        self.total = Decimal(total)

    def filter(self, **kwargs):
        return self

    def aggregate(self, **kwargs):
        return {'total': self.total}


class FakeAllocationQuerySet:
    def __init__(self, rows):
        self.rows = list(rows)

    def filter(self, **kwargs):
        return self

    def values(self, *fields):
        return self

    def annotate(self, **kwargs):
        return self

    def __iter__(self):
        return iter(self.rows)


@pytest.mark.django_db
def test_billing_live_payload_uses_bulk_allocated_invoice_balances(monkeypatch):
    from billing import models as billing_models
    from ledger import models as ledger_models

    today = timezone.localdate()
    charge_one = UUID('11111111-1111-1111-1111-111111111101')
    charge_two = UUID('11111111-1111-1111-1111-111111111102')
    charge_three = UUID('11111111-1111-1111-1111-111111111103')
    invoices = [
        SimpleNamespace(
            total_amount=Decimal('1000.00'),
            due_on=today - timedelta(days=10),
            ledger_charge_id=charge_one,
        ),
        SimpleNamespace(
            total_amount=Decimal('500.00'),
            due_on=today - timedelta(days=5),
            ledger_charge_id=charge_two,
        ),
        SimpleNamespace(
            total_amount=Decimal('300.00'),
            due_on=today + timedelta(days=5),
            ledger_charge_id=charge_three,
        ),
    ]
    allocation_rows = [
        {'charge_id': charge_one, 'total': Decimal('750.00')},
        {'charge_id': charge_two, 'total': Decimal('500.00')},
    ]

    monkeypatch.setattr(
        billing_models,
        'Invoice',
        SimpleNamespace(objects=FakeInvoiceQuerySet(invoices)),
    )
    monkeypatch.setattr(
        ledger_models,
        'Payment',
        SimpleNamespace(objects=FakePaymentQuerySet('75.00')),
    )
    monkeypatch.setattr(
        ledger_models,
        'Allocation',
        SimpleNamespace(objects=FakeAllocationQuerySet(allocation_rows)),
    )

    payload = billing_live_payload('11111111-1111-1111-1111-111111111111')
    metrics = {row['label']: row['value'] for row in payload['metrics']}

    assert payload['meta']['served_from'] == 'live_db'
    assert payload['meta']['billed_total'] == '1800.00'
    assert payload['meta']['outstanding_total'] == '550.00'
    assert payload['meta']['paid_total'] == '1250.00'
    assert metrics['Invoices Issued'] == '3'
    assert metrics['Outstanding Balances'] == '$550.00'
    assert metrics['Overdue Invoices'] == '1'
    assert metrics['Payments Collected Today'] == '$75.00'
