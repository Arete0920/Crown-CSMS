import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase

from payments.authority_services import (
    PaymentAuthorityError,
    create_payment,
    settle_payment,
)


class CanonicalAllocationIntegrityTest(TestCase):
    def test_duplicate_obligation_allocation_fails_before_legacy_bridge(self):
        school_id = uuid.UUID("00000000-0000-0000-0000-000000000051")
        household_id = uuid.UUID("00000000-0000-0000-0000-000000000052")
        payment = create_payment(
            school_id=school_id,
            household_id=household_id,
            finance_payment_id=812,
            amount_cents=10_000,
            currency="USD",
            idempotency_key="duplicate-allocation-guard",
        )
        legacy_payment = SimpleNamespace(
            pk=812,
            school_id=school_id,
            amount_cents=10_000,
            currency="USD",
            processor="manual",
            status="pending",
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
            with self.assertRaisesRegex(
                PaymentAuthorityError,
                "same obligation more than once",
            ):
                settle_payment(
                    payment=payment,
                    allocations_payload=[
                        {"obligation_id": 7, "amount_cents": 4_000},
                        {"obligation_id": 7, "amount_cents": 3_000},
                    ],
                )

        settle_mock.assert_not_called()
        payment.refresh_from_db()
        self.assertEqual(payment.status, "pending")
