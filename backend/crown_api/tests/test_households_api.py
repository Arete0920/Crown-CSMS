from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import UserAccount
from crown_api.models import Household, HouseholdMember, Person, Student
from crown_api.models_households import ROLE_GUARDIAN, ROLE_PRIMARY_GUARDIAN


class HouseholdsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.staff_user = UserAccount.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass",
            is_staff=True,
        )
        self.nonstaff_user = UserAccount.objects.create_user(
            username="normaluser",
            email="normal@example.com",
            password="testpass",
            is_staff=False,
        )

        self.household = Household.objects.create(household_name="The Test Family")
        self.guardian1 = Person.objects.create(
            first_name="G1", last_name="Test", email="g1@example.com"
        )
        self.guardian2 = Person.objects.create(
            first_name="G2", last_name="Test", email="g2@example.com"
        )

        HouseholdMember.objects.create(
            household=self.household,
            person=self.guardian1,
            role=ROLE_PRIMARY_GUARDIAN,
            is_primary=True,
        )
        HouseholdMember.objects.create(
            household=self.household,
            person=self.guardian2,
            role=ROLE_GUARDIAN,
            is_primary=False,
        )

        student_person = Person.objects.create(
            first_name="S1", last_name="Test", email="s1@student.example.com"
        )
        Student.objects.create(
            person=student_person,
            household=self.household,
            grade_level="3",
            active=True,
        )

    def test_model_creation(self):
        self.assertEqual(Household.objects.count(), 1)
        self.assertEqual(Person.objects.count(), 3)
        self.assertEqual(HouseholdMember.objects.count(), 2)
        self.assertEqual(Student.objects.count(), 1)

    def test_primary_guardian_uniqueness(self):
        """At most one primary guardian per household."""
        with self.assertRaises(IntegrityError):
            HouseholdMember.objects.create(
                household=self.household,
                person=self.guardian2,
                role=ROLE_GUARDIAN,
                is_primary=True,
            )

    def test_list_households_staff_200(self):
        self.client.force_authenticate(user=self.staff_user)
        resp = self.client.get("/api/households/")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)
        self.assertEqual(resp.json()[0]["household_name"], "The Test Family")

    def test_detail_household_staff_200(self):
        self.client.force_authenticate(user=self.staff_user)
        resp = self.client.get(f"/api/households/{self.household.id}/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["id"], str(self.household.id))
        self.assertIn("members", body)
        self.assertIn("students", body)

    def test_nonstaff_forbidden(self):
        self.client.force_authenticate(user=self.nonstaff_user)
        resp = self.client.get("/api/households/")
        self.assertEqual(resp.status_code, 403)
