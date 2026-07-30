"""Provider-neutral test doubles for the deferred Advancement payment pipeline.

CROWN has no selected or authorized external payment provider. Production-facing
payment entry points remain fail-closed in ``advancement.payment_hold_views`` and
``payments.hold``. These in-process providers exist only for isolated domain and
workflow tests that do not contact an external processor.
"""

from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, Optional


class PaymentProviderBase(ABC):
    """Contract used by provider-neutral Advancement workflow tests."""

    @abstractmethod
    def create_checkout_session(
        self, amount: float, currency: str, metadata: dict
    ) -> dict:
        """Return a provider-neutral checkout result for an isolated test flow."""

    @abstractmethod
    def retrieve_payment_status(self, provider_payment_id: str) -> str:
        """Return one of: pending, paid, failed, or refunded."""


class FakeProvider(PaymentProviderBase):
    """In-process test double; it never contacts an external processor."""

    PROVIDER_NAME = "fake"

    def create_checkout_session(
        self, amount: float, currency: str, metadata: dict
    ) -> dict:
        return {
            "provider_payment_id": f"fake_{uuid.uuid4().hex}",
            "checkout_url": "",
        }

    def retrieve_payment_status(self, provider_payment_id: str) -> str:
        return "pending"


@dataclass
class PaymentIntentResult:
    """Normalized result returned by an isolated checkout test double."""

    provider: str
    provider_payment_id: str
    client_secret: Optional[str] = None
    checkout_url: Optional[str] = None
    raw: Optional[Dict[str, Any]] = dc_field(default_factory=dict)


class CheckoutProviderBase:
    """Contract for provider-neutral checkout workflow tests."""

    name: str = "base"

    def create_checkout_session(
        self,
        *,
        amount_cents: int,
        currency: str,
        description: str,
        success_url: str,
        cancel_url: str,
        metadata: dict,
    ) -> PaymentIntentResult:
        raise NotImplementedError

    def verify_webhook(
        self, *, payload: bytes, signature: str, webhook_secret: str
    ) -> dict:
        raise NotImplementedError


class FakeCheckoutProvider(CheckoutProviderBase):
    """In-process test double; it never verifies or sends external webhooks."""

    name = "fake"

    def create_checkout_session(
        self,
        *,
        amount_cents: int,
        currency: str,
        description: str,
        success_url: str,
        cancel_url: str,
        metadata: dict,
    ) -> PaymentIntentResult:
        sid = f"fake_cs_{uuid.uuid4().hex[:12]}"
        return PaymentIntentResult(
            provider=self.name,
            provider_payment_id=sid,
            checkout_url=f"{success_url}?session_id={sid}",
            raw={"metadata": metadata},
        )

    def fetch_checkout_line_items(self, session_id: str, limit: int = 20) -> dict:
        return {"data": []}

    def verify_webhook(
        self, *, payload: bytes, signature: str, webhook_secret: str
    ) -> dict:
        return json.loads(payload)
