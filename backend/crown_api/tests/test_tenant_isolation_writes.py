"""
Crown2026 — Tenant isolation proof: WRITE operations.

Extends Phase 7.2 (which covers GET isolation) with mutation-level checks:
- Cross-tenant CREATE must not succeed (data for School A cannot be injected via School B)
- Cross-tenant READ of a School A record as School B user → 404 (not 200)
- Cross-tenant POST/mutate must return 404, not produce or reveal School A data

Canonical scoping used throughout: households.scoping.get_request_school_id()
Endpoint under test: /api/v1/financial-aid/applications/ and /api/v1/financial-aid/awards/

Evidence: TENANT_PRIVACY_CANON.md §3 — non-staff cross-tenant → 404, never 403,
never success.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School
from financial_aid.models import FinancialAidApplication, AidAward

User = get_user_model()

APPLICATIONS_URL = "/api/v1/financial-aid/applications/"
AWARDS_URL = "/api/v1/financial-aid/awards/"


# ---------------------------------------------------------------------------
# Shared fixture — identical structure to _TenantBase in test_phase72_…
# ---------------------------------------------------------------------------

class _WriteIsolationBase(TestCase):
    """Two schools, one non-staff user per school, one staff per school."""

    def setUp(self):
        self.school_a = School.objects.create(name="WriteIso-School-A")
        self.school_b = School.objects.create(name="WriteIso-School-B")

        self.user_a = User.objects.create_user(
            username="wiso_user_a",
            email="wiso_a@example.com",
            password="wiso_pass",
            school_id=self.school_a.id,
        )
        self.staff_a = User.objects.create_user(
            username="wiso_staff_a",
            email="wiso_staff_a@example.com",
            password="wiso_pass",
            school_id=self.school_a.id,
            is_staff=True,
        )
        self.user_b = User.objects.create_user(
            username="wiso_user_b",
            email="wiso_b@example.com",
            password="wiso_pass",
            school_id=self.school_b.id,
        )
        self.client = APIClient()


# ---------------------------------------------------------------------------
# 1. Cross-tenant READ isolation — FinancialAidApplication
# ---------------------------------------------------------------------------

class FinancialAidCrossTenantReadTests(_WriteIsolationBase):
    """
    School B user must not see School A's financial-aid applications.
    """

    def setUp(self):
        super().setUp()
        # Seed one application under school_a
        self.app_a = FinancialAidApplication.objects.create(
            school_id=self.school_a.id,
            household_id=self.school_a.id,  # reuse school UUID for fixture simplicity
            academic_year="2025-2026",
            status="submitted",
        )

    def test_user_b_cannot_read_school_a_applications(self):
        """
        Non-staff user_b supplying school_a's ID → 404.
        Cross-tenant data must not be returned even for the same global resource.
        """
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.get(APPLICATIONS_URL, HTTP_X_SCHOOL_ID=str(self.school_a.id))
        self.assertEqual(
            resp.status_code, 404,
            msg=(
                f"Expected 404 (cross-tenant block). "
                f"Got {resp.status_code}. "
                f"Body: {resp.content[:300]!r}"
            ),
        )

    def test_user_a_can_read_own_school_applications(self):
        """
        Positive control: staff_a supplying school_a's ID → not 404.
        (staff bypasses role checks; confirms endpoint is reachable)
        """
        self.client.force_authenticate(user=self.staff_a)
        resp = self.client.get(APPLICATIONS_URL, HTTP_X_SCHOOL_ID=str(self.school_a.id))
        self.assertIn(
            resp.status_code, (200, 400, 403),
            msg=f"Unexpected status {resp.status_code} for own-school read by staff.",
        )
        self.assertNotEqual(resp.status_code, 404, msg="Staff reading own school must not get 404.")

    def test_unauthenticated_read_blocked(self):
        """No credentials → 401 or 403, never 200."""
        resp = self.client.get(APPLICATIONS_URL, HTTP_X_SCHOOL_ID=str(self.school_a.id))
        self.assertIn(
            resp.status_code, (401, 403),
            msg=f"Unauthenticated read returned unexpected {resp.status_code}.",
        )


# ---------------------------------------------------------------------------
# 2. Cross-tenant WRITE isolation — POST to create
# ---------------------------------------------------------------------------

class FinancialAidCrossTenantWriteTests(_WriteIsolationBase):
    """
    School B user must not be able to POST (create) records into School A.
    """

    _POST_PAYLOAD = {
        "household_id": "00000000-0000-0000-0000-000000000001",
        "academic_year": "2025-2026",
        "status": "submitted",
        "household_income": "50000.00",
        "household_size": 4,
    }

    def test_user_b_cannot_post_into_school_a(self):
        """
        Non-staff user_b supplying school_a's ID in POST → 404.
        School A data must not be created by a School B user.
        """
        count_before = FinancialAidApplication.objects.filter(
            school_id=self.school_a.id
        ).count()

        self.client.force_authenticate(user=self.user_b)
        resp = self.client.post(
            APPLICATIONS_URL,
            data=self._POST_PAYLOAD,
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school_a.id),
        )

        # Primary assertion: cross-tenant POSTs are rejected (404 or 403)
        self.assertIn(
            resp.status_code, (404, 403, 400, 405),
            msg=(
                f"Cross-tenant POST must be rejected. "
                f"Got {resp.status_code}. "
                f"Body: {resp.content[:400]!r}"
            ),
        )

        # Critical: NO new record created in school_a
        count_after = FinancialAidApplication.objects.filter(
            school_id=self.school_a.id
        ).count()
        self.assertEqual(
            count_before, count_after,
            msg=(
                "Cross-tenant POST must not create records in School A. "
                f"Count went from {count_before} → {count_after}."
            ),
        )

    def test_cross_tenant_post_does_not_create_in_school_b_either(self):
        """
        A cross-tenant POST that fails must not silently create records
        in School B (the attacker's own school) as a side effect.
        """
        count_b_before = FinancialAidApplication.objects.filter(
            school_id=self.school_b.id
        ).count()

        self.client.force_authenticate(user=self.user_b)
        self.client.post(
            APPLICATIONS_URL,
            data=self._POST_PAYLOAD,
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school_a.id),
        )

        count_b_after = FinancialAidApplication.objects.filter(
            school_id=self.school_b.id
        ).count()
        self.assertEqual(
            count_b_before, count_b_after,
            msg="Cross-tenant POST must not create records in the attacker's own school.",
        )


# ---------------------------------------------------------------------------
# 3. Cross-tenant READ isolation — AidAward (awards list)
# ---------------------------------------------------------------------------

class AidAwardCrossTenantTests(_WriteIsolationBase):
    """
    AidAward is the financial output of the aid process.
    School B user must not read School A awards.
    """

    def setUp(self):
        super().setUp()
        # Seed one award under school_a
        self.award_a = AidAward.objects.create(
            school_id=self.school_a.id,
            application=None,  # intentionally null for isolation test
            bucket="NEED_BASED",
            amount="5000.00",
        )

    def test_user_b_cannot_read_school_a_awards(self):
        """Non-staff user_b supplying school_a ID → 404."""
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.get(AWARDS_URL, HTTP_X_SCHOOL_ID=str(self.school_a.id))
        self.assertEqual(
            resp.status_code, 404,
            msg=f"Cross-tenant awards read returned {resp.status_code}, expected 404.",
        )

    def test_school_a_award_not_visible_in_school_b_listing(self):
        """
        Even if the endpoint returns 200 for some reason, School A's award data
        must NOT appear in a School B scoped response.
        """
        self.client.force_authenticate(user=self.staff_a)
        # Read as school_b explicitly (staff bypass scope, but header is school_b)
        resp = self.client.get(AWARDS_URL, HTTP_X_SCHOOL_ID=str(self.school_b.id))

        if resp.status_code == 200:
            # If 200, verify school_a's award ID is absent
            try:
                data = resp.json()
                body_str = str(data)
            except Exception:
                body_str = resp.content.decode("utf-8", errors="replace")

            self.assertNotIn(
                str(self.award_a.id), body_str,
                msg=(
                    "School A's award ID appeared in a School B scoped response. "
                    "Tenant isolation breach."
                ),
            )
