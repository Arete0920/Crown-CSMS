"""Django regression tests for the read-only Kairos canonical snapshot."""
from datetime import date

from django.test import TestCase
from rest_framework.exceptions import PermissionDenied, ValidationError

from academics.models import Course, Enrollment, Section, TeacherAssignment
from bell_schedule_wizard.models import BellSchedule
from core.models import Family, Staff, Student as CoreStudent, StudentIdentityLink
from households.models import Household, Student as CompatibilityStudent
from section_scheduler_wizard.canonical_snapshot import build_canonical_planning_snapshot
from section_scheduler_wizard.preflight import CandidatePlacement, validate_candidate_placements

from .test_views import _client_for, _fixtures


class CanonicalSnapshotTests(TestCase):
    def setUp(self):
        self.school, self.year, self.section, self.template, self.block, self.room = _fixtures()
        self.actor = _client_for(self.school).handler._force_user

    def snapshot(self, **overrides):
        args = dict(actor=self.actor, school_id=self.school.id,
                    academic_year_id=self.year.id, term_code="S1")
        args.update(overrides)
        return build_canonical_planning_snapshot(**args)

    def add_enrollment(self, *, identity=True):
        family = Family.objects.create(school=self.school, family_name="Synthetic Family")
        student = CoreStudent.objects.create(
            school=self.school, family=family, student_number="SYN-1",
            first_name="Synthetic", last_name="Learner", dob=date(2012, 1, 1), status="ACTIVE")
        household = Household.objects.create(school_id=self.school.id, name="Synthetic Household")
        compat = CompatibilityStudent.objects.create(school_id=self.school.id, household=household,
            first_name="Synthetic", last_name="Learner")
        Enrollment.objects.create(school_id=self.school.id, section=self.section, student=compat)
        if identity:
            StudentIdentityLink.objects.create(school=self.school, core_student=student,
                compatibility_student=compat, verification_status="verified",
                source="manual", evidence_reference="test-fixture-proof")
        return student, compat

    def add_teacher(self):
        staff = Staff.objects.create(school=self.school, first_name="Synthetic",
            last_name="Teacher", email="kairos-synthetic@example.invalid",
            role_type="TEACHER", status="ACTIVE")
        TeacherAssignment.objects.create(school_id=self.school.id,
            section=self.section, staff=staff)
        return staff

    def test_verified_canonical_identity_and_preflight(self):
        core, compat = self.add_enrollment()
        staff = self.add_teacher()
        snap = self.snapshot()
        projection = snap.section_inputs[str(self.section.id)]
        self.assertEqual(projection.student_ids, frozenset({str(core.id)}))
        self.assertNotIn(str(compat.id), projection.student_ids)
        self.assertEqual(projection.teacher_ids, frozenset({str(staff.id)}))
        self.assertEqual(validate_candidate_placements(
            school_id=snap.school_id, academic_year_id=snap.academic_year_id,
            term_code=snap.term_code, sections=snap.section_inputs,
            periods=snap.period_inputs, rooms=snap.room_inputs,
            placements=[CandidatePlacement(str(self.section.id), str(self.block.id), str(self.room.id))]
        ), ())

    def test_unlinked_or_pending_student_denied(self):
        _, compat = self.add_enrollment(identity=False)
        with self.assertRaises(ValidationError):
            self.snapshot()
        link = StudentIdentityLink.objects.create(
            school=self.school, core_student=CoreStudent.objects.get(school=self.school),
            compatibility_student=compat, source="manual",
            verification_status="pending", evidence_reference="synthetic-proof")
        with self.assertRaises(ValidationError):
            self.snapshot()
        link.verification_status = "verified"
        link.save(update_fields=["verification_status"])
        self.assertEqual(len(self.snapshot().verified_student_ids), 1)

    def test_foreign_tenant_and_year_denied(self):
        another_school, another_year, *_ = _fixtures()
        with self.assertRaises(PermissionDenied):
            self.snapshot(school_id=another_school.id)
        with self.assertRaises(ValidationError):
            self.snapshot(academic_year_id=another_year.id)

    def test_absent_principal_denied(self):
        with self.assertRaises(PermissionDenied):
            self.snapshot(actor=None)

    def test_foreign_enrollment_attribution_denied(self):
        self.add_enrollment()
        another_school, *_ = _fixtures()
        # Canonical model forbids foreign authority mutation before extraction.
        with self.assertRaises(Exception):
            Enrollment.objects.filter(section=self.section).update(school_id=another_school.id)
        self.assertEqual(len(self.snapshot().verified_student_ids), 1)

    def test_foreign_teacher_attribution_denied(self):
        self.add_teacher()
        another_school, *_ = _fixtures()
        # Tenant guards must reject a cross-school attribution update.
        with self.assertRaises(Exception):
            TeacherAssignment.objects.filter(section=self.section).update(school_id=another_school.id)
        self.assertEqual(len(self.snapshot().assigned_staff_ids), 1)

    def test_changed_protected_period_changes_fingerprint(self):
        prior = self.snapshot().source_fingerprint
        # Keep one instructional period so the snapshot remains valid.
        from bell_schedule_wizard.models import PeriodBlock
        PeriodBlock.objects.create(
            template=self.template, code="P2", label="Period 2",
            start_time=__import__("datetime").time(9, 0),
            end_time=__import__("datetime").time(10, 0),
            ordering=1, is_instructional=True)
        self.block.is_instructional = False
        self.block.save(update_fields=["is_instructional"])
        self.assertNotEqual(self.snapshot().source_fingerprint, prior)

    def test_changed_room_capacity_changes_fingerprint(self):
        prior = self.snapshot().source_fingerprint
        self.room.capacity = 18
        self.room.save(update_fields=["capacity"])
        self.assertNotEqual(self.snapshot().source_fingerprint, prior)

    def test_legacy_unlinked_section_denied(self):
        Section.objects.create(school_id=self.school.id,
            course=self.section.course, term="S1", term_ref=None)
        with self.assertRaises(ValidationError):
            self.snapshot()

    def test_multiple_active_bell_schedules_denied(self):
        BellSchedule.objects.create(school=self.school, academic_year=self.year,
            name="Duplicate Active", schedule_mode="SINGLE_DAY", is_active=True)
        with self.assertRaises(ValidationError):
            self.snapshot()

    def test_foreign_course_denied(self):
        school_b, *_ = _fixtures()
        self.section.course = Course.objects.create(school_id=school_b.id,
            code="TEST", name="Synthetic Foreign Course")
        # The existing model save guard blocks foreign-course assignments.
        from django.core.exceptions import ValidationError as DjangoValidationError
        with self.assertRaises(DjangoValidationError):
            self.section.save(update_fields=["course"])
        self.assertIn(str(self.section.id), self.snapshot().section_inputs)

    def test_input_is_immutable_and_version_stable(self):
        snap = self.snapshot()
        self.assertEqual(snap.source_fingerprint, self.snapshot().source_fingerprint)
        with self.assertRaises(TypeError):
            snap.section_inputs["forged"] = "new section"

    def test_historical_same_term_code_does_not_block_current_year(self):
        from academics.models import Term
        from core.models import AcademicYear
        from datetime import date
        prior_year = AcademicYear.objects.create(
            school=self.school, name="2025-2026",
            start_date=date(2025, 8, 20), end_date=date(2026, 6, 10))
        prior_term = Term.objects.create(
            school_id=self.school.id, academic_year=prior_year, code="S1",
            name="Prior fall", active=True)
        Section.objects.create(school_id=self.school.id, course=self.section.course,
                               term="S1", term_ref=prior_term)
        self.assertIn(str(self.section.id), self.snapshot().section_inputs)

    def test_empty_selected_term_denied(self):
        Section.objects.filter(pk=self.section.pk).delete()
        with self.assertRaises(ValidationError):
            self.snapshot()

    def test_missing_tenant_permission_denied(self):
        from core.models import UserRole
        actor = self.actor
        UserRole.objects.filter(user=actor, school=self.school).delete()
        with self.assertRaises(PermissionDenied):
            self.snapshot(actor=actor)
