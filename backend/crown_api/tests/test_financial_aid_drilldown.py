from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

class FinancialAidDrilldownTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create a test user
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            is_staff=True,
        )

    def test_missing_school_header_400(self):
        self.client.force_login(self.user)
        resp = self.client.get("/api/financial-aid/drilldown/")
        self.assertEqual(resp.status_code, 400)

    def test_happy_path_200(self):
        self.client.force_login(self.user)
        resp = self.client.get("/api/financial-aid/drilldown/", HTTP_X_SCHOOL_ID="852e31bc-d953-48c5-b081-98d27469d634")
        # If no data yet, 200 should still return a stable shape
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("ok"))
        self.assertIn("items", data)
        self.assertIn("summary", data)
        self.assertIn("facets", data)