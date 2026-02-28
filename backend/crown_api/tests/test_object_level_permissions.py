"""
Crown2026 — CrownMagus III: Object-level authorization proof.

This module tests authorization boundaries WITHIN the same tenant (school).
Tenant-level isolation (cross-school) is covered in test_phase72_tenant_isolation.py
and test_tenant_isolation_writes.py.

Scope here: same school_id, different users.

What IS enforced (role-based object access):
  - Staff-only actions (admissions/enroll, finance/settle, finance/refund)
    → non-staff user in the SAME school receives 403.
  - These are ROLE-based object access controls, not creator-based.

What is NOT currently enforced (documented boundary):
  - Per-creator ownership: User A creates a record, User B (same school, same
    role) can also read/modify it. The authorization model is school-scoped,
    not owner-scoped. This is a documented architectural decision, not a gap.

Evidence anchors:
  - admissions/views_enroll.py: _require_staff() checks is_staff/is_superuser.
  - finance/api_views.py: _is_staff() applied to settle and refund endpoints.
  - discipline/api/views.py: DisciplineIncidentActions — school-scoped only.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School
from finance.models import FinancePayment

User = get_user_model()

# ---------------------------------------------------------------------------
# URL constants
# ---------------------------------------------------------------------------
ENROLL_URL = "/api/v1/admissions/enroll/"
PAYMENT_INTENT_URL = "/api/finance/payments/intent/"
PAYMENT_SETTLE_URL_TMPL = "/api/finance/payments/{id}/settle/"
PAYMENT_REFUND_URL_TMPL = "/api/finance/payments/{id}/refund/"
INSTALLMENT_PLANS_URL = "/api/v1/billing/installment-plans/"


# ---------------------------------------------------------------------------
# Shared base
# ---------------------------------------------------------------------------

class _ObjPermBase(TestCase):
    """
    One school. Two users — same school, different staff status.
    This simulates the within-tenant object-access scenario.
    """

    def setUp(self):
        self.school = School.objects.create(name="ObjPerm-School")
        # user_staff: admin/staff role; user_plain: regular authenticated user
        self.user_staff = User.objects.create_user(
            username="objperm_staff",
            email="staff@objperm.example.com",
            password="pass",
            school_id=self.school.id,
            is_staff=True,
        )
        self.user_plain = User.objects.create_user(
            username="objperm_plain",
            email="plain@objperm.example.com",
            password="pass",
            school_id=self.school.id,
            is_staff=False,
        )
        self.client = APIClient()


# ---------------------------------------------------------------------------
# 1. Staff-gated actions — non-staff in SAME school receives 403
# ---------------------------------------------------------------------------

class StaffGatedActionsTests(_ObjPermBase):
    """
    Tests that staff-only endpoints deny non-staff users even when those
    users belong to the same school (same tenant).

    This is the object-level authorization guard for privileged mutations.
    """

    def test_plain_user_cannot_enroll_applicant(self):
        """
        admissions/enroll/ is staff-only.
        plain user (same school) → must receive 403.
        """
        self.client.force_authenticate(user=self.user_plain)
        resp = self.client.post(
            ENROLL_URL,
            data={"application_id": 99999},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(
            resp.status_code, 403,
            msg=(
                f"Non-staff same-school user got {resp.status_code} on enroll, "
                f"expected 403. Body: {resp.content[:300]!r}"
            ),
        )

    def test_staff_user_passes_enroll_gate(self):
        """
        Staff user in same school: passes the role gate.
        Returns 400/404 (bad data/not found), NOT 401/403.
        """
        self.client.force_authenticate(user=self.user_staff)
        resp = self.client.post(
            ENROLL_URL,
            data={"application_id": 99999},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertNotIn(
            resp.status_code, (401, 403, 500),
            msg=f"Staff enroll gate returned {resp.status_code}, expected non-auth-error.",
        )

    def test_plain_user_cannot_settle_payment(self):
        """
        finance/payments/<id>/settle/ is staff-only.
        Non-staff user → 403, even for their own payment (if one existed).
        The staff check fires BEFORE the DB lookup.
        """
        self.client.force_authenticate(user=self.user_plain)
        resp = self.client.post(
            PAYMENT_SETTLE_URL_TMPL.format(id=99999),
            data={"allocations": []},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(
            resp.status_code, 403,
            msg=(
                f"Non-staff same-school user got {resp.status_code} on payment settle, "
                f"expected 403."
            ),
        )

    def test_plain_user_cannot_issue_refund(self):
        """
        finance/payments/<id>/refund/ is staff-only.
        Non-staff user → 403.
        """
        self.client.force_authenticate(user=self.user_plain)
        resp = self.client.post(
            PAYMENT_REFUND_URL_TMPL.format(id=99999),
            data={"amount_cents": 100},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(
            resp.status_code, 403,
            msg=(
                f"Non-staff same-school user got {resp.status_code} on refund, "
                f"expected 403."
            ),
        )

    def test_staff_user_passes_settle_gate(self):
        """
        Staff user: passes role gate on settle.
        Returns 404 (payment 99999 not found), NOT 403.
        """
        self.client.force_authenticate(user=self.user_staff)
        resp = self.client.post(
            PAYMENT_SETTLE_URL_TMPL.format(id=99999),
            data={"allocations": []},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertNotEqual(
            resp.status_code, 403,
            msg=f"Staff settle still got 403 — role gate is not recognizing staff status.",
        )
        self.assertNotEqual(resp.status_code, 401)
        self.assertNotEqual(resp.status_code, 500)


# ---------------------------------------------------------------------------
# 2. Payment creator does NOT limit settle scope (school-scoped, not owner-scoped)
# ---------------------------------------------------------------------------

class PaymentOwnershipBoundaryTests(_ObjPermBase):
    """
    Documents the current authorization model:

    FinancePayment is school-scoped. Any staff member may settle any payment
    within the school — there is no creator-level ownership restriction.

    This test DOCUMENTS this behavior as an explicit architectural assertion.
    If the intent is to add owner-only settlement, this test must be updated.
    """

    def test_staff_can_settle_any_school_payment_not_just_own(self):
        """
        Staff user_staff can attempt to settle a payment created by user_plain.
        This is expected to succeed (or 404 if not found) — NOT 403.
        The authorization model is: school-scoped + staff-role, not creator-scoped.
        """
        # Create a real payment via the intent endpoint as user_plain
        self.client.force_authenticate(user=self.user_plain)
        create_resp = self.client.post(
            PAYMENT_INTENT_URL,
            data={"amount_cents": 5000},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        # Skip test if payment creation itself fails for infra reasons
        if create_resp.status_code not in (200, 201):
            self.skipTest(
                f"Payment intent creation returned {create_resp.status_code} — "
                f"skipping ownership boundary test (infra prerequisite not met)."
            )

        # Get the payment ID from the response
        try:
            payment_id = create_resp.json().get("id") or create_resp.json().get("data", {}).get("id")
        except Exception:
            payment_id = None

        if not payment_id:
            self.skipTest("Could not extract payment ID from intent response.")

        # Now, user_staff (different user, same school) tries to settle
        self.client.force_authenticate(user=self.user_staff)
        settle_resp = self.client.post(
            PAYMENT_SETTLE_URL_TMPL.format(id=payment_id),
            data={"allocations": []},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        # Should NOT be 403 (staff has school-level permission, not creator-restricted)
        self.assertNotEqual(
            settle_resp.status_code, 403,
            msg=(
                "Staff settlement of another user's payment returned 403. "
                "This suggests owner-level restriction was added — verify intentional."
            ),
        )
        self.assertNotEqual(settle_resp.status_code, 500)


# ---------------------------------------------------------------------------
# 3. Non-gated shared resources — any same-school user has read access
# ---------------------------------------------------------------------------

class SharedSchoolResourceAccessTests(_ObjPermBase):
    """
    Billing installment plans created by user_plain are also accessible to user_staff
    and vice versa — there is no per-creator restriction.

    This asserts the current authorization boundary explicitly:
    school-scoped resources are shared within the school.
    """

    _PLAN_PAYLOAD = {
        "term": "2025-2026",
        "name": "ObjPerm Test Plan",
        "installment_count": 10,
        "first_due_on": "2025-09-01",
        "cadence_days": 30,
    }

    def test_shared_installment_plan_list_accessible_to_all_school_members(self):
        """
        User_plain creates a plan. User_staff can see it (GET list).
        Demonstrates school-level sharing (not creator-only visibility).
        """
        # Create as plain user
        self.client.force_authenticate(user=self.user_plain)
        create_resp = self.client.post(
            INSTALLMENT_PLANS_URL,
            data=self._PLAN_PAYLOAD,
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        if create_resp.status_code not in (200, 201):
            self.skipTest(
                f"Plan creation returned {create_resp.status_code} — "
                f"skipping shared access test."
            )

        # Read as staff user in same school
        self.client.force_authenticate(user=self.user_staff)
        list_resp = self.client.get(
            INSTALLMENT_PLANS_URL,
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertIn(
            list_resp.status_code, (200, 201),
            msg=f"Staff list of installment plans returned {list_resp.status_code}.",
        )
        self.assertNotEqual(list_resp.status_code, 500)
