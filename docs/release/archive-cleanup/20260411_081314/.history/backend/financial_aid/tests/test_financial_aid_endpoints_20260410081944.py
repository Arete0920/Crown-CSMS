import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from core.models import CrownPermission, RolePermission, School, UserRole
from financial_aid.models import FinancialAidApplication, AidAward, AidBucket

class FinancialAidEndpointsTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="test@crown-demo.local", password="pass1234")

        # Grant financial_aid.view so these contract tests reach the business logic.
        # Permission gate tests live in test_financial_aid_authz.py.
        self.school = School.objects.create(name="FA Endpoints Test School")
        UserRole.objects.create(user=self.user, school=self.school, role_code="AID_DIRECTOR")
        _perm, _ = CrownPermission.objects.get_or_create(
            code="financial_aid.view", defaults={"description": "View financial aid"}
        )
        RolePermission.objects.get_or_create(role_code="AID_DIRECTOR", permission=_perm)
        _edit_perm, _ = CrownPermission.objects.get_or_create(
            code="financial_aid.edit", defaults={"description": "Edit financial aid"}
        )
        RolePermission.objects.get_or_create(role_code="AID_DIRECTOR", permission=_edit_perm)

        self.client.force_authenticate(user=self.user)

        # Use the real school's ID so the middleware can validate it.
        self.school_id = self.school.id
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
        self.assertEqual(r.data["applications"]["total"], 1)
        self.assertEqual(r.data["awards"]["total"], 1)
        self.assertEqual(r.data["discernment_framework"]["title"], "Crown Discernment + Biblical Principles")

    def test_summary_contract_keys(self):
        """Verify frozen contract structure (applications + awards top-level)."""
        r = self.client.get(
            "/api/v1/financial-aid/summary/?academic_year=2026-2027",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)
        
        # Top-level keys (frozen contract)
        self.assertIn("academic_year", r.data)
        self.assertIn("applications", r.data)
        self.assertIn("awards", r.data)
        
        # Applications keys
        apps = r.data["applications"]
        self.assertIn("total", apps)
        self.assertIn("by_status", apps)
        self.assertIn("draft", apps["by_status"])
        self.assertIn("submitted", apps["by_status"])
        self.assertIn("in_review", apps["by_status"])
        self.assertIn("decided", apps["by_status"])
        
        # Awards keys
        awards = r.data["awards"]
        self.assertIn("total", awards)
        self.assertIn("total_amount", awards)
        self.assertIn("avg_amount", awards)
        self.assertIn("by_bucket", awards)
        
        # All bucket keys present
        buckets = awards["by_bucket"]
        for key, _label in AidBucket.choices:
            self.assertIn(key, buckets)
            self.assertIn("total", buckets[key])
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
        self.assertEqual(r.data["applications"]["total"], 1)
        self.assertEqual(r.data["applications"]["by_status"]["draft"], 1)

    def test_summary_decimals_serialize_as_strings(self):
        """Verify amounts serialize as strings."""
        r = self.client.get(
            "/api/v1/financial-aid/summary/?academic_year=2026-2027",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)
        
        # Check amounts are strings
        self.assertIsInstance(r.data["awards"]["total_amount"], str)
        self.assertIsInstance(r.data["awards"]["avg_amount"], str)
        for bucket, data in r.data["awards"]["by_bucket"].items():
            self.assertIsInstance(data["amount"], str)

    def test_drilldown_bucket_filter(self):
        r = self.client.get(
            "/api/v1/financial-aid/drilldown/?academic_year=2026-2027&bucket=need",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.data["total"], 1)
        self.assertIn("limit", r.data)
        self.assertIn("offset", r.data)

    def test_drilldown_pagination_contract(self):
        """Verify pagination works correctly with limit and offset."""
        # Create additional awards (we already have 1 from setUp)
        app = FinancialAidApplication.objects.filter(school_id=self.school_id).first()
        for i in range(3):
            AidAward.objects.create(
                school_id=self.school_id,
                application=app,
                bucket=AidBucket.NEED,
                amount="1000.00",
                rationale=f"Additional award {i}",
            )
        
        # First page: limit=2, offset=0
        r1 = self.client.get(
            "/api/v1/financial-aid/drilldown/?academic_year=2026-2027&bucket=need&limit=2&offset=0",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(len(r1.data["rows"]), 2)
        self.assertGreaterEqual(r1.data["total"], 4)
        self.assertEqual(r1.data["limit"], 2)
        self.assertEqual(r1.data["offset"], 0)
        
        # Second page: limit=2, offset=2
        r2 = self.client.get(
            "/api/v1/financial-aid/drilldown/?academic_year=2026-2027&bucket=need&limit=2&offset=2",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r2.status_code, 200)
        self.assertGreaterEqual(len(r2.data["rows"]), 1)
        self.assertEqual(r2.data["total"], r1.data["total"])  # Same total
        self.assertEqual(r2.data["limit"], 2)
        self.assertEqual(r2.data["offset"], 2)

    def test_drilldown_invalid_bucket_400(self):
        """Verify invalid bucket returns 400 error."""
        r = self.client.get(
            "/api/v1/financial-aid/drilldown/?academic_year=2026-2027&bucket=bogus",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("detail", r.data)

    def test_drilldown_contract_keys(self):
        """Verify all required response keys match frozen contract."""
        r = self.client.get(
            "/api/v1/financial-aid/drilldown/?academic_year=2026-2027&bucket=need",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)
        required_keys = {"academic_year", "bucket", "total", "limit", "offset", "rows"}
        self.assertTrue(required_keys.issubset(set(r.data.keys())))
        self.assertIsInstance(r.data["rows"], list)
        self.assertIsInstance(r.data["total"], int)
        self.assertIsInstance(r.data["limit"], int)
        self.assertIsInstance(r.data["offset"], int)
        
        # Check row schema if present
        if r.data["rows"]:
            row = r.data["rows"][0]
            row_keys = {"award_id", "application_id", "household_id", "bucket", "amount", "application_status", "award_status", "rationale", "updated_at"}
            self.assertTrue(row_keys.issubset(set(row.keys())))
            self.assertNotIn("status", row)
            
            # Validate enum values (prevent silent regressions)
            self.assertIn(row["application_status"], {"draft", "submitted", "in_review", "decided"})
            self.assertIn(row["award_status"], {"awarded", "denied", "revised", "withdrawn"})

    def test_drilldown_empty_results_valid_shape(self):
        """Verify empty results still return valid contract."""
        r = self.client.get(
            "/api/v1/financial-aid/drilldown/?academic_year=2026-2027&bucket=hardship",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["total"], 0)
        self.assertEqual(r.data["rows"], [])
        self.assertIsNotNone(r.data["academic_year"])
        self.assertEqual(r.data["bucket"], "hardship")

    def test_drilldown_requires_school_header(self):
        """Verify X-School-Id header is required."""
        r = self.client.get("/api/v1/financial-aid/drilldown/?bucket=need")
        self.assertEqual(r.status_code, 400)

    def test_process_endpoint_advances_submitted_application(self):
        app = FinancialAidApplication.objects.filter(school_id=self.school_id).first()

        r = self.client.post(
            f"/api/financial-aid/applications/{app.id}/process/",
            {},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        payload = r.json()

        self.assertEqual(r.status_code, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["review_status"], "in_review")
        self.assertIn("need_index", payload["data"])
        self.assertIn("solomon_article_slug", payload["data"])
        self.assertIn("review_guidance", payload["data"])
        self.assertIn("biblical_principles", payload["data"]["review_guidance"])

