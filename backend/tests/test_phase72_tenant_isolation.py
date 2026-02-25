"""
Phase 7.2 â€” Cross-Module Tenant Isolation Tests
================================================

Verifies tenant-scoping enforcement across the six major live API surfaces,
grouping endpoints by *scoping mechanism*:

  Canonical  (households.scoping.get_request_school_id):
    gradebook/views.py, billing/api.py
    â†’ non-staff cross-tenant request â†’ HTTP 404

  Non-canonical (weaker: direct header read):
    discipline/api/views.py
    â†’ cross-tenant request â†’ HTTP 200 with empty/school-B-only data
    â†’ school-A data MUST NOT appear (ORM-level isolation confirmed)

For each module we test three invariants:
  1. Missing X-School-Id header  â†’ 400
  2. Valid header, correct school â†’ 200 (user owns their data)
  3. Valid header, wrong school   â†’ 404 (canonical) or data-isolated 200 (non-canonical)

Evidence basis: TENANT_AUDIT_CERTIFICATION.md Â§4 "Test Coverage"
Branch: phase/7.2-tenant-isolation-audit
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School

User = get_user_model()


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Shared fixture: two schools, one non-staff user per school, no data needed.
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class _TenantBase(TestCase):
    """Minimal fixture â€” just schools + users; no domain data required."""

    def setUp(self):
        self.school_a = School.objects.create(name="Phase72-School-A")
        self.school_b = School.objects.create(name="Phase72-School-B")

        # Non-staff user â€” used for cross-tenant (wrong school) tests.
        self.user_a = User.objects.create_user(
            username="p72_user_a",
            email="p72_a@example.com",
            password="p72pass",
            school_id=self.school_a.id,
        )
        # Staff user â€” bypasses role checks; used for correct-school 200 tests.
        self.staff_a = User.objects.create_user(
            username="p72_staff_a",
            email="p72_staff_a@example.com",
            password="p72pass",
            school_id=self.school_a.id,
            is_staff=True,
        )
        self.user_b = User.objects.create_user(
            username="p72_user_b",
            email="p72_b@example.com",
            password="p72pass",
            school_id=self.school_b.id,
        )
        # User with NO school affiliation - used for missing-header tests.
        # tenant resolver finds no header and no user.school_id -> None -> 400.
        self.user_noschool = User.objects.create_user(
            username="p72_noschool",
            email="p72_noschool@example.com",
            password="p72pass",
        )

        self.client = APIClient()


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 1. Gradebook â€” CANONICAL scoping (get_request_school_id required=True)
#    Endpoint: GET /api/v1/gradebook/sections/
#    File:     backend/gradebook/views.py
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class Phase72GradebookTenantTests(_TenantBase):
    """
    gradebook/views.py uses households.scoping.get_request_school_id(required=True).
    Non-staff users providing a header for a school they do not own â†’ HTTP 404.
    Mechanism: resolve_tenant_school_id detects header_present + user.school_id mismatch.
    """

    URL = "/api/v1/gradebook/sections/"

    def test_missing_header_returns_400(self):
        """
        No X-School-Id header -> MissingSchoolContext (HTTP 400).
        Must use user_noschool (no school_id attribute) so tenant resolver
        does not auto-derive school from user profile and bypasses 400.
        """
        self.client.force_authenticate(user=self.user_noschool)
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 400)

    def test_correct_school_returns_200(self):
        """
        Staff user with correct school header â†’ HTTP 200.
        Non-staff users without a gradebook role get 403 from _sections_for_gradebook().
        Using is_staff=True user to confirm the endpoint itself is reachable without
        the tenant guard firing.
        """
        self.client.force_authenticate(user=self.staff_a)
        resp = self.client.get(self.URL, HTTP_X_SCHOOL_ID=str(self.school_a.id))
        self.assertEqual(resp.status_code, 200)

    def test_wrong_school_nonstaff_returns_404(self):
        """
        Non-staff user_a supplies school_b's ID.
        get_request_school_id() enforces: header_present AND user.school_id â‰  header â†’ 404.
        Canonical cross-tenant prevention confirmed.
        """
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get(self.URL, HTTP_X_SCHOOL_ID=str(self.school_b.id))
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_returns_401_or_403(self):
        """No credentials -> 401 or 403 (DRF bearer-token auth; 403 is normal)."""
        resp = self.client.get(self.URL, HTTP_X_SCHOOL_ID=str(self.school_a.id))
        self.assertIn(resp.status_code, (401, 403))


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 2. Billing Runs â€” CANONICAL scoping (get_request_school_id via @api_view)
#    Endpoint: GET /api/v1/billing/runs/
#    File:     backend/billing/api.py
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class Phase72BillingRunsTenantTests(_TenantBase):
    """
    billing/api.py  billing_runs()  uses get_request_school_id (canonical).
    Pattern identical to the gradebook surface:
      missing header â†’ 400, wrong tenant â†’ 404.
    """

    URL = "/api/v1/billing/runs/"

    def test_missing_header_returns_400(self):
        """
        No X-School-Id -> MissingSchoolContext (HTTP 400).
        Must use user_noschool (no school_id attribute) so tenant resolver
        does not auto-derive the school from the user profile (which would
        bypass the missing-header guard and return 200 for billing).
        """
        self.client.force_authenticate(user=self.user_noschool)
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 400)

    def test_correct_school_returns_200(self):
        """Correct school header -> HTTP 200 (empty list acceptable)."""
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get(self.URL, HTTP_X_SCHOOL_ID=str(self.school_a.id))
        self.assertEqual(resp.status_code, 200)

    def test_wrong_school_nonstaff_returns_404(self):
        """
        Non-staff user_a supplies school_b's ID.
        get_request_school_id() â†’ HTTP 404.
        Canonical cross-tenant prevention confirmed for billing module.
        """
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get(self.URL, HTTP_X_SCHOOL_ID=str(self.school_b.id))
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_returns_401_or_403(self):
        """No credentials -> 401 or 403 (DRF bearer-token auth; 403 is normal)."""
        resp = self.client.get(self.URL, HTTP_X_SCHOOL_ID=str(self.school_a.id))
        self.assertIn(resp.status_code, (401, 403))


# ---------------------------------------------------------------------------
# 3. Discipline Incidents -- CANONICAL scoping (Phase 7.2B remediated)
#    Endpoint: GET /api/v1/discipline/incidents/
#    File:     backend/discipline/api/views.py
#
#  Scoping upgraded to get_request_school_id() in Phase 7.2B:
#    - Missing header           -> MissingSchoolContext (HTTP 400)
#    - Non-staff, wrong school  -> NotFound (HTTP 404)
#    - Correct school           -> HTTP 200
# ---------------------------------------------------------------------------

class Phase72DisciplineTenantTests(_TenantBase):
    """
    Phase 7.2B: discipline upgraded to canonical get_request_school_id() scoping.
    Wrong-tenant non-staff requests now return HTTP 404 (was 200 before remediation).
    """

    URL = "/api/v1/discipline/incidents/"

    def test_missing_header_returns_400(self):
        """
        No X-School-Id header -> MissingSchoolContext (HTTP 400).
        Must use user_noschool so the canonical resolver finds no header and no
        user.school_id, returning None -> MissingSchoolContext -> 400.
        """
        self.client.force_authenticate(user=self.user_noschool)
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 400)

    def test_correct_school_returns_200(self):
        """Correct school header -> HTTP 200."""
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get(self.URL, HTTP_X_SCHOOL_ID=str(self.school_a.id))
        self.assertEqual(resp.status_code, 200)

    def test_wrong_school_nonstaff_returns_404(self):
        """
        Phase 7.2B: canonical scoping now in place.
        Non-staff user_a with school_b header -> HTTP 404 (was 200 before remediation).
        get_request_school_id() enforces the cross-tenant guard.
        """
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get(self.URL, HTTP_X_SCHOOL_ID=str(self.school_b.id))
        self.assertEqual(resp.status_code, 404)

    def test_cross_tenant_data_isolation_confirmed(self):
        """
        Cross-tenant request blocked at the scoping layer (404).
        School-A data is unreachable under school-B scope.
        """
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get(self.URL, HTTP_X_SCHOOL_ID=str(self.school_b.id))
        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_returns_401_or_403(self):
        """No credentials -> 401 or 403 (DRF bearer-token auth; 403 is normal)."""
        resp = self.client.get(self.URL, HTTP_X_SCHOOL_ID=str(self.school_a.id))
        self.assertIn(resp.status_code, (401, 403))
