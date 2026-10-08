import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied, ValidationError
from jireh_sgo.models import SGOOrganization, SGOMembership, SGOAward, SGOAuditEvent
from jireh_sgo.services import create_program, create_application, attest_eligibility, commit_award


class SGOServiceTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username="sgo_admin", password="test-password")
        self.reviewer = User.objects.create_user(username="sgo_reviewer", password="test-password")
        self.viewer = User.objects.create_user(username="sgo_viewer", password="test-password")
        self.outsider = User.objects.create_superuser(username="sgo_outsider", password="test-password", email="outsider@example.test")
        self.org = SGOOrganization.objects.create(legal_name="Test Grantor", state_of_domicile="VA", active=True)
        self.other = SGOOrganization.objects.create(legal_name="Other Grantor", state_of_domicile="PA", active=True)
        for user, role in [(self.admin, SGOMembership.ADMIN), (self.reviewer, SGOMembership.REVIEWER), (self.viewer, SGOMembership.VIEWER)]:
            SGOMembership.objects.create(organization=self.org, user=user, role=role, active=True)
        self.program = create_program(user=self.admin, organization_id=self.org.id, name="2027 Pilot",
            code="pilot", calendar_year=2027, funding_source="FEDERAL_25F", rule_version="RULE_2027_V1")
        self.application = create_application(user=self.reviewer, organization_id=self.org.id,
            program_id=self.program.id, student_key=uuid.uuid4(), school_key=uuid.uuid4())

    def test_lifecycle_creates_noncash_commitment_with_audit(self):
        attest_eligibility(user=self.reviewer, organization_id=self.org.id,
            application_id=self.application.id, eligible=True, evidence_key="EVIDENCE_2027_X")
        award = commit_award(user=self.admin, organization_id=self.org.id,
            application_id=self.application.id, amount_cents=125000)
        self.assertEqual(award.status, "COMMITTED")
        self.assertEqual(award.amount_cents, 125000)
        self.assertEqual(SGOAuditEvent.objects.filter(organization=self.org, action="AWARD_COMMITTED_NONCASH").count(), 1)

    def test_unapproved_application_rejected(self):
        with self.assertRaises(ValidationError):
            commit_award(user=self.admin, organization_id=self.org.id,
                application_id=self.application.id, amount_cents=1000)

    def test_viewer_and_outsider_must_not_write(self):
        for user in (self.viewer, self.outsider):
            with self.assertRaises(PermissionDenied):
                attest_eligibility(user=user, organization_id=self.org.id,
                    application_id=self.application.id, eligible=True, evidence_key="EVIDENCE_2027_X")
            with self.assertRaises(PermissionDenied):
                commit_award(user=user, organization_id=self.org.id,
                    application_id=self.application.id, amount_cents=1000)

    def test_cross_organization_access_denied(self):
        for user in (self.admin, self.reviewer, self.viewer, self.outsider):
            with self.assertRaises(PermissionDenied):
                create_application(user=user, organization_id=self.other.id,
                    program_id=self.program.id, student_key=uuid.uuid4(), school_key=uuid.uuid4())

    def test_duplicate_award_rejected(self):
        attest_eligibility(user=self.reviewer, organization_id=self.org.id,
            application_id=self.application.id, eligible=True, evidence_key="EVIDENCE_2027_X")
        commit_award(user=self.admin, organization_id=self.org.id,
            application_id=self.application.id, amount_cents=1000)
        with self.assertRaises(ValidationError):
            commit_award(user=self.admin, organization_id=self.org.id,
                application_id=self.application.id, amount_cents=1000)
        self.assertEqual(SGOAward.objects.filter(application=self.application).count(), 1)

    def test_negative_and_invalid_amounts_rejected(self):
        attest_eligibility(user=self.reviewer, organization_id=self.org.id,
            application_id=self.application.id, eligible=True, evidence_key="EVIDENCE_2027_X")
        for amount in (0, -1, True, "1000", 9000000000000001):
            with self.assertRaises(ValidationError):
                commit_award(user=self.admin, organization_id=self.org.id,
                    application_id=self.application.id, amount_cents=amount)

    def test_evidence_key_must_be_opaque(self):
        with self.assertRaises(ValidationError):
            attest_eligibility(user=self.reviewer, organization_id=self.org.id,
                application_id=self.application.id, eligible=True, evidence_key="My SSN 123-45-6789")
