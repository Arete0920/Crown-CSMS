import hashlib
import hmac
import json

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from payments.models import GatewayEvent


@override_settings(COMPUWERX_WEBHOOK_SECRET="test-secret")
class CompuwerxWebhookIdempotencyTests(TestCase):
    def _signature(self, body: bytes) -> str:
        return hmac.new(
            key=settings.COMPUWERX_WEBHOOK_SECRET.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256,
        ).hexdigest()

    def test_duplicate_event_is_accepted_once(self):
        payload = {
            "event_id": "evt_123",
            "event_type": "payment.settled",
            "intent_id": "pi_123",
            "payment_id": "pay_123",
            "status": "settled",
            "metadata": {"school_id": "00000000-0000-0000-0000-000000000000"},
        }
        body = json.dumps(payload).encode("utf-8")
        sig = self._signature(body)

        client = Client()
        url = reverse("payments-webhook-compuwerx")

        first = client.generic("POST", url, body, content_type="application/json", HTTP_X_COMPUWERX_SIGNATURE=sig)
        second = client.generic("POST", url, body, content_type="application/json", HTTP_X_COMPUWERX_SIGNATURE=sig)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(GatewayEvent.objects.filter(event_id="evt_123").count(), 1)
