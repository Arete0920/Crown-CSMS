"""
Provider factory for the Advancement payment pipeline.
Reads ADVANCEMENT_PAYMENT_PROVIDER from settings (default "fake").
"""
from django.conf import settings

from .providers import FakeProvider, PaymentProviderBase

_REGISTRY: dict[str, type[PaymentProviderBase]] = {
    "fake": FakeProvider,
}


def get_provider() -> PaymentProviderBase:
    """Return an instantiated provider based on settings (Stage 2 – keep unchanged)."""
    key = getattr(settings, "ADVANCEMENT_PAYMENT_PROVIDER", "fake").lower()
    cls = _REGISTRY.get(key)
    if cls is None:
        raise ValueError(
            f"Unknown ADVANCEMENT_PAYMENT_PROVIDER: '{key}'. "
            f"Valid choices: {list(_REGISTRY.keys())}"
        )
    return cls()


def get_checkout_provider():
    """Stage 3.2 factory – returns a CheckoutProviderBase instance."""
    from .providers import FakeCheckoutProvider, StripeProvider  # local import avoids circular
    key = getattr(settings, "ADVANCEMENT_PAYMENT_PROVIDER", "fake").lower()
    if key == "fake":
        return FakeCheckoutProvider()
    if key == "stripe":
        api_key = getattr(settings, "STRIPE_SECRET_KEY", "")
        if not api_key:
            raise ValueError("STRIPE_SECRET_KEY is not configured in settings.")
        return StripeProvider(api_key=api_key)
    raise ValueError(f"Unknown ADVANCEMENT_PAYMENT_PROVIDER for checkout: '{key}'.")
