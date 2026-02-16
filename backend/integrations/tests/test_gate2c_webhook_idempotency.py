import json
from decimal import Decimal

import pytest
from django.urls import reverse

from core.models import School
from households.models import Household
from ledger.models import LedgerAccount, Payment
from journal.models import JournalEntry, GLAccount
from integrations.models import WebhookEvent


pytestmark = pytest.mark.django_db


def test_compuwerx_webhook_is_idempotent_and_void_triggers_single_reversal(client):
    school = School.objects.create(name="Heritage")

    # Create household and ledger account (required for Payment)
    household = Household.objects.create(school_id=school.id, name="Test Household")
    ledger_account = LedgerAccount.objects.create(school_id=school.id, household=household)

    # Ensure canonical GL accounts exist (for payment posting signal)
    cash, _ = GLAccount.objects.get_or_create(
        school=school,
        code="1000",
        defaults={"name": "Cash", "account_type": "ASSET"},
    )
    ar, _ = GLAccount.objects.get_or_create(
        school=school,
        code="1100",
        defaults={"name": "Accounts Receivable", "account_type": "ASSET"},
    )

    # Create Payment (existing signal posts JE on create: reference_type="payment")
    p = Payment.objects.create(
        school_id=school.id,
        account=ledger_account,
        amount=Decimal("50.00"),
        source="test",
        reference="t1",
    )

    original = JournalEntry.objects.filter(
        school=school,
        reference_type="payment",
        reference_id=p.id,
    ).first()
    assert original is not None, "Expected payment JE posted on create"

    url = reverse("compuwerx-webhook")
    payload = {"event_id": "cw_evt_1", "type": "payment.voided", "payment_id": str(p.id)}

    # First delivery applies void + reversal
    r1 = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert r1.status_code == 200
    assert WebhookEvent.objects.filter(provider="compuwerx", event_id="cw_evt_1").count() == 1

    original.refresh_from_db()

    reversal = JournalEntry.objects.filter(reversal_of=original).first()
    assert reversal is not None, "Expected reversing JournalEntry to be created"
    assert reversal.reversal_of_id == original.id

    # idempotency proof
    assert JournalEntry.objects.filter(reversal_of=original).count() == 1

    # Replay: no new WebhookEvent row, no duplicate reversal
    r2 = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert r2.status_code == 200
    assert WebhookEvent.objects.filter(provider="compuwerx", event_id="cw_evt_1").count() == 1
    assert JournalEntry.objects.filter(reversal_of=original).count() == 1
