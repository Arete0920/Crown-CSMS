import uuid
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as ModelValidationError
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied, ValidationError

from jireh_sgo.models import SGOOrganization, SGOMembership, SGOAuditEvent, SGOAward
from jireh_sgo.services import (
    create_program, create_application, attest_eligibility, commit_award, cancel_award, membership_for,
)


class SGOFoundationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username="grantor_admin", password="sample-password")
        self.reviewer = User.objects.create_user(username="grantor_reviewer", password="sample-password")
        self.viewer = User.objects.create_user(username="grantor_viewer", password="sample-password")
        self.outsider = User.objects.create_superuser(
            username="grantor_outsider", password="sample-password", email="outsider@example.test",
        )
        self.org = SGOOrganization.objects.create(legal_name="A", state_of_domicile="VA", active=True)
        self.other = SGOOrganization.objects.create(legal_name="B", state_of_domicile="PA", active=True)
        for user, role in (
            (self.admin, SGOMembership.ADMIN),
            (self.reviewer, SGOMembership.REVIEWER),
            (self.viewer, SGOMembership.VIEWER),
        ):
            SGOMembership.objects.create(organization=self.org, user=user, role=role, active=True)
        self.kwargs = dict(
            user=self.admin, organization_id=self.org.id, name="Synthetic policy",
            code="pilot", calendar_year=2027, funding_source="PRIVATE", rule_version="POLICY_2027_V1",
        )
        self.program = create_program(**self.kwargs)
        self.student, self.school, self.evidence = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        self.app = create_application(
            user=self.reviewer, organization_id=self.org.id,
            program_id=self.program.id, student_key=self.student, school_key=self.school,
        )

    def attest(self, eligible=True, evidence=None):
        return attest_eligibility(
            user=self.reviewer, organization_id=self.org.id,
            application_id=self.app.id, eligible=eligible, evidence_key=evidence or self.evidence,
        )

    def award(self, amount=1000):
        return commit_award(
            user=self.admin, organization_id=self.org.id, application_id=self.app.id, amount_cents=amount,
        )

    def test_inactive_membership_and_superuser_do_not_bypass_authority(self):
        org = SGOOrganization.objects.create(legal_name="C", state_of_domicile="DE")
        member = SGOMembership.objects.create(
            user=self.outsider, organization=org, role=SGOMembership.ADMIN,
        )
        self.assertFalse(org.active)
        self.assertFalse(member.active)
        for user in (self.viewer, self.outsider):
            with self.assertRaises(PermissionDenied):
                commit_award(user=user, organization_id=self.org.id, application_id=self.app.id, amount_cents=10)
        with self.assertRaises(PermissionDenied):
            membership_for(self.outsider, org.id)

    def test_cross_organization_program_application_and_award_denied(self):
        SGOMembership.objects.create(
            user=self.outsider, organization=self.other, role=SGOMembership.ADMIN, active=True,
        )
        with self.assertRaises(PermissionDenied):
            create_application(
                user=self.outsider, organization_id=self.other.id, program_id=self.program.id,
                student_key=uuid.uuid4(), school_key=uuid.uuid4(),
            )
        with self.assertRaises(PermissionDenied):
            attest_eligibility(
                user=self.outsider, organization_id=self.other.id, application_id=self.app.id,
                eligible=True, evidence_key=self.evidence,
            )
        with self.assertRaises(PermissionDenied):
            commit_award(
                user=self.outsider, organization_id=self.other.id,
                application_id=self.app.id, amount_cents=10,
            )
        self.assertFalse(hasattr(self.app, "organization_id"))

    def test_direct_application_reassignment_rejected(self):
        second = create_program(**{**self.kwargs, "rule_version": "POLICY_2027_V2"})
        self.app.program = second
        with self.assertRaises(ModelValidationError):
            self.app.save()
        self.app.refresh_from_db()
        self.app.school_key = uuid.uuid4()
        with self.assertRaises(ModelValidationError):
            self.app.save()
        self.app.refresh_from_db()
        self.app.student_key = uuid.uuid4()
        with self.assertRaises(ModelValidationError):
            self.app.save()

    def test_program_and_application_concurrent_retry_contract(self):
        self.assertEqual(create_program(**self.kwargs).pk, self.program.pk)
        same = create_application(
            user=self.reviewer, organization_id=self.org.id,
            program_id=self.program.pk, student_key=self.student, school_key=self.school,
        )
        self.assertEqual(same.pk, self.app.pk)
        self.assertEqual(SGOAuditEvent.objects.filter(
            action=SGOAuditEvent.PROGRAM_CREATED,
        ).count(), 1)
        self.assertEqual(SGOAuditEvent.objects.filter(
            action=SGOAuditEvent.APPLICATION_CREATED,
        ).count(), 1)

    def test_rejects_string_boolean_and_personal_evidence(self):
        for value in ("false", "true", 0, 1, None):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.attest(eligible=value)
        for value in ("My SSN 123-45-6789", "123-45-6789", uuid.uuid1()):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.attest(evidence=value)

    def test_program_version_and_replay(self):
        self.assertEqual(create_program(**self.kwargs).id, self.program.id)
        version_two = create_program(**{**self.kwargs, "rule_version": "POLICY_2027_V2"})
        self.assertNotEqual(version_two.id, self.program.id)
        self.assertEqual(self.app.program_id, self.program.id)
        self.program.eligibility_rule_version = "POLICY_2027_V3"
        with self.assertRaises(ModelValidationError):
            self.program.save()

    def test_application_and_attestation_replay(self):
        same = create_application(
            user=self.reviewer, organization_id=self.org.id,
            program_id=self.program.id, student_key=self.student, school_key=self.school,
        )
        self.assertEqual(same.id, self.app.id)
        with self.assertRaises(ValidationError):
            create_application(
                user=self.reviewer, organization_id=self.org.id,
                program_id=self.program.id, student_key=self.student, school_key=uuid.uuid4(),
            )
        self.attest()
        self.attest()
        self.assertEqual(
            SGOAuditEvent.objects.filter(action=SGOAuditEvent.ELIGIBILITY_ATTESTED).count(), 1,
        )

    def test_noncash_commit_replay_and_cancellation(self):
        with self.assertRaises(ValidationError):
            self.award()
        self.attest()
        award = self.award()
        self.assertEqual(self.award().id, award.id)
        self.assertEqual(award.status, SGOAward.COMMITTED)
        self.assertFalse(hasattr(award, "organization_id"))
        self.assertEqual(SGOAuditEvent.objects.filter(action=SGOAuditEvent.AWARD_COMMITTED).count(), 1)
        with self.assertRaises(ValidationError):
            self.award(1001)
        cancel_award(user=self.admin, organization_id=self.org.id, award_id=award.id)
        cancel_award(user=self.admin, organization_id=self.org.id, award_id=award.id)
        self.assertEqual(SGOAuditEvent.objects.filter(action=SGOAuditEvent.AWARD_CANCELLED).count(), 1)
        with self.assertRaises(ValidationError):
            self.award()
        self.assertEqual(SGOAward.objects.count(), 1)

    def test_reject_invalid_amount_and_funded_status(self):
        self.attest()
        for value in (0, -1, True, "1000", 2.0, 9_000_000_000_000_001):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.award(value)
        award = self.award()
        award.status = "FUNDED"
        with self.assertRaises(ModelValidationError):
            award.save()
        award.refresh_from_db()
        award.amount_cents = 1001
        with self.assertRaises(ModelValidationError):
            award.save()
        with self.assertRaises(ValidationError):
            self.attest()

    def test_audit_rejects_sensitive_metadata_and_updates(self):
        with self.assertRaises(ModelValidationError):
            SGOAuditEvent.objects.create(
                organization=self.org, actor=self.admin,
                action=SGOAuditEvent.APPLICATION_CREATED,
                subject_key=uuid.uuid4(), metadata={"ssn": "123-45-6789"},
            )
        with self.assertRaises(ModelValidationError):
            SGOAuditEvent.objects.create(
                organization=self.org, actor=self.admin,
                action=SGOAuditEvent.PROGRAM_CREATED,
                subject_key=uuid.uuid4(), metadata={"source": "PRIVATE", "year": True},
            )
        event = SGOAuditEvent.objects.first()
        with self.assertRaises(ModelValidationError):
            event.save()

    def test_no_school_ledger_or_payment_dependency(self):
        import inspect
        import jireh_sgo.services as services
        source = inspect.getsource(services)
        for text in ("from aid.", "from financial_aid.", "from ledger.", "from core.", "Payment.objects", "LedgerEntry"):
            self.assertNotIn(text, source)
