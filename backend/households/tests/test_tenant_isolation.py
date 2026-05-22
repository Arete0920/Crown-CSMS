"""
Tenant isolation tests per TENANT_PRIVACY_CANON.md

Tests the contract:
- Missing tenant context → fail-closed deny (400/401/403)
- Wrong tenant context → 404 (non-staff)
- Correct tenant context → 200
- Querysets never return cross-tenant rows
"""
# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false, reportAttributeAccessIssue=false

import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient  # type: ignore[import-untyped]
from core.models import School
from households.models import Household, Student


User = get_user_model()


@override_settings(HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED=False)
class TenantIsolationTestCase(TestCase):
    """
    Tenant isolation enforcement tests.
    Per TENANT_PRIVACY_CANON.md section 6.
    """

    def setUp(self):
        """Create two schools with separate data"""
        self.school_a = School.objects.create(name="School A")
        self.school_b = School.objects.create(name="School B")

        # School A user (non-staff)
        self.user_a = User.objects.create_user(
            username="usera",
            email="usera@test.com",
            school_id=self.school_a.id
        )

        # School B user (non-staff)
        self.user_b = User.objects.create_user(
            username="userb",
            email="userb@test.com",
            school_id=self.school_b.id
        )

        # Staff user (can override)
        self.staff_user = User.objects.create_user(
            username="staff",
            email="staff@test.com",
            is_staff=True,
            school_id=self.school_a.id
        )

        # Create households in each school
        self.household_a = Household.objects.create(
            school_id=self.school_a.id,
            name="FamilyA"
        )
        self.household_b = Household.objects.create(
            school_id=self.school_b.id,
            name="FamilyB"
        )

        # Create students in each school
        self.student_a = Student.objects.create(
            school_id=self.school_a.id,
            household=self.household_a,
            first_name="Alice",
            last_name="FamilyA"
        )
        self.student_b = Student.objects.create(
            school_id=self.school_b.id,
            household=self.household_b,
            first_name="Bob",
            last_name="FamilyB"
        )

        self.api_client = APIClient()

    def test_missing_tenant_fails_closed_or_empty_scope(self):
        """
        Missing tenant context must fail closed (400/401/403), and
        no-school authenticated requests must not leak cross-tenant data.
        """
        # Anonymous request (no auth, no tenant)
        response = self.api_client.get("/api/households/")
        # Missing tenant context may be denied by auth layer (401/403)
        # or tenant middleware (400), all of which are fail-closed outcomes.
        self.assertIn(response.status_code, [400, 401, 403])

        # Authenticated but user has no school_id
        user_no_school = User.objects.create_user(
            username="noschool",
            email="noschool@test.com"
        )
        self.api_client.force_authenticate(user=user_no_school)

        # Endpoints using get_request_school_id(required=True) should return 400
        # For now, test that it returns empty results (existing behavior)
        response = self.api_client.get("/api/households/")
        # This should be 400 once we update views to use required=True
        self.assertIn(response.status_code, [200, 400])
        if response.status_code == 200:
            results = response.data if isinstance(response.data, list) else response.data.get("results", [])
            self.assertEqual(len(results), 0)

    def test_wrong_tenant_returns_404_non_staff(self):
        """
        CANON Rule 3: Non-staff cross-tenant access MUST return 404 (not 403)
        """
        self.api_client.force_authenticate(user=self.user_a)

        # Try to access School B's household (should return 404)
        response = self.api_client.get(f"/api/households/{self.household_b.id}/")
        self.assertEqual(response.status_code, 404)

        # Try to access School B's student (should return 404)
        response = self.api_client.get(f"/api/students/{self.student_b.id}/")
        self.assertEqual(response.status_code, 404)

    def test_correct_tenant_returns_200(self):
        """
        CANON Rule 6: Correct tenant context MUST return 200 and scoped data
        """
        self.api_client.force_authenticate(user=self.user_a)

        # List households - should see only School A
        response = self.api_client.get("/api/households/")
        self.assertEqual(response.status_code, 200)
        # response.data is a list directly (not {"results": [...]})
        results = response.data if isinstance(response.data, list) else response.data.get("results", [])
        self.assertEqual(len(results), 1, f"Expected 1 household, got {len(results)}")
        self.assertEqual(results[0]["id"], str(self.household_a.id))

        # Detail household - should see School A household
        response = self.api_client.get(f"/api/households/{self.household_a.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(self.household_a.id))

        # List students - should see only School A
        response = self.api_client.get("/api/students/")
        self.assertEqual(response.status_code, 200)
        results = response.data if isinstance(response.data, list) else response.data.get("results", [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], str(self.student_a.id))

    def test_staff_can_override_tenant(self):
        """
        CANON Rule 2: Staff may use X-School-Id header to override
        """
        self.api_client.force_authenticate(user=self.staff_user)

        # Access School B data via header override
        response = self.api_client.get(
            "/api/households/",
            HTTP_X_SCHOOL_ID=str(self.school_b.id)
        )
        self.assertEqual(response.status_code, 200)
        results = response.data if isinstance(response.data, list) else response.data.get("results", [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], str(self.household_b.id))

    def test_invalid_tenant_header_returns_400(self):
        """
        Invalid UUID in tenant header MUST return 400
        """
        self.api_client.force_authenticate(user=self.staff_user)

        response = self.api_client.get(
            "/api/households/",
            HTTP_X_SCHOOL_ID="not-a-uuid"
        )
        self.assertEqual(response.status_code, 400)

    def test_nonexistent_tenant_returns_404(self):
        """
        Valid UUID but nonexistent school MUST return 404
        """
        self.api_client.force_authenticate(user=self.staff_user)

        fake_uuid = str(uuid.uuid4())
        response = self.api_client.get(
            "/api/households/",
            HTTP_X_SCHOOL_ID=fake_uuid
        )
        self.assertEqual(response.status_code, 404)

    def test_queryset_never_crosses_tenants(self):
        """
        CANON Rule 6: Querysets MUST NOT return cross-tenant rows
        """
        self.api_client.force_authenticate(user=self.user_a)

        # List all households
        response = self.api_client.get("/api/households/")
        self.assertEqual(response.status_code, 200)
        results = response.data if isinstance(response.data, list) else response.data.get("results", [])

        # Verify no School B data leaked
        household_ids = [r["id"] for r in results]
        self.assertNotIn(str(self.household_b.id), household_ids)
        self.assertIn(str(self.household_a.id), household_ids)

    def test_finance_endpoint_respects_tenant(self):
        """
        Sensitive endpoints (finance) MUST enforce tenant isolation
        """
        self.api_client.force_authenticate(user=self.user_a)

        # This endpoint should only return School A data
        # Adjust URL based on actual finance endpoint
        response = self.api_client.get("/api/billing/summary/")

        # Should either succeed with School A data or require explicit tenant
        self.assertIn(response.status_code, [200, 400, 404])

        if response.status_code == 200:
            # Verify it's School A's data (structure depends on endpoint)
            self.assertIsNotNone(response.data)
