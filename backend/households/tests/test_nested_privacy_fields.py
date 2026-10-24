"""Nested household data must obey the same grants and fields as direct reads."""
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from households.models import Guardian, Household, Student


@override_settings(TENANT_HEADER_REQUIRED=True, HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED=False)
class NestedHouseholdPrivacyTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Synthetic Nested Privacy School")
        self.home = Household.objects.create(
            school_id=self.school.pk, name="Synthetic Nested Household",
        )
        self.parent = UserAccount.objects.create_user(
            username="synthetic-nested-parent", email="nested-parent@example.invalid",
            school=self.school,
        )
        UserRole.objects.create(
            user=self.parent, school=self.school, role_code="PARENT",
        )
        self.guardian = Guardian.objects.create(
            school_id=self.school.pk, household=self.home, account=self.parent,
            first_name="Synthetic", last_name="Guardian",
            email="nested-parent@example.invalid", phone="555-0101",
        )
        self.child = Student.objects.create(
            school_id=self.school.pk, household=self.home,
            first_name="Synthetic", last_name="Child", grade_level="4",
        )

    def client_for(self, user):
        client = APIClient()
        client.force_login(user)
        client.credentials(HTTP_X_SCHOOL_ID=str(self.school.pk))
        return client

    def test_parent_embedded_fields_match_direct_domain_fields(self):
        client = self.client_for(self.parent)
        for prefix in ("/api/", "/api/v1/"):
            with self.subTest(prefix=prefix):
                response = client.get(f"{prefix}households/{self.home.pk}/")
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertNotIn("created_at", body)
                self.assertNotIn("updated_at", body)
                guardian_response = client.get(f"{prefix}guardians/{self.guardian.pk}/")
                student_response = client.get(f"{prefix}students/{self.child.pk}/")
                self.assertEqual(guardian_response.status_code, 200)
                self.assertEqual(student_response.status_code, 200)
                self.assertEqual(body["guardians"], [guardian_response.json()])
                self.assertEqual(body["students"], [student_response.json()])
                self.assertNotIn("created_at", body["guardians"][0])
                self.assertNotIn("updated_at", body["guardians"][0])
                self.assertNotIn("household", body["students"][0])
                self.assertNotIn("created_at", body["students"][0])

    def test_household_grant_does_not_inherit_guardian_contact_grant(self):
        staff = UserAccount.objects.create_user(
            username="synthetic-nested-registrar", email="nested-staff@example.invalid",
            school=self.school, is_staff=True,
        )
        UserRole.objects.create(
            user=staff, school=self.school, role_code="REGISTRAR",
        )
        # Explicit isolated policy: household directory only.
        RolePermission.objects.filter(
            role_code="REGISTRAR", permission__code="guardians.view",
        ).delete()
        household_permission, _ = CrownPermission.objects.get_or_create(code="households.view")
        RolePermission.objects.get_or_create(
            role_code="REGISTRAR", permission=household_permission,
        )
        client = self.client_for(staff)
        for prefix in ("/api/", "/api/v1/"):
            with self.subTest(prefix=prefix):
                response = client.get(f"{prefix}households/{self.home.pk}/")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["id"], str(self.home.pk))
                self.assertNotIn("guardians", response.json())
                self.assertNotIn("nested-parent@example.invalid", response.content.decode())
                self.assertEqual(client.get(f"{prefix}guardians/").json(), [])
                self.assertEqual(
                    client.get(f"{prefix}guardians/{self.guardian.pk}/").status_code, 404,
                )

        guardian_permission, _ = CrownPermission.objects.get_or_create(code="guardians.view")
        RolePermission.objects.get_or_create(
            role_code="REGISTRAR", permission=guardian_permission,
        )
        # A separately granted contact read still works through both surfaces.
        for prefix in ("/api/", "/api/v1/"):
            with self.subTest(prefix=prefix, grant="guardians.view"):
                response = client.get(f"{prefix}households/{self.home.pk}/")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.json()["guardians"]), 1)
                self.assertEqual(
                    client.get(f"{prefix}guardians/{self.guardian.pk}/").status_code, 200,
                )
