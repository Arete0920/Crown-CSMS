import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import Resolver404, resolve
from rest_framework.test import APITestCase

from applications.models import (
    Application,
    Applicant,
    ApplicationChecklistDocument,
    ApplicationChecklistItem,
    ApplicationEvent,
    ChecklistItemStatus,
)
from core.models import AcademicYear, CrownPermission, RolePermission, School, UserRole
from finance.models import FinanceInvoice, FinanceObligation
from households.models import Household


class AdmissionsEndpointsTests(APITestCase):
    @staticmethod
    def _payload(response):
        try:
            return response.json()
        except Exception:
            return {}

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create(username="test@crown-demo.local")
        self.user.set_password("pass1234")
        self.user.save(update_fields=["password"])

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

    def _submit_payload(self):
        return {
            "inquiry": {
                "campus": "Test School",
                "startTerm": "2026-2027",
                "heardAbout": "Church referral",
            },
            "family": {
                "guardians": [
                    {
                        "relationship": "Mother",
                        "relationshipOther": "",
                        "guardianName": "Maria Parent",
                        "email": "maria.parent@example.com",
                        "phone": "555-0101",
                        "isPrimary": True,
                    }
                ],
                "churchAffiliation": "Attend regularly",
                "churchAffiliationOther": "",
            },
            "students": [
                {
                    "firstName": "Ava",
                    "lastName": "Parent",
                    "gradeApplyingFor": "5",
                    "currentSchool": "Public school",
                    "currentSchoolOther": "",
                    "strengths": "Reading",
                    "supportNeeds": "",
                }
            ],
            "mission": {
                "covenantPartnership": True,
                "discipleshipCommitment": True,
                "serviceMindset": True,
                "comments": "Aligned with mission.",
            },
            "documents": {
                "transcriptReady": True,
                "recommendationsReady": True,
                "pastorReferenceReady": False,
                "immunizationReady": True,
            },
            "attestations": {
                "informationAccurate": True,
                "missionPartnershipUnderstood": True,
                "communicationOptIn": True,
            },
            "applicationFee": {
                "policyAccepted": True,
                "waiverRequested": False,
            },
        }

    def test_summary_uses_single_role_school_fallback(self):
        """The authenticated user's sole school role supplies tenant context."""
        r = self.client.get("/api/v1/admissions/summary/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["academic_year"], "2026-2027")
        self.assertIn("pipeline", r.data)

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
        # User must have a role at other_school now that permission is scoped.
        UserRole.objects.create(user=self.user, school=other_school, role_code="REGISTRAR")
        r = self.client.get(
            "/api/v1/admissions/summary/",
            HTTP_X_SCHOOL_ID=str(other_school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["pipeline"]["total"], 0)
        # All stage counts are zero
        for count in r.data["pipeline"]["by_stage"].values():
            self.assertEqual(count, 0)

    def test_drilldown_uses_single_role_school_fallback(self):
        """The authenticated user's sole school role supplies tenant context."""
        r = self.client.get("/api/v1/admissions/drilldown/?stage=inquiry")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["academic_year"], "2026-2027")
        self.assertIn("rows", r.data)

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
        # User must have a role at other_school now that permission is scoped.
        UserRole.objects.create(user=self.user, school=other_school, role_code="REGISTRAR")
        r = self.client.get(
            "/api/v1/admissions/drilldown/",
            HTTP_X_SCHOOL_ID=str(other_school.id),
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["total"], 0)
        self.assertEqual(r.data["rows"], [])
        self.assertIsNotNone(r.data["academic_year"])

    def test_drilldown_missing_auth(self):
        """Missing auth returns 401 (JWT configured — DRF emits 401 not 403)."""
        self.client.force_authenticate(user=None)
        r = self.client.get(
            "/api/v1/admissions/drilldown/",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )
        self.assertEqual(r.status_code, 401)

    def test_submit_public_happy_path_creates_records(self):
        """Public submit persists application/applicant/event records."""
        self.client.force_authenticate(user=None)
        before_apps = Application.objects.filter(school_id=self.school_id).count()
        before_applicants = Applicant.objects.filter(school_id=self.school_id).count()
        before_events = ApplicationEvent.objects.filter(school_id=self.school_id).count()
        before_fee_obligations = FinanceObligation.objects.filter(school_id=self.school_id).count()
        before_fee_invoices = FinanceInvoice.objects.filter(school_id=self.school_id).count()

        r = self.client.post("/api/v1/admissions/submit/", self._submit_payload(), format="json")

        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data.get("ok"))
        self.assertEqual(r.data.get("stage"), "application_submitted")
        self.assertEqual(r.data.get("application_count"), 1)
        self.assertIn("status_center", r.data)
        self.assertIn("documents_lifecycle", r.data)
        self.assertIn("enrollment_continuity", r.data)
        self.assertIn("reviewer_summary", r.data)
        self.assertIn("family_affordability_profile", r.data)
        self.assertIn("application_fee", r.data)
        self.assertIn("application_fee_status_card", r.data)
        self.assertIn("admissions_to_finance_handoff", r.data)
        self.assertIsInstance(r.data["status_center"].get("milestones"), list)
        self.assertIsInstance(r.data["documents_lifecycle"], list)
        self.assertIsInstance(r.data["enrollment_continuity"].get("checklist"), list)
        self.assertIn(r.data["application_fee"].get("status"), ["pending", "waiver_requested", "not_required"])
        self.assertEqual(r.data["application_fee"].get("finance", {}).get("state"), "invoiced")
        self.assertEqual(r.data["application_fee"].get("payment_handoff", {}).get("state"), "ready")
        self.assertEqual(r.data["application_fee"].get("payment_handoff", {}).get("requires_auth"), True)
        self.assertEqual(r.data["application_fee_status_card"].get("finance_state"), "invoiced")
        self.assertEqual(r.data["application_fee_status_card"].get("requires_action"), True)
        self.assertEqual(r.data["family_affordability_profile"].get("currency"), "USD")
        self.assertIn("upfront", r.data["family_affordability_profile"])
        self.assertIn("total_estimated", r.data["family_affordability_profile"].get("upfront", {}))
        self.assertIn("fee_readiness", r.data["admissions_to_finance_handoff"])
        self.assertIn("aid_readiness", r.data["admissions_to_finance_handoff"])
        self.assertIn("deposit_readiness", r.data["admissions_to_finance_handoff"])
        self.assertEqual(
            r.data["admissions_to_finance_handoff"].get("fee_readiness", {}).get("finance_state"),
            "invoiced",
        )

        self.assertEqual(
            Application.objects.filter(school_id=self.school_id).count(),
            before_apps + 1,
        )
        self.assertEqual(
            Applicant.objects.filter(school_id=self.school_id).count(),
            before_applicants + 1,
        )
        self.assertEqual(
            ApplicationEvent.objects.filter(school_id=self.school_id).count(),
            before_events + 3,
        )
        self.assertEqual(
            FinanceObligation.objects.filter(school_id=self.school_id).count(),
            before_fee_obligations + 1,
        )
        self.assertEqual(
            FinanceInvoice.objects.filter(school_id=self.school_id).count(),
            before_fee_invoices + 1,
        )

    def test_submit_requires_campus_when_no_tenant_header(self):
        """Public submit must include inquiry.campus when no tenant header is provided."""
        self.client.force_authenticate(user=None)
        payload = self._submit_payload()
        payload["inquiry"]["campus"] = ""

        r = self.client.post("/api/v1/admissions/submit/", payload, format="json")

        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data.get("code"), "missing_tenant")

    def test_submit_requires_fee_policy_or_waiver(self):
        """When fee is enabled, submit requires fee policy acceptance or waiver request."""
        self.client.force_authenticate(user=None)
        payload = self._submit_payload()
        payload["applicationFee"] = {
            "policyAccepted": False,
            "waiverRequested": False,
        }

        r = self.client.post("/api/v1/admissions/submit/", payload, format="json")

        self.assertEqual(r.status_code, 400)
        self.assertIn("applicationFee", r.data.get("detail", ""))

    def test_submit_rejects_fee_policy_and_waiver_both_true(self):
        """Submit should reject conflicting fee flags when both policy and waiver are true."""
        self.client.force_authenticate(user=None)
        payload = self._submit_payload()
        payload["applicationFee"] = {
            "policyAccepted": True,
            "waiverRequested": True,
        }

        r = self.client.post("/api/v1/admissions/submit/", payload, format="json")

        self.assertEqual(r.status_code, 400)
        self.assertIn("cannot both be true", r.data.get("detail", ""))

    def test_submit_waiver_request_skips_finance_invoice(self):
        """Waiver requested should not create finance obligation/invoice records."""
        self.client.force_authenticate(user=None)
        payload = self._submit_payload()
        payload["applicationFee"] = {
            "policyAccepted": False,
            "waiverRequested": True,
        }
        before_fee_obligations = FinanceObligation.objects.filter(school_id=self.school_id).count()
        before_fee_invoices = FinanceInvoice.objects.filter(school_id=self.school_id).count()

        r = self.client.post("/api/v1/admissions/submit/", payload, format="json")

        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["application_fee"].get("finance", {}).get("state"), "waiver_requested")
        self.assertEqual(
            FinanceObligation.objects.filter(school_id=self.school_id).count(),
            before_fee_obligations,
        )
        self.assertEqual(
            FinanceInvoice.objects.filter(school_id=self.school_id).count(),
            before_fee_invoices,
        )

    def test_submit_idempotency_replay_does_not_create_duplicates(self):
        """Same Idempotency-Key should replay the original result and avoid duplicate records."""
        self.client.force_authenticate(user=None)
        key = "admissions-submit-fixed-key"

        before_apps = Application.objects.filter(school_id=self.school_id).count()
        before_applicants = Applicant.objects.filter(school_id=self.school_id).count()

        first = self.client.post(
            "/api/v1/admissions/submit/",
            self._submit_payload(),
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
            HTTP_X_REQUEST_ID="req-submit-1",
        )
        second = self.client.post(
            "/api/v1/admissions/submit/",
            self._submit_payload(),
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
            HTTP_X_REQUEST_ID="req-submit-2",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second["X-Idempotent-Replay"], "true")
        self.assertEqual(first.data.get("application_id"), second.data.get("application_id"))
        self.assertIn("status_center", second.data)

        self.assertEqual(
            Application.objects.filter(school_id=self.school_id).count(),
            before_apps + 1,
        )
        self.assertEqual(
            Applicant.objects.filter(school_id=self.school_id).count(),
            before_applicants + 1,
        )

    def test_submit_validation_error_includes_correlation(self):
        """Validation errors should include a correlation id in both header and body."""
        self.client.force_authenticate(user=None)
        payload = self._submit_payload()
        payload["students"][0]["gradeApplyingFor"] = ""

        r = self.client.post(
            "/api/v1/admissions/submit/",
            payload,
            format="json",
            HTTP_X_REQUEST_ID="corr-test-123",
        )

        self.assertEqual(r.status_code, 400)
        self.assertEqual(r["X-Correlation-Id"], "corr-test-123")
        self.assertEqual(r.data.get("correlation_id"), "corr-test-123")
        self.assertIsInstance(r.data.get("message"), str)

    def test_submit_rate_limit_returns_429(self):
        """Abuse controls should return 429 once email bucket exceeds threshold."""
        self.client.force_authenticate(user=None)
        cache.set(
            f"admissions_submit_rl:email:{self.school_id}:maria.parent@example.com",
            6,
            timeout=60 * 60,
        )

        r = self.client.post("/api/v1/admissions/submit/", self._submit_payload(), format="json")

        self.assertEqual(r.status_code, 429)
        self.assertEqual(r.data.get("code"), "rate_limited")
        self.assertIn("Retry-After", r)

    def test_submit_crm_import_failure_is_non_blocking(self):
        """Admissions submit must succeed and persist records when CRM module import fails."""
        self.client.force_authenticate(user=None)
        before_apps = Application.objects.filter(school_id=self.school_id).count()
        before_applicants = Applicant.objects.filter(school_id=self.school_id).count()
        before_events = ApplicationEvent.objects.filter(school_id=self.school_id).count()
        sentinel = "CRM_FALLBACK_SENTINEL"
        real_import = __import__

        def _failing_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "crm_marketing.services" or (name == "crm_marketing" and fromlist and "services" in fromlist):
                raise ModuleNotFoundError(sentinel)
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=_failing_import), patch(
            "applications.views_admissions.logger.exception"
        ) as log_exception:
            r = self.client.post("/api/v1/admissions/submit/", self._submit_payload(), format="json")

        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data.get("ok"))
        self.assertEqual(r.data.get("stage"), "application_submitted")
        self.assertEqual(Application.objects.filter(school_id=self.school_id).count(), before_apps + 1)
        self.assertEqual(Applicant.objects.filter(school_id=self.school_id).count(), before_applicants + 1)
        self.assertEqual(ApplicationEvent.objects.filter(school_id=self.school_id).count(), before_events + 3)
        self.assertTrue(log_exception.called)
        self.assertEqual(log_exception.call_args.args[0], "crm_marketing_register_submit_failed")
        self.assertNotIn(sentinel, str(r.data))
        self.assertNotIn(sentinel, r.content.decode("utf-8", errors="ignore"))

    def test_public_config_returns_fee_source_of_truth(self):
        """Public config endpoint should expose backend fee configuration."""
        self.client.force_authenticate(user=None)

        r = self.client.get(
            "/api/v1/admissions/public-config/",
            HTTP_X_SCHOOL_ID=str(self.school_id),
        )

        self.assertEqual(r.status_code, 200)
        self.assertIn("application_fee", r.data)
        self.assertIn("required", r.data["application_fee"])
        self.assertIn("amount", r.data["application_fee"])
        self.assertEqual(r.data["application_fee"].get("currency"), "USD")

    def test_submit_returns_enrollment_continuity_checklist(self):
        """
        Admissions checklist is not a standalone endpoint.

        CROWN owns the admissions-to-enrollment continuity process, and the
        checklist is returned as part of the public admissions submit contract:
        POST /api/v1/admissions/submit/
        """
        self.client.force_authenticate(user=None)

        response = self.client.post(
            "/api/v1/admissions/submit/",
            self._submit_payload(),
            format="json",
            HTTP_IDEMPOTENCY_KEY="admissions-checklist-contract-test",
            HTTP_X_REQUEST_ID="req-admissions-checklist-contract",
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(response.data.get("ok"))

        self.assertIn("enrollment_continuity", response.data)
        continuity = response.data["enrollment_continuity"]

        self.assertEqual(continuity.get("phase"), "admissions_to_enrollment")
        self.assertIn("checklist", continuity)
        self.assertIsInstance(continuity["checklist"], list)

        checklist_keys = {item.get("key") for item in continuity["checklist"]}

        self.assertIn("application_fee", checklist_keys)
        self.assertIn("tour_or_interview", checklist_keys)
        self.assertIn("record_completion", checklist_keys)
        self.assertIn("family_partnership_conversation", checklist_keys)
        self.assertIn("decision_and_enrollment_next_steps", checklist_keys)

    def test_public_config_allows_missing_tenant_header(self):
        """Public config must be reachable without X-School-Id for public funnel bootstrap."""
        self.client.force_authenticate(user=None)

        r = self.client.get("/api/v1/admissions/public-config/")

        self.assertEqual(r.status_code, 200)
        self.assertIn("application_fee", r.data)

class AdmissionsRouteContractTests(APITestCase):
    def test_admissions_checklist_route_is_not_exposed(self):
        """
        Guard against phantom admissions checklist endpoints.

        Checklist state belongs inside the CROWN admissions submit response,
        not under a standalone /api/v1/admissions/checklist/ route.
        """
        with self.assertRaises(Resolver404):
            resolve("/api/v1/admissions/checklist/")

        with self.assertRaises(Resolver404):
            resolve("/api/v1/admissions/checklist/items/")
