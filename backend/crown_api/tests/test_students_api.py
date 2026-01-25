from django.test import TestCase
from rest_framework.test import APIClient

from core.models import UserAccount
from crown_api.models import (
    Household,
    HouseholdMember,
    Person,
    Student,
    StudentProfile,
    UserPersonLink,
)
from crown_api.models_households import ROLE_GUARDIAN


class StudentsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.staff_user = UserAccount.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass",
            is_staff=True,
        )

        self.parent_user = UserAccount.objects.create_user(
            username="parentuser",
            email="parent@example.com",
            password="testpass",
            is_staff=False,
        )

        self.household_a = Household.objects.create(household_name="Household A")
        self.household_b = Household.objects.create(household_name="Household B")

        self.parent_person = Person.objects.create(
            first_name="Parent",
            last_name="A",
            email="parent@example.com",
        )
        UserPersonLink.objects.create(user=self.parent_user, person=self.parent_person)
        HouseholdMember.objects.create(
            household=self.household_a,
            person=self.parent_person,
            role=ROLE_GUARDIAN,
            is_primary=False,
        )

        self.student_a_person = Person.objects.create(
            first_name="Student",
            last_name="A",
            email="student.a@example.com",
        )
        self.student_b_person = Person.objects.create(
            first_name="Student",
            last_name="B",
            email="student.b@example.com",
        )

        self.student_a = Student.objects.create(
            person=self.student_a_person,
            household=self.household_a,
            grade_level="3",
            active=True,
        )
        self.student_b = Student.objects.create(
            person=self.student_b_person,
            household=self.household_b,
            grade_level="5",
            active=True,
        )

        StudentProfile.objects.create(
            student=self.student_a,
            student_number="HCA-9001",
            expected_grad_year=2035,
        )

    def test_list_students_staff_sees_all(self):
        self.client.force_authenticate(user=self.staff_user)
        resp = self.client.get("/api/students/")
        self.assertEqual(resp.status_code, 200)
        ids = {row["student_id"] for row in resp.json()}
        self.assertEqual(ids, {str(self.student_a.id), str(self.student_b.id)})

    def test_list_students_parent_scoped_to_household(self):
        self.client.force_authenticate(user=self.parent_user)
        resp = self.client.get("/api/students/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual({row["student_id"] for row in body}, {str(self.student_a.id)})

        # Profile fields should be returned when present
        self.assertEqual(body[0]["profile"]["student_number"], "HCA-9001")

    def test_student_detail_parent_out_of_scope_404(self):
        self.client.force_authenticate(user=self.parent_user)
        ok = self.client.get(f"/api/students/{self.student_a.id}/")
        self.assertEqual(ok.status_code, 200)

        no = self.client.get(f"/api/students/{self.student_b.id}/")
        self.assertEqual(no.status_code, 404)

    def test_students_unauth_401(self):
        resp = self.client.get("/api/students/")
        self.assertEqual(resp.status_code, 401)
        resp2 = self.client.get(f"/api/students/{self.student_a.id}/")
        self.assertEqual(resp2.status_code, 401)
