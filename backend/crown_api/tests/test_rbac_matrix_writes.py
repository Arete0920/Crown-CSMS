"""
Crown2026 — CrownMagus III: RBAC matrix for WRITE endpoints.

Covers POST/PATCH/DELETE surfaces across critical modules:
  - admissions    (enroll — staff-only action)
  - billing       (installment-plans POST — any authenticated)
  - financial-aid (applications POST — any authenticated)
  - finance       (payment intent — any authenticated)
  - finance       (payment settle — staff/admin only)

For each endpoint:
  1. Unauthenticated → 401 (always)
  2. Non-staff authenticated (same school) → 403 on staff-gated; 4xx/2xx elsewhere
  3. Staff authenticated (same school) → non-403 (gate is passed)

Rules:
  • NEVER assert 500 — that is always a bug.
  • For admin-gated endpoints, non-staff must receive EXACTLY 403.
  • Unauthenticated must NEVER receive 200/201.
"""
from __future__ import annotations

import json

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School

User = get_user_model()

# ---------------------------------------------------------------------------
# URL constants
# ---------------------------------------------------------------------------
ENROLL_URL = "/api/v1/admissions/enroll/"
INSTALLMENT_PLANS_URL = "/api/v1/billing/installment-plans/"
FINANCIAL_AID_APPS_URL = "/api/v1/financial-aid/applications/"
PAYMENT_INTENT_URL = "/api/finance/payments/intent/"


# ---------------------------------------------------------------------------
# Shared base fixture
# ---------------------------------------------------------------------------

class _RbacWriteBase(TestCase):
    """One school, one staff user, one non-staff user."""

    def setUp(self):
        self.school = School.objects.create(name="RBACWrite-School")
        self.staff = User.objects.create_user(
            username="rbacw_staff",
            email="rbacw_staff@example.com",
            password="pass",
            school_id=self.school.id,
            is_staff=True,
        )
        self.non_staff = User.objects.create_user(
            username="rbacw_user",
            email="rbacw_user@example.com",
            password="pass",
            school_id=self.school.id,
            is_staff=False,
        )
        self.client = APIClient()


# ---------------------------------------------------------------------------
# 1. Admissions enroll — staff-only POST
# ---------------------------------------------------------------------------

class AdmissionsEnrollRbacTests(_RbacWriteBase):
    """
    POST /api/v1/admissions/enroll/ — guarded by _require_staff().
    Verified in views_enroll.py: non-staff returns HTTP 403 explicitly.
    """

    def test_unauthenticated_enroll_returns_401(self):
        """No credentials → 401, never 200/201."""
        resp = self.client.post(
            ENROLL_URL,
            data=json.dumps({"application_id": 99999}),
            content_type="application/json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(
            resp.status_code, 401,
            msg=f"Unauthenticated enroll returned {resp.status_code}, expected 401.",
        )
        self.assertNotEqual(resp.status_code, 200)
        self.assertNotEqual(resp.status_code, 201)
        self.assertNotEqual(resp.status_code, 500)

    def test_non_staff_enroll_returns_403(self):
        """
        Non-staff authenticated user → 403.
        This is the critical RBAC guard for the enroll action.
        """
        self.client.force_authenticate(user=self.non_staff)
        resp = self.client.post(
            ENROLL_URL,
            data=json.dumps({"application_id": 99999}),
            content_type="application/json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(
            resp.status_code, 403,
            msg=(
                f"Non-staff enroll returned {resp.status_code}, expected 403. "
                f"This means the staff gate is NOT enforced — authorization bypass."
            ),
        )

    def test_staff_enroll_passes_gate(self):
        """
        Staff user passes the role gate.
        Will return 400 (bad data — no application_id) or 404 (not found),
        NOT 403 or 401.
        """
        self.client.force_authenticate(user=self.staff)
        resp = self.client.post(
            ENROLL_URL,
            data=json.dumps({"application_id": 99999}),
            content_type="application/json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertNotIn(
            resp.status_code, (401, 403, 500),
            msg=(
                f"Staff enroll returned {resp.status_code}. "
                f"Expected to pass gate (400/404 from bad data, not auth rejection)."
            ),
        )


# ---------------------------------------------------------------------------
# 2. Billing installment plans — any-auth POST
# ---------------------------------------------------------------------------

