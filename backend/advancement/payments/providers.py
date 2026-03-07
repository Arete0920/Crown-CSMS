"""
Payment provider abstraction for the Advancement module.

Real providers (Stripe, etc.) should subclass PaymentProviderBase and implement
the two abstract methods. The FakeProvider is used in dev/test environments.
"""
import uuid
from abc import ABC, abstractmethod


class PaymentProviderBase(ABC):
    """Contract every payment provider must satisfy."""

    @abstractmethod
    def create_checkout_session(self, amount: float, currency: str, metadata: dict) -> dict:
        """
        Create a checkout session for the given amount.

        Returns a dict with at minimum:
            {
                "provider_payment_id": str,  # provider's opaque reference
                "checkout_url": str,          # redirect URL for the payer (may be empty)
            }
        """

    @abstractmethod
    def retrieve_payment_status(self, provider_payment_id: str) -> str:
        """
        Look up the current status of a payment from the provider.

        Returns one of: "pending" | "paid" | "failed" | "refunded"
        """


class FakeProvider(PaymentProviderBase):
    """
    In-process stub used in development & automated tests.
    All sessions are instantly marked as pending with a deterministic ID prefix.
    Callers must explicitly invoke mark_gift_paid / mark_sponsorship_paid to transition
    to "paid" — this mirrors the real asynchronous webhook flow.
    """

    PROVIDER_NAME = "fake"

    def create_checkout_session(self, amount: float, currency: str, metadata: dict) -> dict:
        return {
            "provider_payment_id": f"fake_{uuid.uuid4().hex}",
            "checkout_url": "",
        }

    def retrieve_payment_status(self, provider_payment_id: str) -> str:
        # Fake provider is always pending until explicitly marked paid
        return "pending"


# ---------------------------------------------------------------------------
# Stage 3.2 – Checkout provider abstraction (Stripe + test double)
# These are SEPARATE from the Stage 2 PaymentProviderBase hierarchy so that
# existing Stage 2 tests continue to pass unchanged.
# ---------------------------------------------------------------------------
from dataclasses import dataclass, field as dc_field
from typing import Optional, Dict, Any


@dataclass
class PaymentIntentResult:
    """Normalised result returned by every CheckoutProviderBase implementation."""
    provider: str
    provider_payment_id: str                    # Stripe CS id (cs_live_…) or fake id
    client_secret: Optional[str] = None
    checkout_url: Optional[str] = None
    raw: Optional[Dict[str, Any]] = dc_field(default_factory=dict)


class CheckoutProviderBase:
    """Abstract base for Stage 3.2 checkout providers."""
    name: str = "base"

    def create_checkout_session(
        self, *, amount_cents: int, currency: str, description: str,
        success_url: str, cancel_url: str, metadata: dict,
    ) -> PaymentIntentResult:
        raise NotImplementedError

    def verify_webhook(self, *, payload: bytes, signature: str, webhook_secret: str) -> dict:
        """Verify + parse an incoming webhook event. Returns the event dict."""
        raise NotImplementedError


class FakeCheckoutProvider(CheckoutProviderBase):
    """Test double – instantly returns a checkout_url = success_url so tests can skip Stripe."""
    name = "fake"

    def create_checkout_session(
        self, *, amount_cents: int, currency: str, description: str,
        success_url: str, cancel_url: str, metadata: dict,
    ) -> PaymentIntentResult:
        sid = f"fake_cs_{uuid.uuid4().hex[:12]}"
        return PaymentIntentResult(
            provider=self.name,
            provider_payment_id=sid,
            checkout_url=f"{success_url}?session_id={sid}",
            raw={"metadata": metadata},
        )

    def fetch_checkout_line_items(self, session_id: str, limit: int = 20) -> dict:
        """Test stub: return a single line item with amount_cents = 0."""
        return {"data": []}

    def verify_webhook(self, *, payload: bytes, signature: str, webhook_secret: str) -> dict:
        """Test: accept raw JSON without verification."""
        import json
        return json.loads(payload)


class StripeProvider(CheckoutProviderBase):
    """Production Stripe Checkout integration."""
    name = "stripe"

    def __init__(self, *, api_key: str):
        try:
            import stripe
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError(
                "stripe package is not installed. Add it to requirements.txt."
            ) from exc
        stripe.api_key = api_key
        self._stripe = stripe

    def create_checkout_session(
        self, *, amount_cents: int, currency: str, description: str,
        success_url: str, cancel_url: str, metadata: dict,
    ) -> PaymentIntentResult:
        # Pop internal-only keys before forwarding metadata to Stripe
        working_meta = dict(metadata)
        donation_presets_cents = working_meta.pop("donation_presets_cents", [])
        if isinstance(donation_presets_cents, str):
            # JSON-serialised list from services layer
            import json as _json
            try:
                donation_presets_cents = _json.loads(donation_presets_cents)
            except Exception:
                donation_presets_cents = []

        optional_items = [
            {
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": f"Add a donation (${int(c) // 100})"},
                    "unit_amount": int(c),
                },
                "quantity": 1,
            }
            for c in donation_presets_cents[:10]
        ]

        session = self._stripe.checkout.Session.create(
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=working_meta.get("customer_email"),
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": description},
                    "unit_amount": amount_cents,
                },
                "quantity": 1,
            }],
            optional_items=optional_items or None,
            metadata=working_meta,
        )
        return PaymentIntentResult(
            provider=self.name,
            provider_payment_id=session.id,
            checkout_url=getattr(session, "url", None),
            raw={"id": session.id},
        )

    def fetch_checkout_line_items(self, session_id: str, limit: int = 20) -> dict:
        """Retrieve line items for a completed Checkout Session.

        Returns a dict-like Stripe ListObject (has .data list).
        Used post-webhook to compute accurate donation totals.
        """
        return self._stripe.checkout.Session.list_line_items(session_id, limit=limit)

    def verify_webhook(self, *, payload: bytes, signature: str, webhook_secret: str) -> dict:
        event = self._stripe.Webhook.construct_event(
            payload=payload, sig_header=signature, secret=webhook_secret
        )
        return dict(event)
