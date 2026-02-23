import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from applications.models import Application, Applicant, ApplicationEvent
from core.models import AcademicYear, CrownPermission, RolePermission, School, UserRole
from households.models import Household


class AdmissionsEndpointsTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="test@crown-demo.local", password="pass1234")

        # Grant admissions.view so these contract tests reach the business logic.
        # Permission gate tests live in test_admissions_authz.py (Layer C).
        _perm, _ = CrownPermission.objects.get_or_create(
            code="admissions.view", defaults={"description": "View admissions"}
        )
        RolePermission.objects.get_or_create(role_code="REGISTRAR", permission=_perm)

        self.client.force_authenticate(user=self.user)

        # Create school
        self.school = School.objects.create(name="Test School")
        self.school_id = self.school.id
        UserRole.objects.create(user=self.user, school=self.school, role_code="REGISTRAR")

        # Create a test household (required for Application)
        self.household = Household.objects.create(
            school_id=self.school_id,
            name="Test Household"
        )

        # Create academic year
        self.ay = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date="2020-08-01",
            end_date="2030-05-31",
            is_current=True,
        )

        # Create test applications with a range of statuses
        self.app_draft = Application.objects.create(
            school_id=self.school_id,
            household=self.household,
            status="DRAFT",
        )

        self.app_submitted = Application.objects.create(
            school_id=self.school_id,
            household=self.household,
            status="SUBMITTED",
            submitted_at=datetime.now(tz=timezone.utc) - timedelta(days=5),
        )

        self.app_in_review = Application.objects.create(
            school_id=self.school_id,
            household=self.household,
            status="IN_REVIEW",
        )

        # Create applicants (leads)
        self.applicant_1 = Applicant.objects.create(
            school_id=self.school_id,
            application=self.app_draft,
            first_name="John",
            last_name="Doe",
            grade_applying_for="5",
            source="facebook",
            flags={"duplicate_suspected": False, "bot_suspected": False},
        )

        self.applicant_2 = Applicant.objects.create(
            school_id=self.school_id,
            application=self.app_submitted,
            first_name="Jane",
            last_name="Smith",
            grade_applying_for="8",
            source="church_referral",
            flags={"duplicate_suspected": False, "bot_suspected": False},
        )

        self.applicant_3 = Applicant.objects.create(
            school_id=self.school_id,
            application=self.app_in_review,
            first_name="Bob",
            last_name="Johnson",
            grade_applying_for="6",
            source="google",
            flags={"duplicate_suspected": False, "bot_suspected": False},
        )

    def test_summary_requires_school_header(self):
        """Missing X-School-Id should return 400."""
        r = self.client.get("/api/v1/admissions/summary/")
        self.assertEqual(r.status_code, 400)
        self.assertIn("X-School-Id", r.json()["detail"])

    def test_summary_happy_path(self):
        """Summary returns 200 with correct structure."""
        r = self.client.get(
            "/api/v1/admissions/summary/",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["academic_year"], "2026-2027")
        self.assertIn("pipeline", r.data)
        self.assertIn("conversion", r.data)
        self.assertIn("velocity_days", r.data)
        self.assertIn("top_sources", r.data)

    def test_summary_contract_keys(self):
        """Verify frozen contract structure (pipeline, conversion, velocity, sources)."""
        r = self.client.get(
            "/api/v1/admissions/summary/",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)

        # Top-level keys (frozen contract)
        self.assertIn("academic_year", r.data)
        self.assertIn("date_from", r.data)
        self.assertIn("date_to", r.data)
        self.assertIn("pipeline", r.data)
        self.assertIn("conversion", r.data)
        self.assertIn("velocity_days", r.data)
        self.assertIn("top_sources", r.data)

        # Pipeline keys
        pipeline = r.data["pipeline"]
        self.assertIn("total", pipeline)
        self.assertIn("by_stage", pipeline)

        # All stage keys present
        stages = pipeline["by_stage"]
        for stage in [
            "inquiry",
            "tour_scheduled",
            "tour_completed",
            "application_started",
            "application_submitted",
            "in_review",
            "accepted",
            "waitlisted",
            "declined",
            "enrolled",
        ]:
            self.assertIn(stage, stages)
            self.assertIsInstance(stages[stage], int)

        # Conversion rates are decimal strings
        conversion = r.data["conversion"]
        for key, val in conversion.items():
            self.assertIsInstance(val, str)
            # Should be 2 decimals
            parts = val.split(".")
            self.assertEqual(len(parts), 2)
            self.assertEqual(len(parts[1]), 2)

    def test_summary_empty_results(self):
        """Empty results still return valid contract shape."""
        # Create a different school with no applications
        other_school = School.objects.create(name="Other School")
        r = self.client.get(
            "/api/v1/admissions/summary/",
            HTTP_X_SCHOOL_ID=str(other_school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["pipeline"]["total"], 0)
        # All stage counts are zero
        for count in r.data["pipeline"]["by_stage"].values():
            self.assertEqual(count, 0)

    def test_drilldown_requires_school_header(self):
        """Missing X-School-Id should return 400."""
        r = self.client.get("/api/v1/admissions/drilldown/?stage=inquiry")
        self.assertEqual(r.status_code, 400)

    def test_drilldown_happy_path(self):
        """Drilldown returns 200 with correct structure."""
        r = self.client.get(
            "/api/v1/admissions/drilldown/",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["academic_year"], "2026-2027")
        self.assertIn("stage", r.data)
        self.assertIn("source", r.data)
        self.assertIn("total", r.data)
        self.assertIn("limit", r.data)
        self.assertIn("offset", r.data)
        self.assertIn("rows", r.data)

    def test_drilldown_contract_keys(self):
        """Verify all required response keys match frozen contract."""
        r = self.client.get(
            "/api/v1/admissions/drilldown/",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 200)
        required_keys = {"academic_year", "stage", "source", "total", "limit", "offset", "rows"}
        self.assertTrue(required_keys.issubset(set(r.data.keys())))
        self.assertIsInstance(r.data["rows"], list)
        self.assertIsInstance(r.data["total"], int)
        self.assertIsInstance(r.data["limit"], int)
        self.assertIsInstance(r.data["offset"], int)

        # Check row schema if present
        if r.data["rows"]:
            row = r.data["rows"][0]
            row_keys = {
                "lead_id",
                "application_id",
                "student_id",
                "stage",
                "source",
                "grade_applying_for",
                "created_at",
                "updated_at",
                "flags",
            }
            self.assertTrue(row_keys.issubset(set(row.keys())))
            self.assertIsInstance(row["flags"], dict)
            self.assertIn("duplicate_suspected", row["flags"])
            self.assertIn("bot_suspected", row["flags"])

    def test_drilldown_invalid_stage_400(self):
        """Invalid stage returns 400."""
        r = self.client.get(
            "/api/v1/admissions/drilldown/?stage=INVALID",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("stage", r.json()["detail"].lower())

    def test_drilldown_pagination_contract(self):
        """Verify pagination works correctly with limit and offset."""
        # Create additional applications
        for i in range(5):
            app = Application.objects.create(
                school_id=self.school_id,
                household=self.household,
                status="SUBMITTED",
            )
            Applicant.objects.create(
                school_id=self.school_id,
                application=app,
                first_name=f"User{i}",
                last_name="Test",
                grade_applying_for="5",
                source="other",
                            flags={"duplicate_suspected": False, "bot_suspected": False},
            )

        # First page: limit=2, offset=0
        r1 = self.client.get(
            "/api/v1/admissions/drilldown/?limit=2&offset=0",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(len(r1.data["rows"]), min(2, r1.data["total"]))
        self.assertGreaterEqual(r1.data["total"], 3)
        self.assertEqual(r1.data["limit"], 2)
        self.assertEqual(r1.data["offset"], 0)

        # Second page: limit=2, offset=2
        r2 = self.client.get(
            "/api/v1/admissions/drilldown/?limit=2&offset=2",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r2.status_code, 200)
        self.assertGreaterEqual(len(r2.data["rows"]), 0)
        self.assertEqual(r2.data["total"], r1.data["total"])
        self.assertEqual(r2.data["limit"], 2)
        self.assertEqual(r2.data["offset"], 2)

    def test_drilldown_empty_results_valid_shape(self):
        """Empty results still return valid contract."""
        # Create a different school
        other_school = School.objects.create(name="Other School 2")
        r = self.client.get(
            "/api/v1/admissions/drilldown/",
            HTTP_X_SCHOOL_ID=str(other_school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["total"], 0)
        self.assertEqual(r.data["rows"], [])
        self.assertIsNotNone(r.data["academic_year"])

    def test_drilldown_missing_auth(self):
        """Missing auth returns 403."""
        self.client.force_authenticate(user=None)
        r = self.client.get(
            "/api/v1/admissions/drilldown/",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 403)
