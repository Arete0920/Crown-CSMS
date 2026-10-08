import json
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from jireh_sgo.models import SGOAward, SGOMembership, SGOOrganization, SGOProgram


class SGOApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username="api_sgo_admin", password="test-password")
        self.reviewer = User.objects.create_user(username="api_sgo_reviewer", password="test-password")
        self.viewer = User.objects.create_user(username="api_sgo_viewer", password="test-password")
        self.outsider = User.objects.create_superuser(
            username="api_sgo_outsider", email="outsider@example.test", password="test-password"
        )
        self.org = SGOOrganization.objects.create(
            legal_name="Virginia Pilot SGO", state_of_domicile="VA", active=True
        )
        self.other = SGOOrganization.objects.create(
            legal_name="Other SGO", state_of_domicile="PA", active=True
        )
        for user, role in (
            (self.admin, SGOMembership.ADMIN),
            (self.reviewer, SGOMembership.REVIEWER),
            (self.viewer, SGOMembership.VIEWER),
        ):
            SGOMembership.objects.create(
                organization=self.org, user=user, role=role, active=True
            )

    def endpoint(self, endpoint="sgo-programs", organization=None, **kwargs):
        return reverse(endpoint, kwargs={"organization_id": (organization or self.org).id, **kwargs})

    def post_json(self, url, data):
        return self.client.post(url, data=json.dumps(data), content_type="application/json")

    def test_missing_auth_and_nonmember_are_denied(self):
        self.assertIn(self.client.get(self.endpoint()).status_code, (401, 403))
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(self.endpoint()).status_code, 403)

    def test_school_tenant_header_cannot_grant_sgo_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.endpoint(), HTTP_X_SCHOOL_ID=str(uuid.uuid4()))
        self.assertIn(response.status_code, (400, 404))

    def test_cross_grantor_access_denied_even_to_sgo_admin(self):
        self.client.force_login(self.admin)
        self.assertEqual(
            self.client.get(self.endpoint(organization=self.other)).status_code, 403
        )

    def test_view_only_cannot_mutate(self):
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(self.endpoint()).status_code, 200)
        response = self.post_json(self.endpoint(), {
            "name": "Pilot", "code": "pilot", "calendar_year": 2027,
            "funding_source": "FEDERAL_25F", "eligibility_rule_version": "RULE_2027_V1",
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(SGOProgram.objects.count(), 0)

    def test_pilot_lifecycle_separates_noncash_awards(self):
        self.client.force_login(self.admin)
        created_program = self.post_json(self.endpoint(), {
            "name": "2027 Pilot", "code": "pilot", "calendar_year": 2027,
            "funding_source": "FEDERAL_25F", "eligibility_rule_version": "RULE_2027_V1",
        })
        self.assertEqual(created_program.status_code, 201)
        self.client.force_login(self.reviewer)
        created_application = self.post_json(self.endpoint("sgo-applications"), {
            "program_id": created_program.json()["id"],
            "student_key": str(uuid.uuid4()),
            "school_key": str(uuid.uuid4()),
        })
        self.assertEqual(created_application.status_code, 201)
        application_id = uuid.UUID(created_application.json()["id"])
        review_url = self.endpoint("sgo-review", application_id=application_id)
        reviewed = self.post_json(review_url, {
            "eligible": True, "evidence_key": "EVIDENCE_2027_A",
        })
        self.assertEqual(reviewed.status_code, 200)
        denied = self.post_json(self.endpoint("sgo-awards"), {
            "application_id": str(application_id), "amount_cents": 125000,
        })
        self.assertEqual(denied.status_code, 403)
        self.client.force_login(self.admin)
        award = self.post_json(self.endpoint("sgo-awards"), {
            "application_id": str(application_id), "amount_cents": 125000,
        })
        self.assertEqual(award.status_code, 201)
        self.assertFalse(award.json()["cash_movement"])
        self.assertEqual(SGOAward.objects.count(), 1)
        self.assertEqual(
            self.post_json(self.endpoint("sgo-awards"), {
                "application_id": str(application_id), "amount_cents": 125000,
            }).status_code, 400
        )
        summary = self.client.get(self.endpoint("sgo-summary")).json()
        self.assertEqual(summary["commitments"], 1)
        self.assertFalse(summary["live_settlement_enabled"])
        self.assertFalse(summary["regulatory_certified"])

    def test_invalid_amount_rejected(self):
        self.client.force_login(self.admin)
        response = self.post_json(self.endpoint("sgo-awards"), {
            "application_id": str(uuid.uuid4()), "amount_cents": -1,
        })
        self.assertEqual(response.status_code, 400)
