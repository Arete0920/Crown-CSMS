import json
from decimal import Decimal

import requests
from django.conf import settings

from .base import (
    CreateIntentResult,
    DisputeActionResult,
    DisputeListResult,
    PaymentGatewayProvider,
    PaymentMethodDetachResult,
    PaymentMethodListResult,
    PaymentMethodSetupResult,
    PaymentStatusResult,
    PayoutListResult,
    RefundResult,
)


class CompuwerxGateway(PaymentGatewayProvider):
    provider_code = "compuwerx"

    @property
    def base_url(self) -> str:
        return settings.COMPUWERX_BASE_URL.rstrip("/")

    @property
    def api_key(self) -> str:
        return settings.COMPUWERX_API_KEY

    @property
    def timeout_seconds(self) -> int:
        return int(getattr(settings, "COMPUWERX_TIMEOUT_SECONDS", 30))

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def create_intent(
        self,
        *,
        amount: Decimal,
        currency: str,
        client_reference_id: str,
        description: str,
        metadata: dict,
    ) -> CreateIntentResult:
        url = f"{self.base_url}/payments/intents"
        payload = {
            "amount": str(amount),
            "currency": currency,
            "client_reference_id": client_reference_id,
            "description": description,
            "metadata": metadata or {},
        }

        try:
            resp = requests.post(
                url,
                headers=self._headers(),
                data=json.dumps(payload),
                timeout=self.timeout_seconds,
            )
            data = resp.json()
        except Exception as exc:
            return CreateIntentResult(ok=False, error=str(exc))

        if resp.status_code >= 400:
            return CreateIntentResult(
                ok=False,
                error=data.get("error") or f"Compuwerx error {resp.status_code}",
                raw=data,
            )

        return CreateIntentResult(
            ok=True,
            provider_intent_id=data.get("intent_id", ""),
            provider_payment_id=data.get("payment_id", ""),
            status=data.get("status", "pending"),
            checkout_url=data.get("checkout_url", ""),
            raw=data,
        )

    def fetch_status(self, *, provider_intent_id: str) -> PaymentStatusResult:
        url = f"{self.base_url}/payments/intents/{provider_intent_id}"

        try:
            resp = requests.get(
                url,
                headers=self._headers(),
                timeout=self.timeout_seconds,
            )
            data = resp.json()
        except Exception as exc:
            return PaymentStatusResult(ok=False, error=str(exc))

        if resp.status_code >= 400:
            return PaymentStatusResult(
                ok=False,
                error=data.get("error") or f"Compuwerx error {resp.status_code}",
                raw=data,
            )

        settled_amount = data.get("settled_amount")
        return PaymentStatusResult(
            ok=True,
            provider_intent_id=data.get("intent_id", provider_intent_id),
            provider_payment_id=data.get("payment_id", ""),
            status=data.get("status", "pending"),
            settled_amount=Decimal(str(settled_amount)) if settled_amount is not None else None,
            raw=data,
        )

    def refund_payment(
        self,
        *,
        provider_payment_id: str,
        amount: Decimal | None = None,
        reason: str = "",
    ) -> RefundResult:
        url = f"{self.base_url}/payments/{provider_payment_id}/refund"
        payload = {
            "reason": reason or "Requested by Crown",
        }
        if amount is not None:
            payload["amount"] = str(amount)

        try:
            resp = requests.post(
                url,
                headers=self._headers(),
                data=json.dumps(payload),
                timeout=self.timeout_seconds,
            )
            data = resp.json()
        except Exception as exc:
            return RefundResult(ok=False, error=str(exc))

        if resp.status_code >= 400:
            return RefundResult(
                ok=False,
                error=data.get("error") or f"Compuwerx error {resp.status_code}",
                raw=data,
            )

        return RefundResult(
            ok=True,
            refund_id=data.get("refund_id", ""),
            status=data.get("status", "pending"),
            raw=data,
        )

    def list_disputes(self) -> DisputeListResult:
        url = f"{self.base_url}/payments/disputes"

        try:
            resp = requests.get(
                url,
                headers=self._headers(),
                timeout=self.timeout_seconds,
            )
            data = resp.json()
        except Exception as exc:
            return DisputeListResult(ok=False, error=str(exc))

        if resp.status_code >= 400:
            return DisputeListResult(
                ok=False,
                error=data.get("error") or f"Compuwerx error {resp.status_code}",
                raw=data,
            )

        return DisputeListResult(
            ok=True,
            disputes=data.get("results") or data.get("disputes") or [],
            raw=data,
        )

    def list_payout_batches(self) -> PayoutListResult:
        url = f"{self.base_url}/payments/payouts"

        try:
            resp = requests.get(
                url,
                headers=self._headers(),
                timeout=self.timeout_seconds,
            )
            data = resp.json()
        except Exception as exc:
            return PayoutListResult(ok=False, error=str(exc))

        if resp.status_code >= 400:
            return PayoutListResult(
                ok=False,
                error=data.get("error") or f"Compuwerx error {resp.status_code}",
                raw=data,
            )

        return PayoutListResult(
            ok=True,
            payouts=data.get("results") or data.get("payouts") or [],
            raw=data,
        )

    def create_payment_method_setup(
        self,
        *,
        customer_reference: str,
        return_url: str,
        metadata: dict,
    ) -> PaymentMethodSetupResult:
        url = f"{self.base_url}/payments/customers/{customer_reference}/payment-method-setup"
        payload = {
            "return_url": return_url,
            "metadata": metadata or {},
        }

        try:
            resp = requests.post(
                url,
                headers=self._headers(),
                data=json.dumps(payload),
                timeout=self.timeout_seconds,
            )
            data = resp.json()
        except Exception as exc:
            return PaymentMethodSetupResult(ok=False, error=str(exc))

        if resp.status_code >= 400:
            return PaymentMethodSetupResult(
                ok=False,
                error=data.get("error") or f"Compuwerx error {resp.status_code}",
                raw=data,
            )

        return PaymentMethodSetupResult(
            ok=True,
            setup_id=data.get("setup_id", ""),
            setup_url=data.get("setup_url", ""),
            raw=data,
        )

    def list_saved_payment_methods(self, *, customer_reference: str) -> PaymentMethodListResult:
        url = f"{self.base_url}/payments/customers/{customer_reference}/payment-methods"

        try:
            resp = requests.get(
                url,
                headers=self._headers(),
                timeout=self.timeout_seconds,
            )
            data = resp.json()
        except Exception as exc:
            return PaymentMethodListResult(ok=False, error=str(exc))

        if resp.status_code >= 400:
            return PaymentMethodListResult(
                ok=False,
                error=data.get("error") or f"Compuwerx error {resp.status_code}",
                raw=data,
            )

        return PaymentMethodListResult(
            ok=True,
            methods=data.get("results") or data.get("payment_methods") or [],
            raw=data,
        )

    def detach_payment_method(self, *, provider_method_id: str) -> PaymentMethodDetachResult:
        url = f"{self.base_url}/payments/payment-methods/{provider_method_id}"

        try:
            resp = requests.delete(
                url,
                headers=self._headers(),
                timeout=self.timeout_seconds,
            )
            try:
                data = resp.json()
            except Exception:
                data = {}
        except Exception as exc:
            return PaymentMethodDetachResult(ok=False, error=str(exc))

        if resp.status_code >= 400:
            return PaymentMethodDetachResult(
                ok=False,
                error=data.get("error") or f"Compuwerx error {resp.status_code}",
                raw=data,
            )

        return PaymentMethodDetachResult(ok=True, raw=data)

    def update_dispute(
        self,
        *,
        dispute_id: str,
        action_type: str,
        note: str = "",
        evidence: dict | None = None,
    ) -> DisputeActionResult:
        url = f"{self.base_url}/payments/disputes/{dispute_id}/actions"
        payload = {
            "action_type": action_type,
            "note": note,
            "evidence": evidence or {},
        }

        try:
            resp = requests.post(
                url,
                headers=self._headers(),
                data=json.dumps(payload),
                timeout=self.timeout_seconds,
            )
            data = resp.json()
        except Exception as exc:
            return DisputeActionResult(ok=False, error=str(exc))

        if resp.status_code >= 400:
            return DisputeActionResult(
                ok=False,
                error=data.get("error") or f"Compuwerx error {resp.status_code}",
                raw=data,
            )

        return DisputeActionResult(
            ok=True,
            provider_response_id=data.get("response_id", ""),
            status=data.get("status", ""),
            raw=data,
        )
