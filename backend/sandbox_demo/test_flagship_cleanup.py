from datetime import date
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from aid.models import AidAuditEvent, AidAward
from core.models import AcademicYear, Family, School, Student, UserAccount
from sandbox_demo.admissions_seed import FAMILY_NAME
from sandbox_demo.catalog import SANDBOX_SCHOOLS
from sandbox_demo.services import _clear_flagship_data, ensure_demo_school


class FlagshipResetCleanupTests(TestCase):
    def test_command_rolls_back_earlier_cleanup_on_foreign_actor_refusal(self):
        school = ensure_demo_school(SANDBOX_SCHOOLS["heritage-core"])
        family = Family.objects.create(school=school, family_name=FAMILY_NAME)
        actor = UserAccount.objects.create_user(
            username="reset-actor@example.org", school=school,
        )
        foreign = School.objects.create(name="Unrelated Customer Academy")
        event = AidAuditEvent.objects.create(
            school=foreign, actor_user=actor,
            entity_type=AidAuditEvent.ENTITY_APPLICATION,
            entity_id="foreign-record", action="REVIEWED",
        )

        with self.assertRaisesRegex(RuntimeError, "another school's records"):
            call_command("sandbox_seed_flagship", reset=True)

        # admissions cleanup runs before the flagship guard and deletes this
        # family. The outer transaction must restore it when the guard refuses.
        self.assertTrue(Family.objects.filter(pk=family.pk, school=school).exists())
        self.assertTrue(UserAccount.objects.filter(pk=actor.pk, school=school).exists())
        self.assertTrue(AidAuditEvent.objects.filter(pk=event.pk, school=foreign).exists())

    def test_command_rolls_back_cleanup_on_school_identity_refusal(self):
        spec = SANDBOX_SCHOOLS["heritage-core"]
        school = School.objects.create(id=spec.id, name="Customer School")
        family = Family.objects.create(school=school, family_name=FAMILY_NAME)

        with self.assertRaisesRegex(RuntimeError, "different institution"):
            call_command("sandbox_seed_flagship", reset=True)

        self.assertTrue(Family.objects.filter(pk=family.pk, school=school).exists())
        school.refresh_from_db()
        self.assertEqual(school.name, "Customer School")

    def test_command_rolls_back_cleanup_when_rebuild_fails(self):
        school = ensure_demo_school(SANDBOX_SCHOOLS["heritage-core"])
        family = Family.objects.create(school=school, family_name=FAMILY_NAME)
        target = "sandbox_demo.management.commands.sandbox_seed_flagship.seed_heritage_flagship"
        with patch(target, side_effect=RuntimeError("rebuild failed")):
            with self.assertRaisesRegex(RuntimeError, "rebuild failed"):
                call_command("sandbox_seed_flagship", reset=True)

        self.assertTrue(Family.objects.filter(pk=family.pk, school=school).exists())

    def test_clear_flagship_data_refuses_foreign_school_aid_award_deletion(self):
        heritage_school = School.objects.create(name="Heritage Test School")
        other_school = School.objects.create(name="Other Test School")
        academic_year = AcademicYear.objects.create(
            school=other_school,
            name="2026-2027",
            start_date=date(2026, 8, 15),
            end_date=date(2027, 6, 5),
            is_current=True,
        )
        family = Family.objects.create(school=other_school, family_name="Reed Family")
        student = Student.objects.create(
            school=other_school,
            family=family,
            student_number="HCA-TEST-0001",
            first_name="Avery",
            last_name="Reed",
            dob=date(2010, 1, 1),
            status="ACTIVE",
        )
        decider = UserAccount.objects.create_user(
            username="director@heritage.example.org",
            email="director@heritage.example.org",
            school=heritage_school,
            password="not-used-in-test",
        )
        award = AidAward.objects.create(
            school=other_school,
            academic_year=academic_year,
            student=student,
            award_type=AidAward.TYPE_NEED,
            awarded_cents=1000,
            decision_status=AidAward.DECISION_ACCEPTED,
            decided_by=decider,
        )

        with self.assertRaisesRegex(RuntimeError, "another school's records"):
            _clear_flagship_data(heritage_school)

        self.assertTrue(AidAward.objects.filter(pk=award.pk, school=other_school).exists())
        self.assertTrue(UserAccount.objects.filter(pk=decider.pk, school=heritage_school).exists())
