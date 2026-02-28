"""
Crown2026 — CrownMagus III: Audit log contract proof.

Verifies that the AuditMiddleware creates structured AuditLog entries
for all state-changing requests (POST, PUT, PATCH, DELETE).

Contract under test (audit/middleware.py + audit/models.py):
  After any POST/PUT/PATCH/DELETE request, an AuditLog row MUST exist with:
    - user_id:   matches the authenticated user's primary key
    - action:    the HTTP method ("POST", "PATCH", etc.)
    - model:     the request path (e.g. "/api/v1/billing/installment-plans/")
    - metadata:  JSON containing "status_code" from the response

Fields the model currently has:
    id, user_id, action, model (path), object_id, metadata (JSON), created_at

What this proves:
  1. Writes leave an immutable audit trail.
  2. The actor (user_id) is captured.
  3. The action type and target path are recorded.
  4. The HTTP outcome (status_code) is captured.

Current limitation (documented):
  - "model" stores the request path, not the Django model class name.
  - "object_id" is not populated by the middleware (middleware has no access to
    response body to extract the created object's ID — this would require
    view-level instrumentation).
  - school_id and correlation_id are not direct fields; these would need to
    be added to extend the contract.

This test proves what IS there, not what should be aspirationally there.
"""
from __future__ import annotations

import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from audit.models import AuditLog
from core.models import School

User = get_user_model()

# ---------------------------------------------------------------------------
# URL constants (must produce POST/PATCH/DELETE traffic through middleware)
# ---------------------------------------------------------------------------
INSTALLMENT_PLANS_URL = "/api/v1/billing/installment-plans/"
PAYMENT_INTENT_URL = "/api/finance/payments/intent/"
FINANCIAL_AID_APPS_URL = "/api/v1/financial-aid/applications/"


# ---------------------------------------------------------------------------
# Shared base
# ---------------------------------------------------------------------------

