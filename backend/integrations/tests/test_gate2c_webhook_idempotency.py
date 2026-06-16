import json
from decimal import Decimal

import pytest
from django.urls import reverse

from core.models import School
from households.models import Household
from ledger.models import LedgerAccount, Payment
from journal.models import JournalEntry, GLAccount

pytestmark = pytest.mark.django_db


def test_retired_legacy_compuwerx_webhook_cannot_void_payment(client):
    school = School.objects.create(name="Heritage")

    # Create household and ledger account (required for Payment)
    household = Household.objects.create(school_id=school.id, name="Test Household")
    ledger_account = LedgerAccount.objects.create(
        school_id=school.id, household=household
    )

    # Ensure canonical GL accounts exist (for payment posting signal)
    _, _ = GLAccount.objects.get_or_create(
        school=school,
        code="1000",
        defaults={"name": "Cash", "account_type": "ASSET"},
    )
    _, _ = GLAccount.objects.get_or_create(
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

    url = reverse("compuwerx-webhook")
    payload = {
        "event_id": "cw_evt_1",
        "type": "payment.voided",
        "payment_id": str(p.id),
    }

    # Legacy route is retired and must never mutate payment state.
    r1 = client.post(url, data=json.dumps(payload), content_type="application/json")
    assert r1.status_code == 410
    assert r1.json()["error"] == "legacy_compuwerx_webhook_retired"

    p.refresh_from_db()
    assert p.is_void is False

    # Existing payment create journal entry remains unchanged.
    original = JournalEntry.objects.filter(
        school=school,
        reference_type="payment",
        reference_id=p.id,
    ).first()
    assert original is not None, "Expected payment JE posted on create"
    assert JournalEntry.objects.filter(reversal_of=original).count() == 0