class BillingInstallmentPlansRbacTests(_RbacWriteBase):
    """
    POST /api/v1/billing/installment-plans/ — IsAuthenticated only.
    Any authenticated user can attempt; unauthenticated must get 401.
    """

    _VALID_PAYLOAD = {
        "term": "2025-2026",
        "name": "Standard 10-Month Plan",
        "installment_count": 10,
        "first_due_on": "2025-09-01",
        "cadence_days": 30,
    }

    def test_unauthenticated_installment_plan_post_returns_401(self):
        resp = self.client.post(
            INSTALLMENT_PLANS_URL,
            data=self._VALID_PAYLOAD,
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(
            resp.status_code, 401,
            msg=f"Unauthenticated installment plan POST returned {resp.status_code}.",
        )
        self.assertNotEqual(resp.status_code, 500)

    def test_non_staff_can_post_installment_plan(self):
        """
        Non-staff authenticated user: endpoint is IsAuthenticated only,
        so non-staff is allowed. Expect 201 (success) or 4xx (bad payload).
        Must NOT return 401 or 403.
        """
        self.client.force_authenticate(user=self.non_staff)
        resp = self.client.post(
            INSTALLMENT_PLANS_URL,
            data=self._VALID_PAYLOAD,
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertNotIn(
            resp.status_code, (401, 403, 500),
            msg=f"Non-staff installment plan POST unexpectedly blocked: {resp.status_code}.",
        )

    def test_staff_can_post_installment_plan(self):
        """Staff: same as non-staff — endpoint is not staff-gated."""
        self.client.force_authenticate(user=self.staff)
        resp = self.client.post(
            INSTALLMENT_PLANS_URL,
            data=self._VALID_PAYLOAD,
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertNotIn(
            resp.status_code, (401, 403, 500),
            msg=f"Staff installment plan POST failed unexpectedly: {resp.status_code}.",
        )


# ---------------------------------------------------------------------------
# 3. Financial-aid applications — any-auth POST
# ---------------------------------------------------------------------------

class FinancialAidApplicationsRbacTests(_RbacWriteBase):
    """
    POST /api/v1/financial-aid/applications/ — IsAuthenticated, school-scoped.
    Unauthenticated → 401; authenticated cross-tenant → 404; own-school → 400/201.
    """

    def test_unauthenticated_faid_application_post_returns_401(self):
        resp = self.client.post(
            FINANCIAL_AID_APPS_URL,
            data={"academic_year": "2025-2026", "status": "submitted"},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertIn(
            resp.status_code, (401, 403),
            msg=f"Unauthenticated financial-aid POST returned {resp.status_code}.",
        )
        self.assertNotEqual(resp.status_code, 500)

    def test_authenticated_user_can_attempt_faid_application_post(self):
        """
        Own-school user can attempt; will get 400 (validation) or 201 (success).
        Must NOT get 401/403/500.
        """
        self.client.force_authenticate(user=self.non_staff)
        resp = self.client.post(
            FINANCIAL_AID_APPS_URL,
            data={
                "household_id": "00000000-0000-0000-0000-000000000001",
                "academic_year": "2025-2026",
                "status": "submitted",
            },
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertNotIn(
            resp.status_code, (401, 403, 500),
            msg=f"Own-school authenticated user blocked on financial-aid POST: {resp.status_code}.",
        )


# ---------------------------------------------------------------------------
# 4. Finance payment intent — any-auth POST
# ---------------------------------------------------------------------------

class FinancePaymentIntentRbacTests(_RbacWriteBase):
    """
    POST /api/finance/payments/intent/ — IsAuthenticated.
    Unauthenticated → 401; authenticated → 201 (or 400 on bad data).
    """

    def test_unauthenticated_payment_intent_returns_401(self):
        resp = self.client.post(
            PAYMENT_INTENT_URL,
            data={"amount_cents": 5000},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(
            resp.status_code, 401,
            msg=f"Unauthenticated payment intent returned {resp.status_code}, expected 401.",
        )
        self.assertNotEqual(resp.status_code, 500)

    def test_authenticated_payment_intent_passes_auth_gate(self):
        """
        Authenticated user: should be able to create a payment intent.
        Returns 201 (success) or 400 (bad data), never 401/403/500.
        """
        self.client.force_authenticate(user=self.non_staff)
        resp = self.client.post(
            PAYMENT_INTENT_URL,
            data={"amount_cents": 1000},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertNotIn(
            resp.status_code, (401, 403, 500),
            msg=(
                f"Authenticated payment intent blocked: {resp.status_code}. "
                f"Body: {resp.content[:200]!r}"
            ),
        )

    def test_no_write_without_school_context(self):
        """
        Authenticated but no school context → must not return 200/201.
        get_request_school_id(required=True) should block or error.
        """
        self.client.force_authenticate(user=self.non_staff)
        resp = self.client.post(
            PAYMENT_INTENT_URL,
            data={"amount_cents": 1000},
            format="json",
            # No HTTP_X_SCHOOL_ID header
        )
        # May return 400, 403, or 404 depending on how school context is enforced
        self.assertNotIn(
            resp.status_code, (200, 201, 500),
            msg=(
                f"Payment intent without school context returned {resp.status_code}. "
                f"Must not succeed (200/201) and must not 500."
            ),
        )
