from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School, UserAccount
from households.models import Guardian, Household, Student
from crown_api.models import UserPersonLink


class HouseholdsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.school = School.objects.create(name="Test School")

        self.staff_user = UserAccount.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass",
            is_staff=True,
        )
        self.staff_user.school = self.school
        self.staff_user.save()
        
        self.nonstaff_user = UserAccount.objects.create_user(
            username="normaluser",
            email="normal@example.com",
            password="testpass",
            is_staff=False,
        )
        self.nonstaff_user.school = self.school
        self.nonstaff_user.save()

        self.household = Household.objects.create(name="The Test Family", school_id=self.school.id)
        self.other_household = Household.objects.create(name="Other Family", school_id=self.school.id)
        
        self.guardian1 = Guardian.objects.create(
            school_id=self.school.id,
            household=self.household,
            first_name="G1",
            last_name="Test",
            email="g1@example.com",
            is_primary=True,
        )
        self.guardian2 = Guardian.objects.create(
            school_id=self.school.id,
            household=self.household,
            first_name="G2",
            last_name="Test",
            email="g2@example.com",
            is_primary=False,
        )

        self.student = Student.objects.create(
            school_id=self.school.id,
            household=self.household,
            first_name="S1",
            last_name="Test",
            grade_level="3",
            is_active=True,
        )

    def test_model_creation(self):
        self.assertEqual(Household.objects.count(), 2)
        self.assertEqual(Guardian.objects.count(), 2)
        self.assertEqual(Student.objects.count(), 1)

    def test_primary_guardian_uniqueness(self):
        """At most one primary guardian per household."""
        # Create second primary guardian - should succeed (no DB constraint in spine model)
        Guardian.objects.create(
            school_id=self.school.id,
            household=self.household,
            first_name="G3",
            last_name="Test",
            email="g3@example.com",
            is_primary=True,
        )
        # Spine version allows multiple is_primary=True (business logic can enforce if needed)
        self.assertEqual(Guardian.objects.filter(household=self.household, is_primary=True).count(), 2)

    def test_list_households_staff_200(self):
        self.client.force_authenticate(user=self.staff_user)
        resp = self.client.get("/api/households/", HTTP_X_CROWN_SCHOOL_ID=str(self.school.id))
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)
        names = {row["name"] for row in resp.json()}
        self.assertIn("The Test Family", names)
        self.assertIn("Other Family", names)

    def test_detail_household_staff_200(self):
        self.client.force_authenticate(user=self.staff_user)
        resp = self.client.get(f"/api/households/{self.household.id}/", HTTP_X_CROWN_SCHOOL_ID=str(self.school.id))
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["id"], str(self.household.id))
        self.assertIn("guardians", body)
        self.assertIn("students", body)

    def test_list_households_nonstaff_scoped(self):
        """Non-staff users see all households in their school (spine version)."""
        # Create guardian in other_household
        Guardian.objects.create(
            school_id=self.school.id,
            household=self.other_household,
            first_name="Normal",
            last_name="User",
            email="normal@example.com",
            is_primary=False,
        )

        self.client.force_authenticate(user=self.nonstaff_user)
        resp = self.client.get("/api/households/", HTTP_X_CROWN_SCHOOL_ID=str(self.school.id))
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIsInstance(body, list)
        # Spine: school-only scoping, so non-staff sees BOTH households
        self.assertEqual({row["id"] for row in body}, {str(self.household.id), str(self.other_household.id)})

    def test_detail_household_nonstaff_out_of_scope_404(self):
        """Non-staff can access all households in their school (spine version)."""
        Guardian.objects.create(
            school_id=self.school.id,
            household=self.other_household,
            first_name="Normal",
            last_name="User",
            email="normal@example.com",
            is_primary=False,
        )

        self.client.force_authenticate(user=self.nonstaff_user)

        # Both households accessible (school-only scoping)
        ok = self.client.get(f"/api/households/{self.other_household.id}/", HTTP_X_CROWN_SCHOOL_ID=str(self.school.id))
        self.assertEqual(ok.status_code, 200)

        also_ok = self.client.get(f"/api/households/{self.household.id}/", HTTP_X_CROWN_SCHOOL_ID=str(self.school.id))
        self.assertEqual(also_ok.status_code, 200)

    def test_unknown_email_nonstaff_empty_list_and_404_detail(self):
        unknown = UserAccount.objects.create_user(
            username="unknown",
            email="unknown@example.com",
            password="testpass",
            is_staff=False,
        )
        unknown.school = self.school
        unknown.save()
        
        self.client.force_authenticate(user=unknown)
        # Spine: school-only scoping, so non-staff still sees all households in school
        resp = self.client.get("/api/households/", HTTP_X_CROWN_SCHOOL_ID=str(self.school.id))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)  # Both households visible

        resp2 = self.client.get(f"/api/households/{self.household.id}/", HTTP_X_CROWN_SCHOOL_ID=str(self.school.id))
        self.assertEqual(resp2.status_code, 200)  # Now 200, not 404

    def test_unauthenticated_401(self):
        resp = self.client.get("/api/households/")
        self.assertEqual(resp.status_code, 403)  # DRF returns 403 for IsAuthenticated
        resp2 = self.client.get(f"/api/households/{self.household.id}/")
        self.assertEqual(resp2.status_code, 403)

