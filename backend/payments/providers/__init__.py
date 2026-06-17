from .stripe_connect import StripeConnect


class DeferredPaymentGateway:
    def _deferred(self):
        return {
            "ok": False,
            "error": "External payment provider deferred pending vendor coordination.",
        }

    def create_intent(self, **kwargs):
        return type("GatewayResult", (), self._deferred())()

    def fetch_status(self, **kwargs):
        return type(
            "GatewayResult",
            (),
            {**self._deferred(), "status": None, "provider_payment_id": "", "raw": {}},
        )()

    def create_payment_method_setup(self, **kwargs):
        return type(
            "GatewayResult", (), {**self._deferred(), "setup_id": "", "setup_url": ""}
        )()

    def detach_payment_method(self, **kwargs):
        return type("GatewayResult", (), self._deferred())()

    def update_dispute(self, **kwargs):
        return type(
            "GatewayResult",
            (),
            {**self._deferred(), "provider_response_id": "", "status": None, "raw": {}},
        )()


def get_gateway(provider_code: str):
    return DeferredPaymentGateway()


__all__ = ["DeferredPaymentGateway", "StripeConnect", "get_gateway"]
