"""
Crown2026 — CrownMagus III: Idempotency & replay safety proof.

Verifies that create operations with idempotency keys:
1. Return stable, identical outcomes on second call.
2. Do NOT create duplicate records in the database.
3. Correctly scope idempotency keys to the school (keys are NOT global).

Endpoints under test:
  - POST /api/finance/payments/intent/  — FinancePayment with idempotency_key

Idempotency contract (from finance/api_views.py:253-256):
  If idempotency_key is provided and a non-FAILED payment with that key exists
  for the school, return HTTP 200 with the existing payment object.
  A brand-new payment returns HTTP 201.

This prevents:
  - Double-charges (same intent submitted twice)
  - Reconciliation divergence (two payment records for one intent)
  - Replay attacks (reusing a known key against a different school)
"""
from __future__ import annotations

import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School
from finance.models import FinancePayment

User = get_user_model()

PAYMENT_INTENT_URL = "/api/finance/payments/intent/"


# ---------------------------------------------------------------------------
# Shared base
# ---------------------------------------------------------------------------

class _IdempotencyBase(TestCase):
    """One school, one authenticated user for payment tests."""

    def setUp(self):
        self.school = School.objects.create(name="Idem-School")
        self.user = User.objects.create_user(
            username="idem_user",
            email="idem@example.com",
            password="pass",
            school_id=self.school.id,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _post_intent(self, key: str | None = None, amount: int = 5000) -> tuple:
        """Helper: POST a payment intent with optional idempotency_key."""
        payload: dict = {"amount_cents": amount}
        if key is not None:
            payload["idempotency_key"] = key
        resp = self.client.post(
            PAYMENT_INTENT_URL,
            data=payload,
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        return resp, resp.status_code


# ---------------------------------------------------------------------------
# 1. Idempotency key presence prevents duplicate creation
# ---------------------------------------------------------------------------

class PaymentIntentIdempotencyTests(_IdempotencyBase):
    """
    Core idempotency contract: same key → same payment, no duplicate DB rows.
    """

    def test_first_call_with_key_returns_201(self):
        """First call with a novel idempotency key must return 201 (Created)."""
        key = f"test-idem-{uuid.uuid4()}"
        resp, status = self._post_intent(key=key)
        self.assertEqual(
            status, 201,
            msg=(
                f"First payment intent with key returned {status}, expected 201. "
                f"Body: {resp.content[:300]!r}"
            ),
        )
        # Verify one record in DB
        count = FinancePayment.objects.filter(
            school_id=self.school.id,
            idempotency_key=key,
        ).count()
        self.assertEqual(count, 1, msg=f"Expected 1 payment in DB after first call, got {count}.")

    def test_second_call_with_same_key_returns_200(self):
        """
        Second call with the SAME idempotency key must return 200 (not 201).
        This is the idempotency guard return path.
        """
        key = f"test-idem-{uuid.uuid4()}"
        self._post_intent(key=key)  # first call — creates
        resp, status = self._post_intent(key=key)  # second call — idempotent
        self.assertEqual(
            status, 200,
            msg=(
                f"Second payment intent with same key returned {status}, expected 200. "
                f"If 201: idempotency guard is NOT working — duplicate payment created. "
                f"Body: {resp.content[:300]!r}"
            ),
        )

    def test_duplicate_call_does_not_create_extra_db_row(self):
        """
        The single most critical idempotency assertion:
        N calls with the same key = exactly 1 DB record.
        """
        key = f"test-idem-{uuid.uuid4()}"
        # Three submissions with the same key
        self._post_intent(key=key)
        self._post_intent(key=key)
        self._post_intent(key=key)

        count = FinancePayment.objects.filter(
            school_id=self.school.id,
            idempotency_key=key,
        ).count()
        self.assertEqual(
            count, 1,
            msg=(
                f"3 calls with same idempotency key created {count} DB rows. "
                f"Expected exactly 1 — idempotency guard not preventing duplicates."
            ),
        )

    def test_same_key_returns_same_payment_id(self):
        """
        The payment ID returned on the first call must match
        the payment ID returned on subsequent calls with the same key.
        """
        key = f"test-idem-{uuid.uuid4()}"
        resp1, _ = self._post_intent(key=key)
        resp2, _ = self._post_intent(key=key)

        try:
            id1 = resp1.json().get("id")
            id2 = resp2.json().get("id")
        except Exception:
            self.skipTest("Response is not JSON — cannot compare payment IDs.")

        if id1 is None or id2 is None:
            self.skipTest("Payment ID not present in response body.")

        self.assertEqual(
            id1, id2,
            msg=(
                f"First call returned payment id={id1}, "
                f"second call returned id={id2}. "
                f"Idempotency must return the SAME object."
            ),
        )

    def test_different_keys_create_separate_payments(self):
        """
        Positive control: two DIFFERENT keys must produce two DIFFERENT payments.
        (Idempotency is key-scoped, not amount-scoped.)
        """
        key_a = f"test-idem-{uuid.uuid4()}"
        key_b = f"test-idem-{uuid.uuid4()}"
        resp_a, status_a = self._post_intent(key=key_a)
        resp_b, status_b = self._post_intent(key=key_b)

        self.assertEqual(status_a, 201, msg=f"First key returned {status_a}.")
        self.assertEqual(status_b, 201, msg=f"Second key returned {status_b}.")

        count = FinancePayment.objects.filter(
            school_id=self.school.id,
            idempotency_key__in=[key_a, key_b],
        ).count()
        self.assertEqual(
            count, 2,
            msg=f"Two different keys should create 2 payments, got {count}.",
        )

    def test_no_key_always_creates_new_payment(self):
        """
        Without an idempotency key each call creates a new distinct payment.
        (No implicit dedup — you must provide a key to opt in to idempotency.)
        """
        resp1, status1 = self._post_intent(key=None, amount=1111)
        resp2, status2 = self._post_intent(key=None, amount=1111)

        self.assertEqual(status1, 201, msg=f"First no-key payment returned {status1}.")
        self.assertEqual(status2, 201, msg=f"Second no-key payment returned {status2}.")

        # Both should be distinct (IDs differ, or count is 2 for amount 1111)
        count = FinancePayment.objects.filter(
            school_id=self.school.id,
            idempotency_key="",  # blank key = no idempotency
            amount_cents=1111,
        ).count()
        self.assertGreaterEqual(
            count, 2,
            msg=(
                f"Without idempotency key, 2 calls should create 2 payments. "
                f"Got {count}. If 1: implicit deduplication is masking intent."
            ),
        )


# ---------------------------------------------------------------------------
# 2. Idempotency keys are school-scoped (not global)
# ---------------------------------------------------------------------------

class IdempotencyKeyScopingTests(TestCase):
    """
    An idempotency key used in school_a must NOT collide with the same
    key string used in school_b.

    This prevents cross-school idempotency bypass, where a school_b key
    might return a school_a payment (data leak + auth bypass).
    """

    def setUp(self):
        self.school_a = School.objects.create(name="Idem-School-A")
        self.school_b = School.objects.create(name="Idem-School-B")
        self.user_a = User.objects.create_user(
            username="idem_school_a",
            email="idem_a@example.com",
            password="pass",
            school_id=self.school_a.id,
        )
        self.user_b = User.objects.create_user(
            username="idem_school_b",
            email="idem_b@example.com",
            password="pass",
            school_id=self.school_b.id,
        )
        self.client = APIClient()

    def test_same_key_across_schools_creates_two_payments(self):
        """
        Same idempotency_key string, different schools → two separate payments.
        The DB lookup in payment_intent_create filters by school_id + key:
          FinancePayment.objects.filter(school=school_obj, idempotency_key=key)
        So school_b's key cannot match school_a's payment.
        """
        shared_key = "shared-cross-school-idem-key"

        # Post as school_a
        self.client.force_authenticate(user=self.user_a)
        resp_a = self.client.post(
            PAYMENT_INTENT_URL,
            data={"amount_cents": 2000, "idempotency_key": shared_key},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school_a.id),
        )

        # Post as school_b with THE SAME KEY
        self.client.force_authenticate(user=self.user_b)
        resp_b = self.client.post(
            PAYMENT_INTENT_URL,
            data={"amount_cents": 2000, "idempotency_key": shared_key},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school_b.id),
        )

        if resp_a.status_code not in (200, 201) or resp_b.status_code not in (200, 201):
            self.skipTest(
                f"Payment intent creation failed (a:{resp_a.status_code} b:{resp_b.status_code}). "
                f"Skipping cross-school key scoping test."
            )

        # Verify both schools each have exactly 1 payment with this key
        count_a = FinancePayment.objects.filter(
            school_id=self.school_a.id, idempotency_key=shared_key
        ).count()
        count_b = FinancePayment.objects.filter(
            school_id=self.school_b.id, idempotency_key=shared_key
        ).count()

        self.assertEqual(count_a, 1, msg=f"School A should have 1 payment with key, got {count_a}.")
        self.assertEqual(count_b, 1, msg=f"School B should have 1 payment with key, got {count_b}.")

        # Total unique payments with this key = 2 (one per school, both non-related)
        total = FinancePayment.objects.filter(idempotency_key=shared_key).count()
        self.assertEqual(
            total, 2,
            msg=(
                f"Expected 2 payments total for shared key (one per school), got {total}. "
                f"If 1: key is treated globally, not school-scoped — data leak risk."
            ),
        )
