import uuid
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from financial_aid.models import FinancialAidApplication, AidAward, AidBucket

class FinancialAidEndpointsTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="test@crown-demo.local", password="pass1234")
        self.client.force_authenticate(user=self.user)

        self.school_id = uuid.uuid4()
        self.household_id = uuid.uuid4()

        app = FinancialAidApplication.objects.create(
            school_id=self.school_id,
            household_id=self.household_id,
            academic_year="2026-2027",
            household_income="65000.00",
            household_size=4,
            status="submitted",
        )

        AidAward.objects.create(
            school_id=self.school_id,
            application=app,
            bucket=AidBucket.NEED,
            amount="5000.00",
            rationale="Need-based award",
        )

    def test_summary_requires_school_header(self):
        r = self.client.get("/api/v1/financial-aid/summary/")
        self.assertEqual(r.status_code, 400)

    def test_summary_happy_path(self):
        r = self.client.get(
            "/api/v1/financial-aid/summary/?year=2026-2027",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["total_applications"], 1)

    def test_drilldown_bucket_filter(self):
        r = self.client.get(
            "/api/v1/financial-aid/drilldown/?year=2026-2027&bucket=need",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.data["count"], 1)
