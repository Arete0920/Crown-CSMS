from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import UserAccount
from crown_api.models import Household, HouseholdMember, Person, Student, UserPersonLink
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
        self.other_household = Household.objects.create(household_name="Other Family")
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
        self.assertEqual(Household.objects.count(), 2)
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
        names = {row["household_name"] for row in resp.json()}
        self.assertIn("The Test Family", names)
        self.assertIn("Other Family", names)

    def test_detail_household_staff_200(self):
        self.client.force_authenticate(user=self.staff_user)
        resp = self.client.get(f"/api/households/{self.household.id}/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["id"], str(self.household.id))
        self.assertIn("members", body)
        self.assertIn("students", body)

    def test_list_households_nonstaff_scoped(self):
        """Non-staff users only see households where their email maps to a Person in membership."""
        # Map nonstaff_user.email -> Person -> household membership
        normal_person = Person.objects.create(
            first_name="Normal", last_name="User", email="normal@example.com"
        )
        HouseholdMember.objects.create(
            household=self.other_household,
            person=normal_person,
            role=ROLE_GUARDIAN,
            is_primary=False,
        )

        self.client.force_authenticate(user=self.nonstaff_user)
        resp = self.client.get("/api/households/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIsInstance(body, list)
        self.assertEqual({row["id"] for row in body}, {str(self.other_household.id)})

    def test_detail_household_nonstaff_out_of_scope_404(self):
        """Non-staff must not learn existence of out-of-scope households."""
        normal_person = Person.objects.create(
            first_name="Normal", last_name="User", email="normal@example.com"
        )
        HouseholdMember.objects.create(
            household=self.other_household,
            person=normal_person,
            role=ROLE_GUARDIAN,
            is_primary=False,
        )

        self.client.force_authenticate(user=self.nonstaff_user)

        # In-scope detail
        ok = self.client.get(f"/api/households/{self.other_household.id}/")
        self.assertEqual(ok.status_code, 200)

        # Out-of-scope detail should be 404 (no existence leak)
        no = self.client.get(f"/api/households/{self.household.id}/")
        self.assertEqual(no.status_code, 404)

    def test_unknown_email_nonstaff_empty_list_and_404_detail(self):
        unknown = UserAccount.objects.create_user(
            username="unknown",
            email="unknown@example.com",
            password="testpass",
            is_staff=False,
        )
        self.client.force_authenticate(user=unknown)
        resp = self.client.get("/api/households/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

        resp2 = self.client.get(f"/api/households/{self.household.id}/")
        self.assertEqual(resp2.status_code, 404)

    def test_unauthenticated_401(self):
        resp = self.client.get("/api/households/")
        self.assertEqual(resp.status_code, 401)
        resp2 = self.client.get(f"/api/households/{self.household.id}/")
        self.assertEqual(resp2.status_code, 401)

    def test_linked_user_blank_email_scopes(self):
        # Create a new user with blank email, but linked to a Person.
        linked_user = UserAccount.objects.create_user(
            username="linked_blank_email",
            email="",
            password="testpass",
            is_staff=False,
        )

        linked_person = Person.objects.create(
            first_name="Linked",
            last_name="Person",
            email="linked@example.com",
        )
        UserPersonLink.objects.create(user=linked_user, person=linked_person)

        HouseholdMember.objects.create(
            household=self.other_household,
            person=linked_person,
            role=ROLE_GUARDIAN,
            is_primary=False,
        )

        self.client.force_authenticate(user=linked_user)
        resp = self.client.get("/api/households/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual({row["id"] for row in resp.json()}, {str(self.other_household.id)})

        # Out-of-scope detail should remain 404
        resp2 = self.client.get(f"/api/households/{self.household.id}/")
        self.assertEqual(resp2.status_code, 404)

    def test_link_overrides_email_match(self):
        # User email matches Person A...
        user = UserAccount.objects.create_user(
            username="override_user",
            email="match@example.com",
            password="testpass",
            is_staff=False,
        )

        person_a = Person.objects.create(
            first_name="Email",
            last_name="Match",
            email="match@example.com",
        )
        HouseholdMember.objects.create(
            household=self.household,
            person=person_a,
            role=ROLE_GUARDIAN,
            is_primary=False,
        )

        # ...but the explicit link points to Person B, so Person B must win.
        person_b = Person.objects.create(
            first_name="Linked",
            last_name="Wins",
            email="different@example.com",
        )
        HouseholdMember.objects.create(
            household=self.other_household,
            person=person_b,
            role=ROLE_GUARDIAN,
            is_primary=False,
        )
        UserPersonLink.objects.create(user=user, person=person_b)

        self.client.force_authenticate(user=user)
        resp = self.client.get("/api/households/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual({row["id"] for row in resp.json()}, {str(self.other_household.id)})

        out = self.client.get(f"/api/households/{self.household.id}/")
        self.assertEqual(out.status_code, 404)
