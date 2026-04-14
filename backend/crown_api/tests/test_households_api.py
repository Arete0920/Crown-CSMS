from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School, UserAccount, UserRole
from households.models import Guardian, Household, Student


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

class HouseholdsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create school for multi-tenant scoping
        self.school = School.objects.create(name="Test School")
        self.other_school = School.objects.create(name="Other School")

        # Staff user with school context
        self.staff_user = UserAccount.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password=TEST_AUTH_SECRET,
            is_staff=True,
            school=self.school,
        )

        # Non-staff user with school context — guardian-scoped (PARENT role required)
        self.nonstaff_user = UserAccount.objects.create_user(
            username="normaluser",
            email="normal@example.com",
            password=TEST_AUTH_SECRET,
            is_staff=False,
            school=self.school,
        )
        UserRole.objects.create(user=self.nonstaff_user, school=self.school, role_code="PARENT")

        # Households in test school
        self.household = Household.objects.create(
            name="The Test Family",
            school_id=self.school.id,
        )
        self.other_household = Household.objects.create(
            name="Other Family",
            school_id=self.school.id,
        )

        # Household in different school (cross-school test)
        self.cross_school_household = Household.objects.create(
            name="Cross School Family",
            school_id=self.other_school.id,
        )

        # Guardians for the test household
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

        # Guardian for other_household matching nonstaff_user email
        self.normal_guardian = Guardian.objects.create(
            school_id=self.school.id,
            household=self.other_household,
            first_name="Normal",
            last_name="User",
            email="normal@example.com",
            is_primary=True,
        )

        # Student in test household
        self.student = Student.objects.create(
            school_id=self.school.id,
            household=self.household,
            first_name="S1",
            last_name="Test",
            grade_level="3",
            is_active=True,
        )

    def test_model_creation(self):
        self.assertEqual(Household.objects.count(), 3)
        self.assertEqual(Guardian.objects.count(), 3)
        self.assertEqual(Student.objects.count(), 1)

    def test_list_households_staff_200(self):
        """Staff users see all households in their school."""
        self.client.force_authenticate(user=self.staff_user)
        resp = self.client.get("/api/households/")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)
        names = {row["name"] for row in resp.json()}
        self.assertIn("The Test Family", names)
        self.assertIn("Other Family", names)
        # Should NOT see cross-school household
        self.assertNotIn("Cross School Family", names)
        self.assertEqual(len(resp.json()), 2)

    def test_detail_household_staff_200(self):
        """Staff can access household detail."""
        self.client.force_authenticate(user=self.staff_user)
        resp = self.client.get(f"/api/households/{self.household.id}/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["id"], str(self.household.id))
        self.assertEqual(body["name"], "The Test Family")

    def test_list_households_nonstaff_scoped(self):
        """Non-staff users only see households where guardian email matches."""
        self.client.force_authenticate(user=self.nonstaff_user)
        resp = self.client.get("/api/households/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIsInstance(body, list)
        # nonstaff_user email is normal@example.com, matches normal_guardian in other_household
        self.assertEqual({row["id"] for row in body}, {str(self.other_household.id)})
        self.assertEqual(len(body), 1)

    def test_detail_household_nonstaff_out_of_scope_404(self):
        """Non-staff must not learn existence of out-of-scope households."""
        self.client.force_authenticate(user=self.nonstaff_user)

        # In-scope detail (normal@example.com matches guardian in other_household)
        ok = self.client.get(f"/api/households/{self.other_household.id}/")
        self.assertEqual(ok.status_code, 200)

        # Out-of-scope detail should be 404 (no existence leak)
        no = self.client.get(f"/api/households/{self.household.id}/")
        self.assertEqual(no.status_code, 404)

    def test_unknown_email_nonstaff_empty_list_and_404_detail(self):
        """Non-staff PARENT with no matching guardian sees nothing."""
        unknown = UserAccount.objects.create_user(
            username="unknown",
            email="unknown@example.com",
            password=TEST_AUTH_SECRET,
            is_staff=False,
            school=self.school,
        )
        # Must be PARENT role for guardian scoping to apply
        UserRole.objects.create(user=unknown, school=self.school, role_code="PARENT")
        self.client.force_authenticate(user=unknown)
        resp = self.client.get("/api/households/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

        resp2 = self.client.get(f"/api/households/{self.household.id}/")
        self.assertEqual(resp2.status_code, 404)

    def test_unauthenticated_401(self):
        """Unauthenticated requests return 401 (JWT auth configured — DRF emits 401 not 403)."""
        resp = self.client.get("/api/households/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(resp.status_code, 401)
        resp2 = self.client.get(f"/api/households/{self.household.id}/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(resp2.status_code, 401)

    def test_cross_school_isolation(self):
        """Users cannot access households from other schools."""
        self.client.force_authenticate(user=self.staff_user)
        
        # Staff can see households in their school
        resp = self.client.get("/api/households/")
        ids = {row["id"] for row in resp.json()}
        self.assertNotIn(str(self.cross_school_household.id), ids)
        
        # Staff cannot access cross-school household detail
        resp = self.client.get(f"/api/households/{self.cross_school_household.id}/")
        self.assertEqual(resp.status_code, 404)

    def test_nonstaff_blank_email_sees_nothing(self):
        """PARENT with blank email cannot see any households (no guardian match)."""
        blank_user = UserAccount.objects.create_user(
            username="blank_email",
            email="",
            password=TEST_AUTH_SECRET,
            is_staff=False,
            school=self.school,
        )
        # Must be PARENT role; blank email → qs.none() in guardian scoping
        UserRole.objects.create(user=blank_user, school=self.school, role_code="PARENT")
        self.client.force_authenticate(user=blank_user)
        resp = self.client.get("/api/households/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])


