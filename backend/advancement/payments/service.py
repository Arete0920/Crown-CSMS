"""Provider factory for isolated Advancement payment workflow tests.

No external payment provider is selected or authorized. Production-facing
payment routes remain fail-closed and do not call this module.
"""

from .providers import FakeCheckoutProvider, FakeProvider, PaymentProviderBase


_REGISTRY: dict[str, type[PaymentProviderBase]] = {
    "fake": FakeProvider,
}


def get_provider() -> PaymentProviderBase:
    """Return the only permitted in-process provider test double."""

    return FakeProvider()


def get_checkout_provider() -> FakeCheckoutProvider:
    """Return the only permitted in-process checkout test double."""

    return FakeCheckoutProvider()
