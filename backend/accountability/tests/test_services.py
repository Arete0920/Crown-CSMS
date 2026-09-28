from django.test import TestCase

from core.models import School, UserAccount
from households.models import Household, Student

from accountability.models import AccountabilityEvent
from accountability.services import (
    AccountabilityConflict,
    InvalidAccountabilityTransition,
    transition_student,
)


class AccountabilityServiceTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Test School")
        self.other_school = School.objects.create(name="Other School")
        self.household = Household.objects.create(school_id=self.school.id, name="Test Family")
        self.student = Student.objects.create(
            school_id=self.school.id,
            household=self.household,
            first_name="Avery",
            last_name="Student",
        )
        self.user = UserAccount.objects.create_user(
            username="accountability-admin",
            password="test-pass",
            school=self.school,
        )

    def test_transition_creates_projection_and_append_only_event(self):
        result = transition_student(
            school=self.school,
            student_id=self.student.id,
            actor_user=self.user,
            event_type="classroom.accounted",
            normal_state="IN_CLASS",
            location_code="ROOM-204",
            expected_version=1,
        )
        self.assertEqual(result.state.normal_state, "IN_CLASS")
        self.assertEqual(result.state.location_code, "ROOM-204")
        self.assertEqual(result.state.version, 2)
        self.assertEqual(result.event.state_version, 2)
        self.assertEqual(AccountabilityEvent.objects.count(), 1)

        result2 = transition_student(
            school=self.school,
            student_id=self.student.id,
            actor_user=self.user,
            event_type="dismissal.queued",
            normal_state="DISMISSAL_QUEUED",
            expected_version=2,
        )
        self.assertEqual(result2.state.version, 3)
        self.assertEqual(AccountabilityEvent.objects.count(), 2)

    def test_expected_version_conflict_is_fail_closed(self):
        transition_student(
            school=self.school,
            student_id=self.student.id,
            actor_user=self.user,
            event_type="classroom.accounted",
            normal_state="IN_CLASS",
            expected_version=1,
        )
        with self.assertRaises(AccountabilityConflict):
            transition_student(
                school=self.school,
                student_id=self.student.id,
                actor_user=self.user,
                event_type="dismissal.queued",
                normal_state="DISMISSAL_QUEUED",
                expected_version=1,
            )

    def test_cross_tenant_student_is_rejected(self):
        with self.assertRaises(InvalidAccountabilityTransition):
            transition_student(
                school=self.other_school,
                student_id=self.student.id,
                actor_user=None,
                event_type="invalid.cross_tenant",
                normal_state="IN_CLASS",
            )

    def test_event_is_immutable(self):
        result = transition_student(
            school=self.school,
            student_id=self.student.id,
            actor_user=self.user,
            event_type="classroom.accounted",
            normal_state="IN_CLASS",
            expected_version=1,
        )
        result.event.event_type = "tampered"
        with self.assertRaises(RuntimeError):
            result.event.save()
        with self.assertRaises(RuntimeError):
            result.event.delete()
