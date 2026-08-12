import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from payments.authority_services import (
    CanonicalOverRefundError,
    IdempotencyConflict,
    PaymentAuthorityError,
    bind_payment_provider,
    create_payment,
    fail_refund,
    request_refund,
    settle_payment,
    settle_refund,
    transition_payment_status,
)
from payments.models import (
    CanonicalPaymentStatus,
    CanonicalRefundStatus,
    Payment,
    Refund,
)


class CanonicalPaymentsAuthorityTest(TestCase):
    def setUp(self):
        self.school_id = uuid.UUID("00000000-0000-0000-0000-000000000041")
        self.household_id = uuid.UUID("00000000-0000-0000-0000-000000000042")

    def payment(self, *, amount_cents=10000, key="payment-1", finance_payment_id=91):
        return create_payment(
            school_id=self.school_id,
            household_id=self.household_id,
            finance_payment_id=finance_payment_id,
            amount_cents=amount_cents,
            currency="usd",
            idempotency_key=key,
        )

    def settled_payment(self, *, amount_cents=10000, key="payment-settled"):
        payment = self.payment(amount_cents=amount_cents, key=key)
        payment.status = CanonicalPaymentStatus.SETTLED
        payment.save(update_fields=["status", "updated_at"])
        return payment

    def test_payment_creation_is_idempotent_and_conflicting_reuse_fails_closed(self):
        first = self.payment(amount_cents=12500, key="idem-1")
        replay = self.payment(amount_cents=12500, key="idem-1")
        self.assertEqual(first.pk, replay.pk)
        self.assertEqual(first.currency, "USD")

        with self.assertRaises(IdempotencyConflict):
            self.payment(amount_cents=12501, key="idem-1")

    def test_payment_facts_and_provider_ids_are_immutable_and_hard_delete_is_blocked(self):
        payment = self.payment(key="immutable-1")
        payment = bind_payment_provider(
            payment=payment,
            provider="metro",
            provider_intent_id="intent-1",
            provider_payment_id="payment-1",
        )

        payment.amount_cents = 9999
        with self.assertRaises(ValidationError):
            payment.save()

        payment.refresh_from_db()
        payment.provider_payment_id = "payment-2"
        with self.assertRaises(ValidationError):
            payment.save()

        payment.refresh_from_db()
        with self.assertRaises(ValidationError):
            payment.delete()
        with self.assertRaises(ValidationError):
            Payment.objects.filter(pk=payment.pk).delete()

    def test_nonfinancial_status_transitions_do_not_settle_legacy_money(self):
        payment = self.payment(key="lifecycle-1")
        with patch("payments.authority_services.settle_payment_and_allocate") as settle_mock:
            payment = transition_payment_status(
                payment=payment,
                target_status=CanonicalPaymentStatus.AUTHORIZED,
            )
        self.assertEqual(payment.status, CanonicalPaymentStatus.AUTHORIZED)
        self.assertIsNotNone(payment.authorized_at)
        settle_mock.assert_not_called()

    def test_canonical_settlement_calls_legacy_bridge_only_at_settlement(self):
        payment = self.payment(key="settlement-1")
        legacy_payment = SimpleNamespace(
            pk=91,
            school_id=self.school_id,
            amount_cents=payment.amount_cents,
            currency="USD",
            processor="manual",
        )
        locked = MagicMock()
        locked.filter.return_value.first.return_value = legacy_payment

        with (
            patch(
                "payments.authority_services.FinancePayment.objects.select_for_update",
                return_value=locked,
            ),
            patch("payments.authority_services.settle_payment_and_allocate") as settle_mock,
        ):
            result = settle_payment(
                payment=payment,
                allocations_payload=[{"obligation_id": 7, "amount_cents": 10000}],
                provider="metro",
                provider_intent_id="intent-settle-1",
                provider_payment_id="payment-settle-1",
            )

        self.assertEqual(result.status, CanonicalPaymentStatus.SETTLED)
        self.assertIsNotNone(result.settled_at)
        settle_mock.assert_called_once_with(
            payment=legacy_payment,
            allocations_payload=[{"obligation_id": 7, "amount_cents": 10000}],
        )

    def test_refund_request_reserves_capacity_without_posting_legacy_refund(self):
        payment = self.settled_payment(key="refund-request-payment")
        with patch("payments.authority_services.initiate_refund") as legacy_refund_mock:
            refund = request_refund(
                payment=payment,
                amount_cents=4000,
                idempotency_key="refund-request-1",
                provider="metro",
            )

        self.assertEqual(refund.status, CanonicalRefundStatus.REQUESTED)
        self.assertIsNone(refund.finance_refund_id)
        legacy_refund_mock.assert_not_called()

    def test_over_refund_prevention_counts_requested_pending_and_settled(self):
        payment = self.settled_payment(amount_cents=10000, key="over-refund-payment")
        first = request_refund(
            payment=payment,
            amount_cents=6000,
            idempotency_key="refund-reserved-1",
            provider="metro",
        )

        with self.assertRaises(CanonicalOverRefundError):
            request_refund(
                payment=payment,
                amount_cents=5000,
                idempotency_key="refund-reserved-2",
                provider="metro",
            )

        fail_refund(refund=first)
        replacement = request_refund(
            payment=payment,
            amount_cents=5000,
            idempotency_key="refund-reserved-2",
            provider="metro",
        )
        self.assertEqual(replacement.status, CanonicalRefundStatus.REQUESTED)

    def test_provider_settled_refund_posts_legacy_effect_then_marks_partial_refund(self):
        payment = self.settled_payment(amount_cents=10000, key="settled-refund-payment")
        refund = request_refund(
            payment=payment,
            amount_cents=2500,
            idempotency_key="settled-refund-1",
            provider="metro",
        )

        legacy_refunds = MagicMock()
        legacy_refunds.filter.return_value.first.return_value = None
        legacy_payment = SimpleNamespace(
            pk=91,
            school_id=self.school_id,
            amount_cents=10000,
            currency="USD",
            processor="manual",
            refunds=legacy_refunds,
        )
        locked = MagicMock()
        locked.filter.return_value.first.return_value = legacy_payment
        legacy_refund = MagicMock(pk=601, status="pending", processor_refund_id="")

        with (
            patch(
                "payments.authority_services.FinancePayment.objects.select_for_update",
                return_value=locked,
            ),
            patch(
                "payments.authority_services.initiate_refund",
                return_value=legacy_refund,
            ) as legacy_refund_mock,
        ):
            result = settle_refund(
                refund=refund,
                provider="metro",
                provider_refund_id="refund-provider-1",
            )

        result.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(result.status, CanonicalRefundStatus.SETTLED)
        self.assertEqual(result.finance_refund_id, 601)
        self.assertEqual(payment.status, CanonicalPaymentStatus.PARTIALLY_REFUNDED)
        legacy_refund_mock.assert_called_once()
        legacy_refund.save.assert_called_once()

    def test_full_provider_settled_refund_marks_payment_refunded(self):
        payment = self.settled_payment(amount_cents=10000, key="full-refund-payment")
        refund = request_refund(
            payment=payment,
            amount_cents=10000,
            idempotency_key="full-refund-1",
            provider="metro",
        )

        legacy_refunds = MagicMock()
        legacy_refunds.filter.return_value.first.return_value = None
        legacy_payment = SimpleNamespace(
            pk=91,
            school_id=self.school_id,
            amount_cents=10000,
            currency="USD",
            processor="manual",
            refunds=legacy_refunds,
        )
        locked = MagicMock()
        locked.filter.return_value.first.return_value = legacy_payment
        legacy_refund = MagicMock(pk=602, status="pending", processor_refund_id="")

        with (
            patch(
                "payments.authority_services.FinancePayment.objects.select_for_update",
                return_value=locked,
            ),
            patch(
                "payments.authority_services.initiate_refund",
                return_value=legacy_refund,
            ),
        ):
            settle_refund(
                refund=refund,
                provider="metro",
                provider_refund_id="refund-provider-full",
            )

        payment.refresh_from_db()
        self.assertEqual(payment.status, CanonicalPaymentStatus.REFUNDED)

    def test_provider_binding_rejects_reassignment(self):
        payment = bind_payment_provider(
            payment=self.payment(key="provider-owner-1"),
            provider="metro",
            provider_payment_id="provider-payment-1",
        )
        with self.assertRaises(PaymentAuthorityError):
            bind_payment_provider(
                payment=payment,
                provider="metro",
                provider_payment_id="provider-payment-2",
            )

    def test_refund_hard_delete_is_blocked(self):
        payment = self.settled_payment(key="refund-delete-payment")
        refund = request_refund(
            payment=payment,
            amount_cents=1000,
            idempotency_key="refund-delete-1",
        )
        with self.assertRaises(ValidationError):
            refund.delete()
        with self.assertRaises(ValidationError):
            Refund.objects.filter(pk=refund.pk).delete()
