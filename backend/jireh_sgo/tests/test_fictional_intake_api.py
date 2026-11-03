"""End-to-end persistence, explicit authority and two-SGO isolation in local synthetic intake."""
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from jireh_sgo.models import (
    SGOApplication, SGOAuditEvent, SGOAward, SGOFamilyGrant, SGOFamilyIntake,
    SGOMembership, SGOOrganization, SGOProcessorAssignment, SGOProgram,
)


@override_settings(
    DEBUG=True, CROWN_ENV="local", DJANGO_ENV="local",
    CROWN_DEMO_MODE=False, CROWN_SGO_FICTIONAL_INTAKE_ENABLED=True,
    TENANT_HEADER_REQUIRED=True,
)
class FictionalSGOIntakeAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.family_a = User.objects.create_user(username="fictional-family-a", password="x")
        self.family_b = User.objects.create_user(username="fictional-family-b", password="x")
        self.processor_a = User.objects.create_user(username="fictional-processor-a", password="x")
        self.processor_b = User.objects.create_user(username="fictional-processor-b", password="x")
        self.partner_admin = User.objects.create_superuser(username="fictional-partner-admin", password="x")
        self.outsider = User.objects.create_superuser(username="fictional-outsider", password="x")
        self.org_a = SGOOrganization.objects.create(
            legal_name="Fictional A", state_of_domicile="DE", active=True,
        )
        self.org_b = SGOOrganization.objects.create(
            legal_name="Fictional B", state_of_domicile="PA", active=True,
        )
        self.program_a = SGOProgram.objects.create(
            organization=self.org_a, name="Synthetic A", code="fictional-a", calendar_year=2027,
            funding_source="PRIVATE", eligibility_rule_version="POLICY_2027_V1",
        )
        self.program_b = SGOProgram.objects.create(
            organization=self.org_b, name="Synthetic B", code="fictional-b", calendar_year=2027,
            funding_source="PRIVATE", eligibility_rule_version="POLICY_2027_V1",
        )
        self.grant_a = SGOFamilyGrant.objects.create(
            program=self.program_a, user=self.family_a,
            student_key=uuid4(), school_key=uuid4(), consent_version="DEMO_CONSENT_V1", active=True,
        )
        self.grant_b = SGOFamilyGrant.objects.create(
            program=self.program_b, user=self.family_b,
            student_key=uuid4(), school_key=uuid4(), consent_version="DEMO_CONSENT_V1", active=True,
        )
        SGOProcessorAssignment.objects.create(
            program=self.program_a, user=self.processor_a, active=True,
        )
        SGOProcessorAssignment.objects.create(
            program=self.program_b, user=self.processor_b, active=True,
        )
        # Existing partner membership is intentionally NOT a family/processor grant.
        SGOMembership.objects.create(
            organization=self.org_a, user=self.partner_admin,
            role=SGOMembership.ADMIN, active=True,
        )

    def _data(self, program=None, key=None, grade="K"):
        return {
            "program_id": str((program or self.program_a).id),
            "grade_level": grade, "consent": True,
            "consent_version": "DEMO_CONSENT_V1",
            "submission_key": str(key or uuid4()),
        }

    def _submit_a(self, data=None):
        self.client.force_authenticate(user=self.family_a)
        return self.client.post(
            "/api/v1/jireh-sgo/family/submit/", data or self._data(), format="json",
        )

    def _correction_url(self, application_id):
        return f"/api/v1/jireh-sgo/family/applications/{application_id}/correct/"

    def _request_url(self, application_id):
        return f"/api/v1/jireh-sgo/processor/applications/{application_id}/request-correction/"

    def test_two_unrelated_sgos_and_explicit_authorization(self):
        self.client.force_authenticate(user=self.family_a)
        response = self.client.get("/api/v1/jireh-sgo/family/programs/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data["programs"]], [str(self.program_a.id)],
        )
        self.assertNotIn(str(self.grant_b.student_key), str(response.data))
        self.assertEqual(self.client.post(
            "/api/v1/jireh-sgo/family/submit/", self._data(program=self.program_b),
            format="json",
        ).status_code, 403)
        self.client.force_authenticate(user=self.partner_admin)
        self.assertEqual(self.client.get("/api/v1/jireh-sgo/family/programs/").data["programs"], [])
        self.assertEqual(self.client.post(
            "/api/v1/jireh-sgo/family/submit/", self._data(), format="json",
        ).status_code, 403)
        self.assertEqual(self.client.get(
            f"/api/v1/jireh-sgo/processor/programs/{self.program_a.id}/queue/",
        ).status_code, 403)
        self.client.force_authenticate(user=self.processor_b)
        self.assertEqual(self.client.get(
            f"/api/v1/jireh-sgo/processor/programs/{self.program_a.id}/queue/",
        ).status_code, 403)
        self.client.force_authenticate(user=self.outsider)
        self.assertEqual(self.client.post(
            "/api/v1/jireh-sgo/family/submit/", self._data(), format="json",
        ).status_code, 403)

    def test_durable_save_readback_and_idempotent_retry_across_sessions(self):
        payload = self._data()
        first = self._submit_a(payload)
        self.assertEqual(first.status_code, 201)
        app_id = first.data["application"]["id"]
        self.assertEqual(first.data["application"]["status"], "SUBMITTED")
        self.assertEqual(first.data["application"]["revision"], 1)
        self.assertEqual(first.data["application"]["consent_version"], "DEMO_CONSENT_V1")
        self.assertEqual(SGOApplication.objects.count(), 1)
        self.assertEqual(SGOFamilyIntake.objects.count(), 1)
        self.client.force_authenticate(user=None)
        self.assertIn(self.client.get(
            f"/api/v1/jireh-sgo/family/applications/{app_id}/",
        ).status_code, (401, 403))
        self.client.force_authenticate(user=self.family_a)
        again = self.client.post("/api/v1/jireh-sgo/family/submit/", payload, format="json")
        self.assertEqual(again.status_code, 200)
        self.assertFalse(again.data["created"])
        self.assertEqual(again.data["application"]["id"], app_id)
        readback = self.client.get(f"/api/v1/jireh-sgo/family/applications/{app_id}/")
        self.assertEqual(readback.status_code, 200)
        self.assertEqual(readback.data["application"]["grade_level"], "K")
        self.assertEqual(readback["Cache-Control"], "private, no-store")
        self.assertEqual(SGOApplication.objects.count(), 1)
        self.assertEqual(SGOAuditEvent.objects.filter(
            action=SGOAuditEvent.INTAKE_SUBMITTED,
        ).count(), 1)
        self.assertEqual(self.client.post(
            "/api/v1/jireh-sgo/family/submit/",
            {**payload, "grade_level": "1"}, format="json",
        ).status_code, 409)
        self.assertEqual(self.client.post(
            "/api/v1/jireh-sgo/family/submit/",
            {**payload, "submission_key": str(uuid4())}, format="json",
        ).status_code, 409)

    def test_correction_request_and_family_resubmission_are_audited_and_idempotent(self):
        created = self._submit_a(self._data())
        app_id = created.data["application"]["id"]
        request_key = str(uuid4())
        self.client.force_authenticate(user=self.processor_a)
        url = self._request_url(app_id)
        req = {"expected_revision": 1, "reason": "GRADE_UNVERIFIED", "request_key": request_key}
        first = self.client.post(url, req, format="json")
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.data["changed"])
        self.assertEqual(first.data["application"]["revision"], 2)
        self.assertEqual(first.data["application"]["status"], "CORRECTION_REQUESTED")
        again = self.client.post(url, req, format="json")
        self.assertEqual(again.status_code, 200)
        self.assertFalse(again.data["changed"])
        self.assertEqual(self.client.post(
            url, {**req, "request_key": str(uuid4())}, format="json",
        ).status_code, 409)
        self.client.force_authenticate(user=self.family_a)
        family_url = self._correction_url(app_id)
        correction = {"expected_revision": 2, "grade_level": "2", "correction_key": str(uuid4())}
        applied = self.client.post(family_url, correction, format="json")
        self.assertEqual(applied.status_code, 200)
        self.assertTrue(applied.data["changed"])
        self.assertEqual(applied.data["application"]["status"], "RESUBMITTED")
        self.assertEqual(applied.data["application"]["revision"], 3)
        self.assertEqual(applied.data["application"]["grade_level"], "2")
        duplicate = self.client.post(family_url, correction, format="json")
        self.assertEqual(duplicate.status_code, 200)
        self.assertFalse(duplicate.data["changed"])
        self.assertEqual(self.client.post(
            family_url, {**correction, "correction_key": str(uuid4())}, format="json",
        ).status_code, 409)
        application = SGOApplication.objects.get(pk=app_id)
        self.assertEqual(application.eligibility, SGOApplication.UNREVIEWED)
        self.assertFalse(SGOAward.objects.exists())
        self.assertEqual(SGOAuditEvent.objects.filter(
            action=SGOAuditEvent.INTAKE_CORRECTION_REQUESTED,
        ).count(), 1)
        self.assertEqual(SGOAuditEvent.objects.filter(
            action=SGOAuditEvent.INTAKE_RESUBMITTED,
        ).count(), 1)
        intake = SGOFamilyIntake.objects.get(application_id=app_id)
        self.assertEqual(intake.initial_grade_level, "K")

    def test_cross_sgo_case_and_queue_scopes(self):
        first = self._submit_a()
        app_a = first.data["application"]["id"]
        self.client.force_authenticate(user=self.family_b)
        second = self.client.post(
            "/api/v1/jireh-sgo/family/submit/", self._data(program=self.program_b),
            format="json",
        )
        self.assertEqual(second.status_code, 201)
        app_b = second.data["application"]["id"]
        self.assertEqual(self.client.get(
            f"/api/v1/jireh-sgo/family/applications/{app_a}/",
        ).status_code, 403)
        self.assertEqual(self.client.post(
            self._correction_url(app_a), {"expected_revision": 1, "grade_level": "1",
            "correction_key": str(uuid4())}, format="json",
        ).status_code, 403)
        self.client.force_authenticate(user=self.processor_a)
        queue = self.client.get(f"/api/v1/jireh-sgo/processor/programs/{self.program_a.id}/queue/")
        self.assertEqual(queue.status_code, 200)
        self.assertEqual([row["id"] for row in queue.data["applications"]], [app_a])
        self.assertNotIn(str(self.grant_b.student_key), str(queue.data))
        self.assertEqual(self.client.post(
            self._request_url(app_b), {"expected_revision": 1,
            "reason": "GRADE_UNVERIFIED", "request_key": str(uuid4())}, format="json",
        ).status_code, 403)

    def test_revocation_inactivity_and_session_change_fail_closed(self):
        created = self._submit_a()
        app_id = created.data["application"]["id"]
        self.client.force_authenticate(user=self.family_b)
        self.assertEqual(self.client.get(
            f"/api/v1/jireh-sgo/family/applications/{app_id}/",
        ).status_code, 403)
        self.grant_a.active = False
        self.grant_a.save(update_fields=["active"])
        self.client.force_authenticate(user=self.family_a)
        self.assertEqual(self.client.get(
            f"/api/v1/jireh-sgo/family/applications/{app_id}/",
        ).status_code, 403)
        self.grant_a.active = True
        self.grant_a.save(update_fields=["active"])
        self.org_a.active = False
        self.org_a.save(update_fields=["active"])
        self.assertEqual(self.client.get(
            f"/api/v1/jireh-sgo/family/applications/{app_id}/",
        ).status_code, 403)

    def test_input_validation_and_school_selector_cannot_bypass_sgo_scope(self):
        self.client.force_authenticate(user=self.family_a)
        for data in (
            {**self._data(), "consent": "true"},
            {**self._data(), "consent": False},
            {**self._data(), "grade_level": "adult"},
            {**self._data(), "ssn": "synthetic-forbidden"},
            {**self._data(), "submission_key": "not-a-uuid"},
        ):
            with self.subTest(data=list(data.keys())):
                self.assertEqual(self.client.post(
                    "/api/v1/jireh-sgo/family/submit/", data, format="json",
                ).status_code, 400)
        self.assertEqual(self.client.post(
            "/api/v1/jireh-sgo/family/submit/", self._data(),
            format="json", HTTP_X_SCHOOL_ID=str(uuid4()),
        ).status_code, 400)
        self.assertEqual(self.client.get(
            "/api/v1/jireh-sgo/family/programs/", HTTP_X_CROWN_SCHOOL_ID=str(uuid4()),
        ).status_code, 400)
        self.assertFalse(SGOApplication.objects.exists())

    def test_local_gate_disabled_and_hosted_runtime_denied(self):
        self.client.force_authenticate(user=self.family_a)
        with override_settings(CROWN_SGO_FICTIONAL_INTAKE_ENABLED=False):
            self.assertNotEqual(self.client.get(
                "/api/v1/jireh-sgo/family/programs/",
            ).status_code, 200)
        with override_settings(CROWN_ENV="production"):
            self.assertNotEqual(self.client.get(
                "/api/v1/jireh-sgo/family/programs/",
            ).status_code, 200)
        with override_settings(DEBUG=False):
            self.assertNotEqual(self.client.get(
                "/api/v1/jireh-sgo/family/programs/",
            ).status_code, 200)

    def test_processor_cannot_act_after_review(self):
        created = self._submit_a()
        app_id = created.data["application"]["id"]
        SGOApplication.objects.filter(pk=app_id).update(eligibility=SGOApplication.ELIGIBLE)
        self.client.force_authenticate(user=self.processor_a)
        self.assertEqual(self.client.post(
            self._request_url(app_id), {"expected_revision": 1,
                "reason": "GRADE_UNVERIFIED", "request_key": str(uuid4())}, format="json",
        ).status_code, 409)
        self.assertFalse(SGOAward.objects.exists())
