"""Canonical fail-closed response while external payment processing is deferred.

The Founder/Product Owner has identified CompuWerx as the intended provider but
has not authorized or certified external money movement. Provider-dependent checkout, payment confirmation,
fulfillment, polling, webhook, and gateway-event retry entry points must not
validate payloads or mutate application state while this hold is active.
"""

from rest_framework import status
from rest_framework.response import Response


PAYMENT_INTEGRATION_ON_HOLD = {
    "code": "payment_integration_on_hold",
    "detail": (
        "External payment processing is disabled pending vendor coordination, "
        "authorization, implementation, and certification."
    ),
    "provider_configured": False,
    "provider": None,
}


def payment_hold_response() -> Response:
    """Return the canonical response after the route's access checks pass."""

    return Response(PAYMENT_INTEGRATION_ON_HOLD, status=status.HTTP_503_SERVICE_UNAVAILABLE)
