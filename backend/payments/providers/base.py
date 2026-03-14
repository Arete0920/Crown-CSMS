from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class CreateIntentResult:
    ok: bool
    provider_intent_id: str = ""
    provider_payment_id: str = ""
    status: str = ""
    checkout_url: str = ""
    raw: dict[str, Any] | None = None
    error: str = ""


@dataclass
class PaymentStatusResult:
    ok: bool
    provider_intent_id: str = ""
    provider_payment_id: str = ""
    status: str = ""
    settled_amount: Decimal | None = None
    raw: dict[str, Any] | None = None
    error: str = ""


@dataclass
class RefundResult:
    ok: bool
    refund_id: str = ""
    status: str = ""
    raw: dict[str, Any] | None = None
    error: str = ""


@dataclass
class DisputeListResult:
    ok: bool
    disputes: list[dict[str, Any]] | None = None
    raw: dict[str, Any] | None = None
    error: str = ""


@dataclass
class PayoutListResult:
    ok: bool
    payouts: list[dict[str, Any]] | None = None
    raw: dict[str, Any] | None = None
    error: str = ""


@dataclass
class PaymentMethodSetupResult:
    ok: bool
    setup_id: str = ""
    setup_url: str = ""
    raw: dict[str, Any] | None = None
    error: str = ""


@dataclass
class PaymentMethodListResult:
    ok: bool
    methods: list[dict[str, Any]] | None = None
    raw: dict[str, Any] | None = None
    error: str = ""


@dataclass
class PaymentMethodDetachResult:
    ok: bool
    raw: dict[str, Any] | None = None
    error: str = ""


@dataclass
class DisputeActionResult:
    ok: bool
    provider_response_id: str = ""
    status: str = ""
    raw: dict[str, Any] | None = None
    error: str = ""


class PaymentGatewayProvider:
    provider_code = ""

    def create_intent(
        self,
        *,
        amount: Decimal,
        currency: str,
        client_reference_id: str,
        description: str,
        metadata: dict,
    ) -> CreateIntentResult:
        raise NotImplementedError

    def fetch_status(self, *, provider_intent_id: str) -> PaymentStatusResult:
        raise NotImplementedError

    def refund_payment(
        self,
        *,
        provider_payment_id: str,
        amount: Decimal | None = None,
        reason: str = "",
    ) -> RefundResult:
        raise NotImplementedError

    def list_disputes(self) -> DisputeListResult:
        raise NotImplementedError

    def list_payout_batches(self) -> PayoutListResult:
        raise NotImplementedError

    def create_payment_method_setup(
        self,
        *,
        customer_reference: str,
        return_url: str,
        metadata: dict,
    ) -> PaymentMethodSetupResult:
        raise NotImplementedError

    def list_saved_payment_methods(self, *, customer_reference: str) -> PaymentMethodListResult:
        raise NotImplementedError

    def detach_payment_method(self, *, provider_method_id: str) -> PaymentMethodDetachResult:
        raise NotImplementedError

    def update_dispute(
        self,
        *,
        dispute_id: str,
        action_type: str,
        note: str = "",
        evidence: dict | None = None,
    ) -> DisputeActionResult:
        raise NotImplementedError
