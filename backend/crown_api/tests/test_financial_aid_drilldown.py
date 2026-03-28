from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import CrownPermission, RolePermission, School, UserRole

class FinancialAidDrilldownTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            is_staff=True,
        )
        # Grant financial_aid.view so the permission gate doesn't block contract tests.
        self.school = School.objects.create(name="FA Drilldown Test School")
        UserRole.objects.create(user=self.user, school=self.school, role_code="AID_DIRECTOR")
        _perm, _ = CrownPermission.objects.get_or_create(
            code="financial_aid.view", defaults={"description": "View financial aid"}
        )
        RolePermission.objects.get_or_create(role_code="AID_DIRECTOR", permission=_perm)

    def test_missing_school_header_400(self):
        self.client.force_login(self.user)
        resp = self.client.get("/api/financial-aid/drilldown/")
        self.assertEqual(resp.status_code, 400)

    def test_happy_path_200(self):
        self.client.force_login(self.user)
        resp = self.client.get("/api/financial-aid/drilldown/", HTTP_X_SCHOOL_ID=str(self.school.id))
        # If no data yet, 200 should still return a stable shape
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("academic_year", data)
        self.assertIn("total", data)
        self.assertIn("limit", data)
        self.assertIn("offset", data)
        self.assertIn("rows", data)