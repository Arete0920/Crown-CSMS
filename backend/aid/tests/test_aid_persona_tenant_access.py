"""Fail-closed tenant and role regression for legacy financial-aid director reads."""
from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from core.models import AcademicYear, CrownPermission, RolePermission, School, UserAccount, UserRole


class AidPersonaTenantTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Synthetic Aid School One")
        self.other = School.objects.create(name="Synthetic Aid School Two")
        self.year = AcademicYear.objects.create(
            school=self.school, name="2026-2027",
            start_date=date(2026, 8, 1), end_date=date(2027, 5, 31),
        )
        self.user = UserAccount.objects.create_user(
            username="synthetic-aid-director", password="test-only", school=self.school,
        )
        UserRole.objects.create(user=self.user, school=self.school, role_code="AID_DIRECTOR")
        permission, _ = CrownPermission.objects.get_or_create(code="financial_aid.view")
        RolePermission.objects.get_or_create(role_code="AID_DIRECTOR", permission=permission)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def request(self, endpoint, *, school=None, requested_school=None):
        return self.client.get(
            f"/api/aid/{endpoint}/",
            {"school_id": str(requested_school or self.school.id), "year_id": str(self.year.id)},
            HTTP_X_SCHOOL_ID=str(school or self.school.id),
        )

    def test_three_director_reads_permit_authorized_school(self):
        for endpoint, expected in (("priority-queue", "rows"), ("metrics", "metrics"), ("timeline", "events")):
            with self.subTest(endpoint=endpoint):
                response = self.request(endpoint)
                self.assertEqual(response.status_code, 200)
                self.assertIn(expected, response.json())

    def test_mismatched_query_school_never_selects_foreign_tenant(self):
        for endpoint in ("priority-queue", "metrics", "timeline"):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.request(endpoint, requested_school=self.other.id).status_code, 404)

    def test_same_school_ungranted_role_is_denied(self):
        self.user.roles.all().delete()
        UserRole.objects.create(user=self.user, school=self.school, role_code="PARENT")
        for endpoint in ("priority-queue", "metrics", "timeline"):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.request(endpoint).status_code, 403)

    def test_anonymous_is_denied(self):
        self.client.force_authenticate(user=None)
        for endpoint in ("priority-queue", "metrics", "timeline"):
            with self.subTest(endpoint=endpoint):
                self.assertIn(self.request(endpoint).status_code, (401, 403))
