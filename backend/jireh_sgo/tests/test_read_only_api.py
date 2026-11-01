"""SGO pilot views: active membership, organization isolation, aggregate-only data."""
import uuid
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from jireh_sgo.models import SGOOrganization, SGOMembership
from jireh_sgo.services import create_program, create_application, attest_eligibility, commit_award


class SGOReadOnlyAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.member = User.objects.create_user(username="sgo-member", email="sgo-member@example.test", password="synthetic")
        self.outsider = User.objects.create_superuser(username="sgo-outsider", email="sgo-outsider@example.test", password="synthetic")
        self.org = SGOOrganization.objects.create(legal_name="Synthetic SGO", state_of_domicile="DE", active=True)
        self.other = SGOOrganization.objects.create(legal_name="Other SGO", state_of_domicile="PA", active=True)
        self.grant = SGOMembership.objects.create(user=self.member, organization=self.org, role=SGOMembership.VIEWER, active=True)
        self.list_url = "/api/v1/jireh-sgo/organizations/"
        self.url = f"/api/v1/jireh-sgo/organizations/{self.org.id}/overview/"

    def test_membership_required_even_for_superuser(self):
        self.assertIn(self.client.get(self.list_url).status_code, (401, 403))
        self.client.force_authenticate(user=self.outsider)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_member_only_sees_own_active_organization(self):
        self.client.force_authenticate(user=self.member)
        listed = self.client.get(self.list_url)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual([o["id"] for o in listed.data["organizations"]], [str(self.org.id)])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response.data["totals"]["noncash_committed_cents"], 0)
        self.assertEqual(self.client.get(f"/api/v1/jireh-sgo/organizations/{self.other.id}/overview/").status_code, 403)

    def test_inactive_member_and_organization_fail_closed(self):
        self.client.force_authenticate(user=self.member)
        self.grant.active = False
        self.grant.save(update_fields=["active"])
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.grant.active = True
        self.grant.save(update_fields=["active"])
        self.org.active = False
        self.org.save(update_fields=["active"])
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_aggregate_reveals_no_student_school_or_evidence_ids(self):
        self.grant.role = SGOMembership.ADMIN
        self.grant.save(update_fields=["role"])
        program = create_program(user=self.member, organization_id=self.org.id,
            name="Synthetic Noncash Program", code="pilot", calendar_year=2027,
            funding_source="PRIVATE", rule_version="POLICY_2027_V1")
        student, school, evidence = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        application = create_application(user=self.member, organization_id=self.org.id,
            program_id=program.id, student_key=student, school_key=school)
        attest_eligibility(user=self.member, organization_id=self.org.id,
            application_id=application.id, eligible=True, evidence_key=evidence)
        commit_award(user=self.member, organization_id=self.org.id,
            application_id=application.id, amount_cents=15750)
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["totals"]["noncash_committed_cents"], 15750)
        self.assertEqual(response.data["funds_status"], "NONCASH_ONLY")
        import json
        payload = json.dumps(response.data)
        for identifier in (student, school, evidence, application.id):
            self.assertNotIn(str(identifier), payload)

    def test_rejects_caller_supplied_school_tenant(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.url, HTTP_X_SCHOOL_ID=str(uuid.uuid4()))
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(response.status_code, (200, 201))
