import io
import json
from datetime import date

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from core.models import Family, School, Student, StudentIdentityLink
from households.models import Household, Student as CompatibilityStudent


class StudentIdentityLinkTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name='Alpha Christian School')
        self.other_school = School.objects.create(name='Beta Christian School')
        self.family = Family.objects.create(school=self.school, family_name='Able')
        self.other_family = Family.objects.create(school=self.other_school, family_name='Baker')
        self.core_student = Student.objects.create(
            school=self.school,
            family=self.family,
            student_number='A-100',
            first_name='Avery',
            last_name='Able',
            dob=date(2012, 1, 2),
            status='ACTIVE',
        )
        self.other_core_student = Student.objects.create(
            school=self.other_school,
            family=self.other_family,
            student_number='B-100',
            first_name='Blake',
            last_name='Baker',
            dob=date(2011, 3, 4),
            status='ACTIVE',
        )
        self.household = Household.objects.create(
            school_id=self.school.id,
            name='Able Household',
        )
        self.other_household = Household.objects.create(
            school_id=self.other_school.id,
            name='Baker Household',
        )
        self.compatibility_student = CompatibilityStudent.objects.create(
            school_id=self.school.id,
            household=self.household,
            first_name='Avery',
            last_name='Able',
            is_active=True,
        )
        self.other_compatibility_student = CompatibilityStudent.objects.create(
            school_id=self.other_school.id,
            household=self.other_household,
            first_name='Blake',
            last_name='Baker',
            is_active=True,
        )

    def test_verified_same_school_mapping_saves(self):
        link = StudentIdentityLink.objects.create(
            school=self.school,
            core_student=self.core_student,
            compatibility_student=self.compatibility_student,
            source=StudentIdentityLink.SOURCE_MANUAL,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
            evidence_reference='ticket:IDENTITY-1',
        )
        self.assertEqual(link.school_id, self.school.id)

    def test_verified_mapping_requires_evidence_reference(self):
        with self.assertRaises(ValidationError):
            StudentIdentityLink.objects.create(
                school=self.school,
                core_student=self.core_student,
                compatibility_student=self.compatibility_student,
                source=StudentIdentityLink.SOURCE_MANUAL,
                verification_status=StudentIdentityLink.STATUS_VERIFIED,
                evidence_reference='',
            )

    def test_cross_school_core_student_is_rejected(self):
        with self.assertRaises(ValidationError):
            StudentIdentityLink.objects.create(
                school=self.school,
                core_student=self.other_core_student,
                compatibility_student=self.compatibility_student,
                source=StudentIdentityLink.SOURCE_MANUAL,
                verification_status=StudentIdentityLink.STATUS_VERIFIED,
                evidence_reference='ticket:IDENTITY-2',
            )

    def test_cross_school_compatibility_student_is_rejected(self):
        with self.assertRaises(ValidationError):
            StudentIdentityLink.objects.create(
                school=self.school,
                core_student=self.core_student,
                compatibility_student=self.other_compatibility_student,
                source=StudentIdentityLink.SOURCE_MANUAL,
                verification_status=StudentIdentityLink.STATUS_VERIFIED,
                evidence_reference='ticket:IDENTITY-3',
            )

    def test_one_to_one_core_mapping_is_enforced(self):
        StudentIdentityLink.objects.create(
            school=self.school,
            core_student=self.core_student,
            compatibility_student=self.compatibility_student,
            source=StudentIdentityLink.SOURCE_MANUAL,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
            evidence_reference='ticket:IDENTITY-4',
        )
        second_household = Household.objects.create(
            school_id=self.school.id,
            name='Second Able Household',
        )
        second_compatibility_student = CompatibilityStudent.objects.create(
            school_id=self.school.id,
            household=second_household,
            first_name='Avery',
            last_name='Able',
            is_active=True,
        )
        with self.assertRaises(ValidationError):
            StudentIdentityLink.objects.create(
                school=self.school,
                core_student=self.core_student,
                compatibility_student=second_compatibility_student,
                source=StudentIdentityLink.SOURCE_MANUAL,
                verification_status=StudentIdentityLink.STATUS_VERIFIED,
                evidence_reference='ticket:IDENTITY-5',
            )

    def test_reconciliation_command_is_read_only_and_reports_unmatched(self):
        StudentIdentityLink.objects.create(
            school=self.school,
            core_student=self.core_student,
            compatibility_student=self.compatibility_student,
            source=StudentIdentityLink.SOURCE_MANUAL,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
            evidence_reference='ticket:IDENTITY-6',
        )
        before = StudentIdentityLink.objects.count()
        stdout = io.StringIO()
        call_command('reconcile_student_identities', '--school-id', str(self.school.id), stdout=stdout)
        payload = json.loads(stdout.getvalue())

        self.assertEqual(StudentIdentityLink.objects.count(), before)
        self.assertEqual(payload['mode'], 'read_only')
        self.assertEqual(payload['candidate_matching'], 'disabled_no_safe_deterministic_key')
        school_report = payload['schools'][0]
        self.assertEqual(school_report['mapped_total'], 1)
        self.assertEqual(school_report['unmatched_core'], 0)
        self.assertEqual(school_report['unmatched_compatibility'], 0)
        self.assertEqual(school_report['invalid_cross_tenant_links'], 0)
        self.assertEqual(school_report['ambiguous_candidates'], 'not_inferred')
