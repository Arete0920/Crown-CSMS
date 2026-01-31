import uuid
from decimal import Decimal
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
            "/api/v1/financial-aid/summary/?academic_year=2026-2027",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["academic_year"], "2026-2027")
        self.assertEqual(r.data["totals"]["applications_total"], 1)
        self.assertEqual(r.data["totals"]["awards_total_count"], 1)

    def test_summary_contract_keys(self):
        """Verify all required response keys are present."""
        r = self.client.get(
            "/api/v1/financial-aid/summary/?academic_year=2026-2027",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)
        
        # Top-level keys
        self.assertIn("academic_year", r.data)
        self.assertIn("totals", r.data)
        self.assertIn("awards_by_bucket", r.data)
        
        # Totals keys
        totals = r.data["totals"]
        self.assertIn("applications_total", totals)
        self.assertIn("applications_by_status", totals)
        self.assertIn("awards_total_count", totals)
        self.assertIn("awards_total_amount", totals)
        self.assertIn("avg_award_amount", totals)
        
        # All status keys present
        status = totals["applications_by_status"]
        self.assertIn("draft", status)
        self.assertIn("submitted", status)
        self.assertIn("in_review", status)
        self.assertIn("decided", status)
        
        # All bucket keys present
        buckets = r.data["awards_by_bucket"]
        for key, _label in AidBucket.choices:
            self.assertIn(key, buckets)
            self.assertIn("count", buckets[key])
            self.assertIn("amount", buckets[key])

    def test_summary_default_year_is_latest_present(self):
        """Verify academic_year parameter defaults to latest present."""
        # Create app in different year
        app2 = FinancialAidApplication.objects.create(
            school_id=self.school_id,
            household_id=self.household_id,
            academic_year="2027-2028",
            household_income="75000.00",
            household_size=4,
            status="draft",
        )
        
        # Call without academic_year param
        r = self.client.get(
            "/api/v1/financial-aid/summary/",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)
        # Should get latest year (2027-2028)
        self.assertEqual(r.data["academic_year"], "2027-2028")
        self.assertEqual(r.data["totals"]["applications_total"], 1)
        self.assertEqual(r.data["totals"]["applications_by_status"]["draft"], 1)

    def test_summary_decimals_serialize_as_strings(self):
        """Verify amounts serialize as strings."""
        r = self.client.get(
            "/api/v1/financial-aid/summary/?academic_year=2026-2027",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)
        
        # Check amounts are strings
        self.assertIsInstance(r.data["totals"]["awards_total_amount"], str)
        self.assertIsInstance(r.data["totals"]["avg_award_amount"], str)
        for bucket, data in r.data["awards_by_bucket"].items():
            self.assertIsInstance(data["amount"], str)

    def test_drilldown_bucket_filter(self):
        r = self.client.get(
            "/api/v1/financial-aid/drilldown/?academic_year=2026-2027&bucket=need",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.data["count"], 1)