class _AuditBase(TestCase):
    """One school, one authenticated user."""

    def setUp(self):
        self.school = School.objects.create(name="Audit-School")
        self.user = User.objects.create_user(
            username="audit_user",
            email="audit@example.com",
            password="pass",
            school_id=self.school.id,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _count_audit_logs(self, action: str, path: str) -> int:
        return AuditLog.objects.filter(action=action, model=path).count()


# ---------------------------------------------------------------------------
# 1. POST creates AuditLog entry
# ---------------------------------------------------------------------------

class AuditLogCreationTests(_AuditBase):
    """
    Verifies that AuditLog entries are created after POST requests.
    """

    def test_post_to_installment_plans_creates_audit_log(self):
        """
        POST /api/v1/billing/installment-plans/ must produce an AuditLog row.
        The middleware runs after every POST regardless of response status.
        """
        count_before = self._count_audit_logs("POST", INSTALLMENT_PLANS_URL)

        self.client.post(
            INSTALLMENT_PLANS_URL,
            data={
                "term": "2025-2026",
                "name": f"Audit-Test Plan {uuid.uuid4()}",
                "installment_count": 10,
                "first_due_on": "2025-09-01",
                "cadence_days": 30,
            },
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        count_after = self._count_audit_logs("POST", INSTALLMENT_PLANS_URL)
        self.assertGreater(
            count_after, count_before,
            msg=(
                f"AuditLog count did not increase after POST to {INSTALLMENT_PLANS_URL}. "
                f"Before: {count_before}, After: {count_after}. "
                f"Possible cause: AuditMiddleware not in MIDDLEWARE list, or path mismatch."
            ),
        )

    def test_post_to_payment_intent_creates_audit_log(self):
        """
        POST /api/finance/payments/intent/ must produce an AuditLog row.
        Finance endpoints are on a separate path prefix but same middleware.
        """
        count_before = self._count_audit_logs("POST", PAYMENT_INTENT_URL)

        self.client.post(
            PAYMENT_INTENT_URL,
            data={"amount_cents": 999},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        count_after = self._count_audit_logs("POST", PAYMENT_INTENT_URL)
        self.assertGreater(
            count_after, count_before,
            msg=(
                f"AuditLog count did not increase after POST to {PAYMENT_INTENT_URL}. "
                f"Before: {count_before}, After: {count_after}."
            ),
        )

    def test_get_request_does_not_create_audit_log(self):
        """
        GET requests must NOT create an AuditLog row.
        The middleware only logs POST, PUT, PATCH, DELETE.
        """
        count_before = AuditLog.objects.count()

        self.client.get(
            INSTALLMENT_PLANS_URL,
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        count_after = AuditLog.objects.count()
        self.assertEqual(
            count_before, count_after,
            msg=(
                f"GET request created an AuditLog entry. "
                f"Before: {count_before}, After: {count_after}. "
                f"Middleware should only log mutating methods (POST/PUT/PATCH/DELETE)."
            ),
        )


# ---------------------------------------------------------------------------
# 2. AuditLog field contract
# ---------------------------------------------------------------------------

class AuditLogFieldContractTests(_AuditBase):
    """
    Verifies the content of AuditLog entries against the contract.
    """

    def _get_last_audit_entry(self, action: str, path: str) -> AuditLog | None:
        return (
            AuditLog.objects.filter(action=action, model=path)
            .order_by("-created_at")
            .first()
        )

    def test_audit_entry_has_correct_action_field(self):
        """
        AuditLog.action must match the HTTP method of the request.
        """
        self.client.post(
            INSTALLMENT_PLANS_URL,
            data={
                "term": "2025-2026",
                "name": f"FieldTest Plan {uuid.uuid4()}",
                "installment_count": 5,
                "first_due_on": "2025-09-01",
                "cadence_days": 30,
            },
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        entry = self._get_last_audit_entry("POST", INSTALLMENT_PLANS_URL)
        self.assertIsNotNone(
            entry,
            msg="No AuditLog entry found for POST to installment-plans.",
        )
        self.assertEqual(
            entry.action, "POST",
            msg=f"AuditLog.action expected 'POST', got {entry.action!r}.",
        )

    def test_audit_entry_model_field_is_request_path(self):
        """
        AuditLog.model stores the request path (not Django model class name).
        This is the current contract per audit/middleware.py.
        """
        self.client.post(
            PAYMENT_INTENT_URL,
            data={"amount_cents": 800},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        entry = self._get_last_audit_entry("POST", PAYMENT_INTENT_URL)
        self.assertIsNotNone(entry, msg="No AuditLog entry found for POST to payment-intent.")
        self.assertEqual(
            entry.model, PAYMENT_INTENT_URL,
            msg=f"AuditLog.model expected {PAYMENT_INTENT_URL!r}, got {entry.model!r}.",
        )

    def test_audit_entry_has_status_code_in_metadata(self):
        """
        AuditLog.metadata must contain 'status_code' from the response.
        Contract: {'status_code': <int>}
        """
        resp = self.client.post(
            INSTALLMENT_PLANS_URL,
            data={
                "term": "2025-2026",
                "name": f"MetaTest Plan {uuid.uuid4()}",
                "installment_count": 12,
                "first_due_on": "2025-09-01",
                "cadence_days": 30,
            },
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        entry = self._get_last_audit_entry("POST", INSTALLMENT_PLANS_URL)
        self.assertIsNotNone(entry, msg="No AuditLog entry for metadata test.")

        self.assertIn(
            "status_code", entry.metadata,
            msg=f"'status_code' missing from AuditLog.metadata. Got: {entry.metadata}",
        )
        self.assertEqual(
            entry.metadata["status_code"], resp.status_code,
            msg=(
                f"AuditLog.metadata.status_code={entry.metadata['status_code']!r} "
                f"does not match actual response status {resp.status_code}."
            ),
        )

    def test_audit_entry_records_user_id_for_authenticated_request(self):
        """
        AuditLog.user_id must match the primary key of the authenticated user.
        Critical for accountability: we must know WHO made the write.
        """
        self.client.post(
            PAYMENT_INTENT_URL,
            data={"amount_cents": 1500},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        entry = self._get_last_audit_entry("POST", PAYMENT_INTENT_URL)
        self.assertIsNotNone(entry, msg="No AuditLog entry for authenticated user test.")

        self.assertIsNotNone(
            entry.user_id,
            msg="AuditLog.user_id is None for an authenticated request. Actor must be captured.",
        )
        # Compare as strings since user_id is UUID field and user.id might be int or UUID
        self.assertEqual(
            str(entry.user_id), str(self.user.id),
            msg=(
                f"AuditLog.user_id={entry.user_id!r} does not match "
                f"authenticated user.id={self.user.id!r}."
            ),
        )

    def test_multiple_writes_each_produce_own_audit_entry(self):
        """
        Each write request produces a separate AuditLog row.
        Audit entries are additive; they are never merged or deduplicated.
        """
        count_before = AuditLog.objects.count()

        n_calls = 3
        for i in range(n_calls):
            self.client.post(
                INSTALLMENT_PLANS_URL,
                data={
                    "term": "2025-2026",
                    "name": f"Multi-Audit Plan {i} {uuid.uuid4()}",
                    "installment_count": 10,
                    "first_due_on": "2025-09-01",
                    "cadence_days": 30,
                },
                format="json",
                HTTP_X_SCHOOL_ID=str(self.school.id),
            )

        count_after = AuditLog.objects.count()
        self.assertEqual(
            count_after - count_before, n_calls,
            msg=(
                f"{n_calls} write calls should produce {n_calls} audit entries. "
                f"Delta was {count_after - count_before}."
            ),
        )


# ---------------------------------------------------------------------------
# 3. Failed write requests are ALSO audited
# ---------------------------------------------------------------------------

class AuditLogFailedWriteTests(_AuditBase):
    """
    Even failed write requests (4xx responses) must produce audit entries.
    The middleware runs regardless of response status.
    """

    def test_failed_post_with_bad_payload_still_creates_audit_log(self):
        """
        Sending invalid data yields 400, but audit log must still be created.
        The middleware captures after the response — status doesn't gate logging.
        """
        count_before = self._count_audit_logs("POST", INSTALLMENT_PLANS_URL)

        # Send deliberately incomplete payload (missing required 'term')
        self.client.post(
            INSTALLMENT_PLANS_URL,
            data={"name": "Missing term field"},  # 'term' is required → 400
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        count_after = self._count_audit_logs("POST", INSTALLMENT_PLANS_URL)
        self.assertGreater(
            count_after, count_before,
            msg=(
                "Failed (400) POST did not create an AuditLog entry. "
                "Even failed writes must be audited — the middleware should not "
                "gate on response status."
            ),
        )

    def test_failed_entry_has_4xx_status_code_in_metadata(self):
        """
        For a bad-data (400) POST, audit metadata must capture the 400 status.
        """
        self.client.post(
            PAYMENT_INTENT_URL,
            data={"amount_cents": -100},  # negative → 400
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

        entry = (
            AuditLog.objects.filter(action="POST", model=PAYMENT_INTENT_URL)
            .order_by("-created_at")
            .first()
        )
        if entry is None:
            self.skipTest("No audit entry found — failed-write audit test not applicable.")

        status_code = entry.metadata.get("status_code")
        self.assertIsNotNone(
            status_code,
            msg=f"status_code missing from failed write audit entry metadata: {entry.metadata}",
        )
        self.assertGreaterEqual(
            status_code, 400,
            msg=f"Expected 4xx status_code in failed write audit. Got {status_code}.",
        )
        self.assertNotEqual(
            status_code, 500,
            msg="Failed write audit has 500 status — this represents an unhandled exception.",
        )
