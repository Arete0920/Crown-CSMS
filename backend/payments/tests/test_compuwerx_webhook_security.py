import hashlib
import hmac
import json
from decimal import Decimal

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from core.models import School
from households.models import Household
from ledger.models import LedgerAccount, Payment
from journal.models import GLAccount
from payments.models import GatewayEvent


pytestmark = pytest.mark.django_db


def _signature(body: bytes) -> str:
    return hmac.new(
        key=settings.COMPUWERX_WEBHOOK_SECRET.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()


@override_settings(COMPUWERX_WEBHOOK_SECRET="test-secret")
def test_canonical_webhook_rejects_missing_signature(client):
    url = reverse("payments-webhook-compuwerx")
    body = json.dumps(
        {
            "event_id": "evt_missing_sig",
            "event_type": "payment.settled",
            "intent_id": "pi_missing_sig",
            "payment_id": "pay_missing_sig",
        }
    ).encode("utf-8")

    response = client.generic("POST", url, body, content_type="application/json")

    assert response.status_code == 401
    assert response.json()["error"] == "Invalid signature"
    assert GatewayEvent.objects.filter(event_id="evt_missing_sig").count() == 0


@override_settings(COMPUWERX_WEBHOOK_SECRET="test-secret")
def test_canonical_webhook_rejects_invalid_signature(client):
    url = reverse("payments-webhook-compuwerx")
    body = json.dumps(
        {
            "event_id": "evt_invalid_sig",
            "event_type": "payment.settled",
            "intent_id": "pi_invalid_sig",
            "payment_id": "pay_invalid_sig",
        }
    ).encode("utf-8")

    response = client.generic(
        "POST",
        url,
        body,
        content_type="application/json",
        HTTP_X_COMPUWERX_SIGNATURE="bad-signature",
    )

    assert response.status_code == 401
    assert response.json()["error"] == "Invalid signature"
    assert GatewayEvent.objects.filter(event_id="evt_invalid_sig").count() == 0


@override_settings(COMPUWERX_WEBHOOK_SECRET="test-secret")
def test_canonical_webhook_accepts_valid_signature(client):
    url = reverse("payments-webhook-compuwerx")
    payload = {
        "event_id": "evt_valid_sig",
        "event_type": "payment.settled",
        "intent_id": "pi_valid_sig",
        "payment_id": "pay_valid_sig",
        "status": "settled",
        "metadata": {"school_id": "00000000-0000-0000-0000-000000000000"},
    }
    body = json.dumps(payload).encode("utf-8")
    sig = _signature(body)

    response = client.generic(
        "POST",
        url,
        body,
        content_type="application/json",
        HTTP_X_COMPUWERX_SIGNATURE=sig,
    )

    assert response.status_code == 200
    assert GatewayEvent.objects.filter(event_id="evt_valid_sig").count() == 1


@override_settings(COMPUWERX_WEBHOOK_SECRET="test-secret")
def test_retired_legacy_route_cannot_mutate_payment_state(client):
    school = School.objects.create(name="Legacy Blocked School")
    household = Household.objects.create(school_id=school.id, name="Blocked Household")
    ledger_account = LedgerAccount.objects.create(
        school_id=school.id, household=household
    )

    GLAccount.objects.get_or_create(
        school=school,
        code="1000",
        defaults={"name": "Cash", "account_type": "ASSET"},
    )
    GLAccount.objects.get_or_create(
        school=school,
        code="1100",
        defaults={"name": "Accounts Receivable", "account_type": "ASSET"},
    )

    payment = Payment.objects.create(
        school_id=school.id,
        account=ledger_account,
        amount=Decimal("25.00"),
        source="test",
        reference="legacy-retired",
    )

    url = reverse("compuwerx-webhook")
    body = json.dumps(
        {
            "event_id": "evt_legacy_retired",
            "type": "payment.voided",
            "payment_id": str(payment.id),
        }
    )

    response = client.post(url, data=body, content_type="application/json")

    assert response.status_code == 410
    payment.refresh_from_db()
    assert payment.is_void is False
