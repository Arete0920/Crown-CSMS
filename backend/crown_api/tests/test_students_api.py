from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School, UserAccount, UserRole
from households.models import Guardian, Household, Student


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

class StudentsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create school for multi-tenant scoping
        self.school = School.objects.create(name="Test School")

        self.staff_user = UserAccount.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password=TEST_AUTH_SECRET,
            is_staff=True,
            school=self.school,
        )

        self.parent_user = UserAccount.objects.create_user(
            username="parentuser",
            email="parent@example.com",
            password=TEST_AUTH_SECRET,
            is_staff=False,
            school=self.school,
        )
        # PARENT role required for guardian scoping to apply
        UserRole.objects.create(user=self.parent_user, school=self.school, role_code="PARENT")

        # Households in test school
        self.household_a = Household.objects.create(
            name="Household A",
            school_id=self.school.id,
        )
        self.household_b = Household.objects.create(
            name="Household B",
            school_id=self.school.id,
        )

        # Guardian for household_a matching parent_user email
        self.parent_guardian = Guardian.objects.create(
            school_id=self.school.id,
            household=self.household_a,
            first_name="Parent",
            last_name="A",
            email="parent@example.com",
            is_primary=True,
        )

        # Students
        self.student_a = Student.objects.create(
            school_id=self.school.id,
            household=self.household_a,
            first_name="Student",
            last_name="A",
            grade_level="3",
            is_active=True,
        )
        self.student_b = Student.objects.create(
            school_id=self.school.id,
            household=self.household_b,
            first_name="Student",
            last_name="B",
            grade_level="5",
            is_active=True,
        )

    def test_list_students_staff_sees_all(self):
        """Staff users see all students in their school."""
        self.client.force_authenticate(user=self.staff_user)
        resp = self.client.get("/api/students/")
        self.assertEqual(resp.status_code, 200)
        ids = {row["id"] for row in resp.json()}
        self.assertEqual(ids, {str(self.student_a.id), str(self.student_b.id)})

    def test_list_students_parent_scoped_to_household(self):
        """Non-staff users only see students in guardian-linked households."""
        self.client.force_authenticate(user=self.parent_user)
        resp = self.client.get("/api/students/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual({row["id"] for row in body}, {str(self.student_a.id)})

    def test_student_detail_parent_out_of_scope_404(self):
        """Non-staff cannot access students outside their households."""
        self.client.force_authenticate(user=self.parent_user)
        ok = self.client.get(f"/api/students/{self.student_a.id}/")
        self.assertEqual(ok.status_code, 200)

        no = self.client.get(f"/api/students/{self.student_b.id}/")
        self.assertEqual(no.status_code, 404)

    def test_students_unauth_403(self):
        """Unauthenticated requests return 401 (JWT auth configured — DRF emits 401 not 403)."""
        resp = self.client.get("/api/students/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(resp.status_code, 401)
        resp2 = self.client.get(f"/api/students/{self.student_a.id}/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(resp2.status_code, 401)


